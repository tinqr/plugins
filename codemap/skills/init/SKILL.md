---
name: init
description: Generate codemap without installing git hooks — one-time snapshot only. Use when the user wants a quick codebase map without permanent hooks, or invokes /codemap:init.
disable-model-invocation: true
---

# /codemap:init — Generate Without Hooks

Generate the codemap for the current project without installing git hooks. Use this for a one-time snapshot without automatic updates.

## Steps

1. Determine the project root (current working directory)
2. Run the init command:

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/codemap_cli.py" init <project_root>
```

3. Confirm to the user what was generated:
   - Which framework was detected
   - What sections were created at `docs/codemap/`
   - Note: no git hooks installed — the codemap won't auto-update on commits. Use `/codemap:setup` for that.
