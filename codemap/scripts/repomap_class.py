"""
RepoMap — tree-sitter tag extraction and PageRank ranking.
Forked from github.com/AbanteAI/repo-map, stripped to essentials.
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Callable

import diskcache
from utils import Tag, read_text
from scm import get_scm_fname

CACHE_VERSION = 1
SQLITE_ERRORS = (sqlite3.OperationalError, sqlite3.DatabaseError)


def _pagerank(adjacency, alpha=0.85, max_iter=100, tol=1e-6):
    """Pure Python PageRank via power iteration.

    adjacency: {node: [target, ...]} — outgoing edges (duplicates OK for multi-edges)
    Returns: {node: rank}
    """
    nodes = list(adjacency)
    n = len(nodes)
    if n == 0:
        return {}

    rank = {node: 1.0 / n for node in nodes}

    in_neighbors = {node: [] for node in nodes}
    out_degree = {}
    for src in nodes:
        targets = adjacency[src]
        out_degree[src] = len(targets)
        for tgt in targets:
            if tgt in in_neighbors:
                in_neighbors[tgt].append(src)

    for _ in range(max_iter):
        dangling_sum = sum(rank[node] for node in nodes if out_degree[node] == 0)

        new_rank = {}
        for node in nodes:
            incoming = sum(
                rank[src] / out_degree[src]
                for src in in_neighbors[node]
            )
            new_rank[node] = (1 - alpha + alpha * dangling_sum) / n + alpha * incoming

        diff = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank
        if diff < tol:
            break

    return rank


class RepoMap:
    """Tag extraction and PageRank ranking for code files."""

    def __init__(
        self,
        root: str = None,
        file_reader_func: Callable[[str], Optional[str]] = read_text,
        verbose: bool = False,
    ):
        self.root = Path(root or os.getcwd()).resolve()
        self.read_text_func = file_reader_func
        self.verbose = verbose
        self._cache_dir = self.root / f".repomap.tags.cache.v{CACHE_VERSION}"
        self.load_tags_cache()

    def load_tags_cache(self):
        try:
            self.TAGS_CACHE = diskcache.Cache(str(self._cache_dir))
        except Exception:
            self.TAGS_CACHE = {}

    def tags_cache_error(self):
        try:
            if self._cache_dir.exists():
                shutil.rmtree(self._cache_dir)
            self.load_tags_cache()
        except Exception:
            self.TAGS_CACHE = {}

    def get_rel_fname(self, fname: str) -> str:
        try:
            return str(Path(fname).relative_to(self.root))
        except ValueError:
            return fname

    def get_mtime(self, fname: str) -> Optional[float]:
        try:
            return os.path.getmtime(fname)
        except FileNotFoundError:
            return None

    def get_tags(self, fname: str, rel_fname: str) -> List[Tag]:
        file_mtime = self.get_mtime(fname)
        if file_mtime is None:
            return []

        try:
            cached = self.TAGS_CACHE.get(fname)
            if cached and cached.get("mtime") == file_mtime:
                return cached["data"]
        except SQLITE_ERRORS:
            self.tags_cache_error()

        tags = self.get_tags_raw(fname, rel_fname)

        try:
            self.TAGS_CACHE[fname] = {"mtime": file_mtime, "data": tags}
        except SQLITE_ERRORS:
            self.tags_cache_error()

        return tags

    def get_tags_raw(self, fname: str, rel_fname: str) -> List[Tag]:
        try:
            from grep_ast import filename_to_lang
            from grep_ast.tsl import get_language, get_parser
        except ImportError:
            print("Error: grep-ast required. pip install grep-ast")
            sys.exit(1)

        lang = filename_to_lang(fname)
        if not lang:
            return []

        try:
            language = get_language(lang)
            parser = get_parser(lang)
        except Exception:
            return []

        scm_fname = get_scm_fname(lang)
        if not scm_fname:
            return []

        code = self.read_text_func(fname)
        if not code:
            return []

        try:
            tree = parser.parse(bytes(code, "utf-8"))
            query_text = read_text(scm_fname, silent=True)
            if not query_text:
                return []

            query = language.query(query_text)
            captures = query.captures(tree.root_node)

            tags = []
            for capture_name, nodes in captures.items():
                for node in nodes:
                    if "name.definition" in capture_name:
                        kind = "def"
                    elif "name.reference" in capture_name:
                        kind = "ref"
                    else:
                        continue

                    tags.append(Tag(
                        rel_fname=rel_fname,
                        fname=fname,
                        line=node.start_point[0] + 1,
                        name=node.text.decode("utf-8") if node.text else "",
                        kind=kind,
                    ))

            return tags
        except Exception:
            return []

    def get_ranked_tags(self, fnames: List[str]) -> Dict[str, float]:
        """Build dependency graph from files and return PageRank scores."""
        if not fnames:
            return {}

        defines = defaultdict(set)
        references = defaultdict(set)

        for fname in fnames:
            if not os.path.exists(fname):
                continue
            rel_fname = self.get_rel_fname(fname)
            tags = self.get_tags(fname, rel_fname)

            for tag in tags:
                if tag.kind == "def":
                    defines[tag.name].add(rel_fname)
                elif tag.kind == "ref":
                    references[tag.name].add(rel_fname)

        all_rel = set(self.get_rel_fname(f) for f in fnames if os.path.exists(f))
        adjacency = {rel: [] for rel in all_rel}

        for name, ref_fnames in references.items():
            def_fnames = defines.get(name, set())
            for ref_fname in ref_fnames:
                for def_fname in def_fnames:
                    if ref_fname != def_fname:
                        adjacency.setdefault(ref_fname, []).append(def_fname)

        if not adjacency:
            return {}

        return _pagerank(adjacency)
