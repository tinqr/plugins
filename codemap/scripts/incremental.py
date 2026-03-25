"""Incremental update logic — git diff to affected codemap sections."""

import re
import subprocess
from typing import List, Set


def _glob_to_regex(pattern: str) -> str:
    """Convert a glob pattern to regex with proper ** support.

    - **/ matches zero or more directory segments (including none)
    - ** at end matches everything remaining
    - * matches anything except /
    - ? matches a single non-/ character
    """
    i, n = 0, len(pattern)
    result = ""
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                if i + 2 < n and pattern[i + 2] == "/":
                    result += "(?:.+/)?"
                    i += 3
                else:
                    result += ".*"
                    i += 2
            else:
                result += "[^/]*"
                i += 1
        elif c == "?":
            result += "[^/]"
            i += 1
        else:
            result += re.escape(c)
            i += 1
    return "^" + result + "$"


def _glob_match(path: str, pattern: str) -> bool:
    """Match a file path against a glob pattern with ** support."""
    return bool(re.match(_glob_to_regex(pattern), path))


def get_changed_files(project_root: str) -> List[str]:
    """Get files changed in the last commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1..HEAD"],
        cwd=project_root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        # First commit or detached HEAD — try root diff
        result = subprocess.run(
            ["git", "diff-tree", "--root", "-r", "--name-only", "--no-commit-id", "HEAD"],
            cwd=project_root, capture_output=True, text=True,
        )
    return [f for f in result.stdout.strip().splitlines() if f]


def get_changed_files_with_status(project_root: str) -> List[str]:
    """Get files changed with status (A/D/M) in the last commit."""
    result = subprocess.run(
        ["git", "diff", "--name-status", "HEAD~1..HEAD"],
        cwd=project_root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff-tree", "--root", "-r", "--name-status", "--no-commit-id", "HEAD"],
            cwd=project_root, capture_output=True, text=True,
        )
    return [line for line in result.stdout.strip().splitlines() if line]


def has_new_or_deleted_files_in_list(status_lines: List[str]) -> bool:
    """Check if any status lines indicate added or deleted files."""
    for line in status_lines:
        if line and line[0] in ("A", "D"):
            return True
    return False


def _matches_section(path: str, section_config: dict) -> bool:
    """Check if a file path matches a section's pattern(s) and exclusions."""
    pattern = section_config["pattern"]
    patterns = pattern if isinstance(pattern, list) else [pattern]

    if not any(_glob_match(path, p) for p in patterns):
        return False

    exclude = section_config.get("exclude", [])
    if exclude and any(_glob_match(path, ex) for ex in exclude):
        return False

    return True


def map_files_to_sections(
    changed_files: List[str],
    sections: dict,
    files_added_or_deleted: bool = False,
) -> Set[str]:
    """Map changed file paths to affected codemap section names."""
    affected = set()

    for changed_file in changed_files:
        for section_name, section_config in sections.items():
            if _matches_section(changed_file, section_config):
                affected.add(section_name)

    if files_added_or_deleted:
        affected.add("structure")

    code_sections = {"routes", "api", "layouts", "components", "actions", "exports",
                     "screens", "models", "widgets", "providers", "services",
                     "schema", "definitions"}
    if affected & code_sections:
        affected.add("graph")

    return affected
