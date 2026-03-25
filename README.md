# codemap

Your AI coding agent shouldn't spend 30 seconds grepping around before it can help you.

Codemap generates a structured map of your codebase: routes, components, schema, exports, ranked by importance. It plugs into Claude Code as a skill, auto-triggers when your agent needs orientation, and stays fresh after every commit. No config files, no MCP servers, no LLM calls. Just markdown files your agent reads instantly.

## The problem

Every time you start a task, your agent burns tokens figuring out what exists:

```
Let me explore the codebase...
[grep for "page.tsx" files]
[glob src/components/**]
[read 6 files to understand structure]
[grep for imports to find connections]
OK, I think I understand the project now.
```

That's 30+ seconds and thousands of tokens before any real work starts. And it happens every session.

## With codemap

Your agent already has the map. It reads the relevant section and goes straight to work:

```markdown
## Routes

### `/checkout`
`src/app/[tenant]/[locale]/checkout/page.tsx`
- `CheckoutPage` (line 6)

### `/order/[id]`
`src/app/[tenant]/[locale]/order/[id]/page.tsx`
- `formatPrice` (line 51)

## Components

### src/app/[tenant]/[locale]/checkout/checkout-form.tsx
- `CustomerSession` (line 18)
- `handleSubmit` (line 211)
```

Ask about routes, it reads `routes.md`. Ask about the data model, it reads `schema.md`. It never loads everything at once. Only the section that answers your question.

## Install

```sh
claude plugin marketplace add https://github.com/tinqr/codemap
claude plugin install codemap
```

Then in any project:

```
/codemap:setup
```

That's it. Dependencies install on first run (Python 3.9+ required). Git hooks and `.gitignore` are configured for you. Restart Claude Code after installing.

## What it generates

All output lives in `docs/codemap/` (gitignored by default). Each section is a small markdown file your agent can read in one shot.

**Routes** map `page.tsx` files to URL paths with their exports:

```markdown
### `/[tenant]/[locale]/addresses`
`src/app/[tenant]/[locale]/addresses/page.tsx`
- `AddressesPage` (line 6)
```

**Schema** renders Prisma models as readable tables:

```markdown
**Tenant**

| Field | Type |
|-------|------|
| id | String |
| name | String |
| slug | String |
| categories | Category[] |
| orders | Order[] |
```

**Components** lists every component with its definitions, including co-located files inside `app/` that aren't routes or layouts:

```markdown
### src/app/[tenant]/[locale]/checkout/checkout-form.tsx
- `CustomerSession` (line 18)
- `SavedAddress` (line 24)
- `handleSubmit` (line 211)
```

**Graph** surfaces your most important files using PageRank. A utility imported everywhere ranks higher than a one-off helper:

```markdown
1. `apps/merchant/src/app/(dashboard)/menu/menu-manager.tsx` (rank: 0.1831)
2. `packages/types/src/index.ts` (rank: 0.0282)
3. `apps/storefront/src/components/menu-content.tsx` (rank: 0.0080)
```

Also generates: **api** (route handlers), **layouts**, **actions** (server actions), **exports** (shared libraries).

## How it stays smart

**Auto-triggers.** You never invoke codemap manually. When Claude needs to understand your project ("where are the routes?", "what does the schema look like?", "how is this organized?"), it reads the right section automatically.

**Progressive disclosure.** Each question loads one section, not the whole map. Your context window stays clean for actual work.

**Incremental updates.** A post-commit hook runs after every `git commit`. It diffs the changed files, figures out which sections are affected, and regenerates only those. Touch a component? `components.md` and `graph.md` update. Everything else stays cached. Large commits (50+ files) trigger a full rebuild. Branch switches mark the map as stale.

**No server, no process.** Codemap is just files. No MCP server running in the background, no sidecar process, no port to manage. Markdown files in `docs/codemap/` that any tool can read.

## Supported frameworks

| Framework | Detection | Sections |
|-----------|-----------|----------|
| Next.js | `next.config.*` | routes, api, layouts, schema, components, actions, exports |
| Flutter | `pubspec.yaml` | screens, models, widgets, providers, services |
| Prisma | `prisma/schema.prisma` | schema (rendered as tables) |
| Generic | everything else | definitions (auto-detected) |

Frameworks compose. A Next.js project with Prisma gets both sets of sections.

**Generic works on any language.** Python, Go, Rust, Ruby, C++, Swift, Kotlin, and 100+ more via tree-sitter. If tree-sitter can parse it, codemap maps it. No config needed: it detects the language and extracts definitions automatically.

**Next.js patterns handle real projects.** Co-located components in `app/`, `.jsx` and `.tsx`, projects with or without `src/`, route groups like `(marketing)` stripped from URL paths, `src/utils/` and `lib/` for shared code. Reserved filenames (`page`, `layout`, `route`, `loading`, `error`, `not-found`, `template`) are classified into their correct sections, not dumped into components.

## Monorepo support

Detected automatically via `pnpm-workspace.yaml`, `turbo.json`, or `lerna.json`. Each app and package gets its own sections:

```
docs/codemap/
├── apps/
│   ├── admin/routes.md
│   ├── merchant/components.md
│   └── storefront/routes.md
├── packages/
│   ├── db/schema.md
│   └── ui/exports.md
└── graph.md
```

## Customization

Create `.codemap.json` in your project root to add or override sections:

```json
{
  "sections": {
    "screens": {"pattern": "lib/**/pages/**/*.dart", "label": "Pages"},
    "blocs": {"pattern": ["lib/**/bloc/**/*.dart", "lib/**/cubit/**/*.dart"], "label": "BLoCs"}
  },
  "monorepo": {
    "apps_dir": "services",
    "packages_dir": "packages/internal"
  }
}
```

Patterns can be a single glob string or an array. Sections also support an `exclude` list for filtering out matched files.

## Commands

```
/codemap:query     # ask about structure (auto-triggers, rarely needed manually)
/codemap:setup     # first-time setup: hooks + deps + full generation
/codemap:init      # generate without hooks
/codemap:refresh   # manual full regeneration
```

## Explorer agent

The plugin ships a `codemap:explorer` subagent that Claude can dispatch for codebase exploration. It checks for codemap before doing any raw grep/glob, then traces actual source files for details.

This replaces the typical pattern where an exploration subagent burns 20+ tool calls rediscovering structure that codemap already has. If the project has a codemap, the explorer reads the relevant section (one tool call), then goes straight to the source files that matter.

The explorer also handles projects without codemap. It falls back to standard grep/glob exploration, so it works everywhere.

## How it compares to RepoMapper

Codemap started as a fork of [RepoMapper](https://github.com/AbanteAI/repo-map), which ports [Aider's](https://github.com/Aider-AI/aider) repo-map algorithm. RepoMapper generates a flat list of every definition in your project. That's useful, but it dumps everything into one file with no structure, no framework awareness, and no way to stay current.

What codemap adds:

- **Framework-aware sections** instead of a flat list. Routes are routes, components are components, schema is rendered as tables.
- **Incremental updates** via post-commit hooks. RepoMapper requires manual re-runs.
- **Progressive disclosure** through a Claude Code skill. Only the relevant section loads into context, not the entire map.
- **Pure Python PageRank.** Dropped networkx and scipy. Three dependencies total (tree-sitter, grep-ast, diskcache) vs a heavier stack.
- **Monorepo support.** Per-app and per-package sections with automatic detection.
- **Multi-pattern matching with excludes.** Sections can use multiple glob patterns and filter results. Handles real-world project layouts where files don't follow textbook conventions.
- **Self-bootstrapping.** No pip install, no venv activation, no requirements.txt. First run sets everything up.
- **Stripped down.** The core RepoMap class went from 615 lines to 150. Everything that isn't parsing or ranking was removed.

## License

MIT
