---
name: query
description: Query codebase structure, architecture, routes, schema, components, dependencies, or imports. Use this skill BEFORE dispatching any code-explorer or exploration subagent. Reading one codemap section takes 1 tool call vs 20+ grep/glob calls for raw exploration. Use this whenever starting work on any code project, exploring unfamiliar code, asking "what does this project look like", "where is X defined", "how is the code organized", or needing to understand what exists before making changes. Even if the user doesn't mention "codemap" explicitly, use this whenever they need codebase orientation or structural understanding. If you're about to dispatch an Agent for exploration, check codemap first.
---

# /codemap:query — Progressive Codebase Context

Codemap provides auto-generated codebase context files at `docs/codemap/` in each project. These files are maintained by post-commit git hooks and give you instant structural understanding without grepping the entire codebase.

## Resolve the Target Project

The codemap lives in the **target project**, not necessarily the current working directory. If the user is asking about a specific project (e.g., "show me Lune's routes" while working from a different directory), resolve that project's path first and look for `docs/codemap/` there.

**Resolution order:**
1. If the user names a project or you know which project is being discussed, use that project's root path
2. If the conversation references files in a specific directory (e.g., `~/projects/lune/`), use that directory
3. Fall back to the current working directory

This matters because agents often operate from a central workspace (like a vault or home directory) while working on code in another project. Always check the actual project's codemap, not the workspace's.

## Setup Check

**After resolving the target project:** Check if `<project_root>/docs/codemap/meta.json` exists.

- **If missing:** Tell the user: "No codemap found for this project. Run `/codemap:setup` in the project directory to generate one."
- **If exists:** Proceed to staleness check, then query.

## Staleness Check

Read `<project_root>/docs/codemap/meta.json`. If `"stale": true`, warn:

> "Codemap may be outdated (branch switch detected). Run `/codemap:refresh` to update."

Then proceed with the query using existing files — stale data is better than no data.

## Progressive Disclosure Protocol

Route the query to the smallest file that answers it. **Never load all codemap files at once.** All paths below are relative to `<project_root>/docs/codemap/`.

| User is asking about | Read this file |
|---|---|
| "What exists?" / project structure / overview | `structure.md` (~200 tokens) |
| Routes, pages, navigation | `routes.md` |
| Schema, models, database, types | `schema.md` |
| Components, widgets, UI pieces | `components.md` |
| Server actions, API handlers | `actions.md` |
| Shared libraries, exports, utilities | `exports.md` |
| Dependencies, "how does X connect to Y?" | `graph.md`, then follow links to source files |

**Monorepo projects:** Section files are in subdirectories: `apps/<name>/routes.md`, `packages/<name>/schema.md`, etc. Check `meta.json` for the full list of available sections.

**When a codemap section is not enough:** Read the actual source files that the codemap points to. Codemap is for wayfinding, not full understanding.

## Commands

| Command | What it does |
|---------|-------------|
| `/codemap:query` | Query the codemap (progressive disclosure) |
| `/codemap:setup` | Install git hooks + generate codemap |
| `/codemap:init` | Generate without hooks |
| `/codemap:refresh` | Manual full regeneration |

## Rules

- **Never** load all codemap files at once — pick the right section for the query.
- **Always** resolve the target project path before checking for a codemap — don't assume the current working directory is the project.
- **Never** fall back to a code-explorer subagent or grepping when a codemap exists for the target project — check the codemap first.
- **Never** guess at codebase structure — read the codemap.
- **When codemap is not enough**, read actual source files. Codemap tells you where to look; source files tell you how things work.
