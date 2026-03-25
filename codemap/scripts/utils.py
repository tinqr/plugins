"""Utility functions for RepoMap."""

from pathlib import Path
from typing import Optional
from collections import namedtuple

Tag = namedtuple("Tag", "rel_fname fname line name kind")


def read_text(filename: str, encoding: str = "utf-8", silent: bool = False) -> Optional[str]:
    try:
        return Path(filename).read_text(encoding=encoding, errors="ignore")
    except (FileNotFoundError, IsADirectoryError, OSError, UnicodeError):
        if not silent:
            print(f"Error reading {filename}")
        return None
