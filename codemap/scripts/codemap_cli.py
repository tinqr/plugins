#!/usr/bin/env python3
"""Codemap CLI — bootstraps venv then delegates to core."""

import os
import subprocess
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = PLUGIN_DIR / ".venv"
VENV_PYTHON = str(VENV_DIR / "bin" / "python3")
REQUIREMENTS = str(PLUGIN_DIR / "requirements.txt")


def _ensure_venv():
    """Create venv and install deps if needed. Re-exec in venv."""
    # Already in a venv — skip bootstrap
    if sys.prefix != sys.base_prefix:
        return

    if not os.path.exists(VENV_PYTHON):
        print("[codemap] First-time setup — creating virtual environment...")

        if sys.version_info < (3, 9):
            print("[codemap] Error: Python 3.9+ required.")
            sys.exit(1)

        try:
            import venv
            venv.create(str(VENV_DIR), with_pip=True)
        except Exception as e:
            print(f"[codemap] Error creating venv: {e}")
            print("[codemap] Ensure Python 3.9+ with ensurepip is installed.")
            sys.exit(1)

        pip = str(VENV_DIR / "bin" / "pip")
        print("[codemap] Installing dependencies (diskcache, grep-ast, tree-sitter)...")
        r = subprocess.run(
            [pip, "install", "-q", "-r", REQUIREMENTS],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"[codemap] Error installing dependencies:\n{r.stderr}")
            sys.exit(1)
        print("[codemap] Ready.")

    # Re-exec in venv
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)


if __name__ == "__main__":
    _ensure_venv()

    # Now in venv — add scripts dir to path and delegate
    sys.path.insert(0, str(Path(__file__).parent))
    from codemap_core import cli_main
    cli_main()
