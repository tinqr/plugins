"""
Section-based file discovery and markdown generation for codemap.

Discovers files per framework section pattern and generates markdown
for each section, using RepoMap's get_tags() for code definitions.
"""

import os
import re
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import List

from repomap_class import RepoMap
from utils import read_text

IGNORED_DIRS = {".git", "node_modules", "__pycache__", "venv", "env", "docs/codemap"}
IGNORED_FILES = {".repomap.tags.cache.v1"}


def _is_ignored(path_parts: tuple) -> bool:
    for part in path_parts:
        if part in (".git", "node_modules", "__pycache__", "venv", "env"):
            return True
    return False


def _discover_parseable_files(project_root: str) -> List[str]:
    """Find all files that tree-sitter can parse."""
    from grep_ast import filename_to_lang

    root = Path(project_root)

    # Prefer git ls-files
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=project_root, capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            all_files = result.stdout.strip().splitlines()
        else:
            all_files = [
                str(p.relative_to(root))
                for p in root.rglob("*") if p.is_file()
            ]
    except Exception:
        all_files = [
            str(p.relative_to(root))
            for p in root.rglob("*") if p.is_file()
        ]

    parseable = []
    for f in sorted(all_files):
        if _is_ignored(Path(f).parts):
            continue
        if "docs/codemap" in f:
            continue
        abs_path = str(root / f)
        lang = filename_to_lang(abs_path)
        if lang:
            parseable.append(f)

    return parseable


def discover_section_files(project_root: str, pattern, exclude=None) -> List[str]:
    """Glob for files matching pattern(s), return sorted relative paths.

    pattern: a glob string, a list of glob strings, or "__auto__"
    exclude: optional list of glob patterns to exclude from results
    """
    if pattern == "__auto__":
        return _discover_parseable_files(project_root)

    root = Path(project_root)
    patterns = pattern if isinstance(pattern, list) else [pattern]
    seen = set()
    matches = []

    for pat in patterns:
        for path in root.glob(pat):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            parts = rel.parts
            if _is_ignored(parts):
                continue
            rel_str = str(rel)
            if "docs/codemap" in rel_str:
                continue
            if rel.name in IGNORED_FILES:
                continue
            if rel_str in seen:
                continue
            seen.add(rel_str)
            matches.append(rel_str)

    if exclude:
        from fnmatch import fnmatch
        matches = [
            m for m in matches
            if not any(fnmatch(m, ex) for ex in exclude)
        ]

    return sorted(matches)


def generate_structure_markdown(project_root: str) -> str:
    """Generate tree-like file listing from git-tracked files."""
    # Try git ls-files first (respects .gitignore)
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=project_root, capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            file_list = sorted(result.stdout.strip().splitlines())
            return _build_tree_from_paths(file_list)
    except Exception:
        pass

    # Fallback to filesystem walk (non-git repos)
    return _build_tree_from_walk(Path(project_root))


def _build_tree_from_paths(paths: List[str]) -> str:
    """Build a visual tree from a sorted list of relative file paths."""
    tree = OrderedDict()
    for path in paths:
        parts = path.split("/")
        node = tree
        for part in parts:
            node = node.setdefault(part, OrderedDict())

    lines = []

    def _render(node, prefix=""):
        entries = list(node.items())
        for i, (name, children) in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            if children:
                lines.append(f"{prefix}{connector}{name}/")
                extension = "    " if is_last else "│   "
                _render(children, prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{name}")

    _render(tree)
    return "\n".join(lines)


def _build_tree_from_walk(root: Path) -> str:
    """Fallback: filesystem walk with hardcoded ignores."""
    lines = []

    def _walk(directory: Path, prefix: str = ""):
        entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        entries = [
            e for e in entries
            if not e.name.startswith(".")
            and e.name not in ("node_modules", "__pycache__", "venv", "env",
                               "build", ".dart_tool", "ios", "android")
            and e.name not in IGNORED_FILES
        ]
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            if entry.is_dir():
                rel_str = str(entry.relative_to(root))
                if "docs/codemap" in rel_str:
                    continue
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    _walk(root)
    return "\n".join(lines)


def _derive_route_path(file_path: str) -> str:
    """Derive URL path from a file path. Strips route groups like (marketing)."""
    parts = Path(file_path).parts
    try:
        app_idx = list(parts).index("app")
    except ValueError:
        return "/" + "/".join(parts[:-1])

    segments = []
    for seg in parts[app_idx + 1:-1]:
        # Route groups don't create URL segments
        if seg.startswith("(") and seg.endswith(")"):
            continue
        segments.append(seg)

    if not segments:
        return "/"
    return "/" + "/".join(segments)


def _parse_prisma_schema(content: str) -> str:
    """Parse Prisma schema content into markdown tables."""
    models = re.findall(r"model\s+(\w+)\s*\{([^}]+)\}", content, re.DOTALL)
    if not models:
        return ""

    lines = []
    for model_name, body in models:
        lines.append(f"**{model_name}**")
        lines.append("")
        lines.append("| Field | Type |")
        lines.append("|-------|------|")
        for line in body.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("@@"):
                continue
            tokens = line.split()
            if len(tokens) >= 2:
                field_name = tokens[0]
                field_type = tokens[1]
                lines.append(f"| {field_name} | {field_type} |")
        lines.append("")

    return "\n".join(lines)


def _get_unique_defs(repo_map: RepoMap, abs_path: str, rel_path: str) -> List[tuple]:
    """Extract definitions from a file, deduplicated by (name, line)."""
    tags = repo_map.get_tags(abs_path, rel_path)
    seen = set()
    result = []
    for t in tags:
        if t.kind != "def":
            continue
        key = (t.name, t.line)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def generate_section_markdown(
    repo_map: RepoMap,
    project_root: str,
    label: str,
    files: List[str],
    route_paths: bool = False,
    schema_mode: bool = False,
) -> str:
    """Generate markdown for a section of files."""
    if not files:
        return f"## {label}\n\nNo files found.\n"

    root = Path(project_root)
    lines = [f"## {label}", ""]

    if schema_mode:
        for f in files:
            abs_path = root / f
            content = read_text(str(abs_path))
            if content:
                lines.append(f"### {f}")
                lines.append("")
                lines.append(_parse_prisma_schema(content))
        return "\n".join(lines)

    if route_paths:
        for f in files:
            route = _derive_route_path(f)
            lines.append(f"### `{route}`")
            lines.append(f"`{f}`")
            lines.append("")
            abs_path = str(root / f)
            defs = _get_unique_defs(repo_map, abs_path, f)
            if defs:
                for name, line in defs:
                    lines.append(f"- `{name}` (line {line})")
                lines.append("")
    else:
        for f in files:
            abs_path = str(root / f)
            defs = _get_unique_defs(repo_map, abs_path, f)
            if defs:
                lines.append(f"### {f}")
                lines.append("")
                for name, line in defs:
                    lines.append(f"- `{name}` (line {line})")
                lines.append("")

    return "\n".join(lines)


def generate_graph_markdown(repo_map: RepoMap, project_root: str, all_files: List[str]) -> str:
    """Use RepoMap's PageRank to rank files by importance."""
    if not all_files:
        return "## Dependency Graph\n\nNo files to analyze.\n"

    root = Path(project_root)
    abs_files = [str(root / f) for f in all_files]
    ranks = repo_map.get_ranked_tags(abs_files)

    sorted_files = sorted(ranks.items(), key=lambda x: x[1], reverse=True)[:10]

    lines = ["## Dependency Graph (Top 10 Hub Files)", ""]
    for i, (fname, rank) in enumerate(sorted_files, 1):
        lines.append(f"{i}. `{fname}` (rank: {rank:.4f})")
    lines.append("")

    return "\n".join(lines)
