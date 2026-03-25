---
name: refresh
description: Regenerate the entire codemap from scratch — use after branch switches, when codemap is stale, or when sections seem outdated. Triggers on /codemap:refresh.
disable-model-invocation: true
---

# /codemap:refresh — Full Regeneration

Regenerate the entire codemap from scratch. Use this when:
- The codemap is marked stale (after branch switch)
- Sections seem outdated or incomplete
- You want a clean regeneration

## Steps

1. Determine the project root (current working directory)
2. Run the refresh command:

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/codemap_cli.py" refresh <project_root>
```

3. Confirm to the user what was regenerated and which sections were updated.
