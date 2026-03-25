import pytest
import json
import tempfile
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from meta import read_meta, write_meta, compute_hash, is_section_stale, get_codemap_dir

def test_get_codemap_dir():
    assert get_codemap_dir("/foo/bar").endswith("docs/codemap")

def test_read_meta_missing():
    with tempfile.TemporaryDirectory() as tmp:
        assert read_meta(tmp) is None

def test_write_and_read_meta():
    with tempfile.TemporaryDirectory() as tmp:
        meta = {"framework": "nextjs", "sections": {}}
        write_meta(tmp, meta)
        loaded = read_meta(tmp)
        assert loaded["framework"] == "nextjs"

def test_compute_hash_deterministic():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.txt")
        Path(f).write_text("hello")
        h1 = compute_hash(tmp, ["a.txt"])
        h2 = compute_hash(tmp, ["a.txt"])
        assert h1 == h2
        assert len(h1) == 12

def test_compute_hash_changes_on_content():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.txt")
        Path(f).write_text("hello")
        h1 = compute_hash(tmp, ["a.txt"])
        Path(f).write_text("world")
        h2 = compute_hash(tmp, ["a.txt"])
        assert h1 != h2

def test_is_section_stale_missing_section():
    meta = {"sections": {}}
    assert is_section_stale(meta, "routes", "abc123") is True

def test_is_section_stale_hash_mismatch():
    meta = {"sections": {"routes": {"hash": "abc123"}}}
    assert is_section_stale(meta, "routes", "def456") is True

def test_is_section_stale_hash_match():
    meta = {"sections": {"routes": {"hash": "abc123"}}}
    assert is_section_stale(meta, "routes", "abc123") is False
