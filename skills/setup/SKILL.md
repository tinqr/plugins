---
name: setup
description: First-time codemap setup for a project — install git hooks, bootstrap dependencies, and generate the full codebase map. Use when setting up codemap in a new project, when the user says "set up codemap", "install codemap", or invokes /codemap:setup.
disable-model-invocation: true
---

# /codemap:setup — First-Time Project Setup

Run the codemap setup command for the current project. This installs git hooks (post-commit + post-checkout), creates `.gitignore` entries for `docs/codemap/`, and generates the full codemap.

## Steps

1. Determine the project root (current working directory)
2. Run the setup command:

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/codemap_cli.py" setup <project_root>
```

3. On first run, this will automatically:
   - Create a virtual environment at the plugin's `.venv/` directory
   - Install dependencies (diskcache, grep-ast, tree-sitter)
   - Re-exec in the venv and run setup

4. Confirm to the user what was set up:
   - Git hooks installed (post-commit for incremental updates, post-checkout for stale marking)
   - `.gitignore` updated
   - Codemap generated at `docs/codemap/`
   - Which framework was detected and what sections were generated

5. If the project already has a codemap, setup will update the hooks and regenerate.
