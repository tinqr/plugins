"""meta.json management — tracks codemap freshness per section."""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_codemap_dir(project_root: str) -> str:
    return os.path.join(project_root, "docs", "codemap")


def read_meta(project_root: str) -> Optional[dict]:
    meta_path = os.path.join(get_codemap_dir(project_root), "meta.json")
    if not os.path.exists(meta_path):
        return None
    with open(meta_path) as f:
        return json.load(f)


def write_meta(project_root: str, meta: dict) -> None:
    codemap_dir = get_codemap_dir(project_root)
    os.makedirs(codemap_dir, exist_ok=True)
    meta_path = os.path.join(codemap_dir, "meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def compute_hash(project_root: str, rel_files: list) -> str:
    """SHA-256 of sorted file contents, truncated to 12 chars."""
    h = hashlib.sha256()
    for rel_path in sorted(rel_files):
        abs_path = os.path.join(project_root, rel_path)
        if os.path.exists(abs_path):
            h.update(Path(abs_path).read_bytes())
    return h.hexdigest()[:12]


def is_section_stale(meta: dict, section_key: str, current_hash: str) -> bool:
    sections = meta.get("sections", {})
    if section_key not in sections:
        return True
    return sections[section_key].get("hash") != current_hash


def get_git_remote(project_root: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=project_root, capture_output=True, text=True
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def get_current_branch(project_root: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_root, capture_output=True, text=True
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
