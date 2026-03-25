import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from repomap_class import RepoMap

FIXTURES = Path(__file__).parent / "fixtures"

def test_get_tags_returns_list():
    root = str(FIXTURES / "nextjs")
    repo_map = RepoMap(root=root)
    files = list((FIXTURES / "nextjs" / "src" / "app").rglob("*.tsx"))
    if files:
        f = str(files[0])
        rel = str(files[0].relative_to(FIXTURES / "nextjs"))
        tags = repo_map.get_tags(f, rel)
        assert isinstance(tags, list)

def test_get_ranked_tags_returns_dict():
    root = str(FIXTURES / "nextjs")
    repo_map = RepoMap(root=root)
    files = [str(f) for f in (FIXTURES / "nextjs" / "src").rglob("*.tsx")]
    ranks = repo_map.get_ranked_tags(files)
    assert isinstance(ranks, dict)

def test_get_ranked_tags_empty():
    repo_map = RepoMap(root=str(FIXTURES / "nextjs"))
    ranks = repo_map.get_ranked_tags([])
    assert ranks == {}

def test_get_ranked_tags_nonexistent_files():
    repo_map = RepoMap(root=str(FIXTURES / "nextjs"))
    ranks = repo_map.get_ranked_tags(["/nonexistent/file.tsx"])
    assert ranks == {}

def test_pagerank_simple_graph():
    """Two files: A references B. B should rank higher."""
    from repomap_class import _pagerank
    adjacency = {
        "a.py": ["b.py"],
        "b.py": [],
    }
    ranks = _pagerank(adjacency)
    assert ranks["b.py"] > ranks["a.py"]

def test_pagerank_empty():
    from repomap_class import _pagerank
    assert _pagerank({}) == {}

def test_pagerank_single_node():
    from repomap_class import _pagerank
    ranks = _pagerank({"a.py": []})
    assert len(ranks) == 1
    assert abs(ranks["a.py"] - 1.0) < 0.01

def test_pagerank_cycle():
    """A->B->C->A should give roughly equal ranks."""
    from repomap_class import _pagerank
    adjacency = {
        "a.py": ["b.py"],
        "b.py": ["c.py"],
        "c.py": ["a.py"],
    }
    ranks = _pagerank(adjacency)
    values = list(ranks.values())
    assert max(values) - min(values) < 0.01

def test_pagerank_star():
    """A,B,C all reference D. D should rank highest."""
    from repomap_class import _pagerank
    adjacency = {
        "a.py": ["d.py"],
        "b.py": ["d.py"],
        "c.py": ["d.py"],
        "d.py": [],
    }
    ranks = _pagerank(adjacency)
    assert ranks["d.py"] == max(ranks.values())

def test_pagerank_multi_edges():
    """Multiple edges (different symbols) from A to B."""
    from repomap_class import _pagerank
    adjacency = {
        "a.py": ["b.py", "b.py", "b.py"],
        "b.py": [],
    }
    ranks = _pagerank(adjacency)
    assert ranks["b.py"] > ranks["a.py"]

def test_pagerank_disconnected():
    """Two disconnected components still get valid ranks."""
    from repomap_class import _pagerank
    adjacency = {
        "a.py": ["b.py"],
        "b.py": [],
        "c.py": ["d.py"],
        "d.py": [],
    }
    ranks = _pagerank(adjacency)
    assert len(ranks) == 4
    assert all(r > 0 for r in ranks.values())
