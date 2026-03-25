---
name: marrow:setup
description: One-time vault setup. Runs a short conversation, then generates a complete knowledge vault with personalized CLAUDE.md, self-space, area maps, and ops infrastructure.
---

# /marrow:setup

This skill runs ONCE to create a new vault for a user. It has six parts: dependency check, conversation, vault location, file generation, git init, and success message.

Do NOT skip or reorder parts. Follow each section exactly.

---

## Part 1: Check Dependencies

Before starting the conversation, verify required tools are installed.

Run these checks:

```bash
command -v git >/dev/null 2>&1
command -v tree >/dev/null 2>&1
```

- If `git` is missing: "git is required for automatic saves. Want me to install it via Homebrew? (brew install git)"
- If `tree` is missing: "tree is required for the orient hook. Want me to install it via Homebrew? (brew install tree)"

Wait for permission before installing anything. If the user declines, explain the feature won't work without it but proceed anyway.

If both are installed, move to Part 2 silently.

---

## Part 2: Conversation (2-4 turns)

### Turn 1 -- open-ended

Say exactly this:

> Tell me about yourself -- what do you work on, what do you want to track and remember, and how do you like your tools to talk to you?

From their response, extract these five things:

1. **Identity** -- their name, role, what they do
2. **Domains** -- broad areas of work/life (these become area map files at `notes/<area>.md`)
3. **Personality** -- how the agent should communicate (casual/formal, warm/clinical, opinionated/neutral, verbose/terse)
4. **Extraction categories** -- what kinds of insights matter to them (e.g. "design decisions", "technical trade-offs", "things I learned", "open questions")
5. **First project** -- something they are actively working on

### Turns 2-3 -- optional follow-ups

Only ask if something from Turn 1 was genuinely unclear. One question per turn, skip if not needed.

Ask a follow-up ONLY if:
- Domains are ambiguous (can't tell what areas to create)
- Personality was not signaled at all
- Extraction categories are completely missing (no hint of what insights matter)
- No active project was mentioned

If all five extraction targets are clear, skip straight to the confirmation turn.

### Final turn -- present and confirm

Show what will be generated. Format it like this:

> Here's what I'll set up for you:
>
> **Vault location:** ~/vault/ (or wherever they chose)
> **Agent personality:** [2-sentence summary of how the agent will communicate]
> **Domains:** [list of area names]
> **Extraction categories:** [bulleted list of what the processing pipeline will look for]
> **First project:** [project name] -- [brief description]
>
> Want me to adjust anything, or should I generate?

On approval, proceed to Part 3.

---

## Part 3: Choose Vault Location

Ask:

> Where should I create your vault? Default is `~/vault/` -- press enter to accept or type a different path.

- If they accept or press enter: use `~/vault/`
- If they provide a path: use that path (expand ~ if needed)
- If the directory already exists and contains a `.marrow` file: "This directory already has a Marrow vault. Choose a different location or delete the existing one first."
- If the directory already exists but has no `.marrow` file: warn that files may be overwritten, ask to confirm

---

## Part 4: Generate Vault

Create ALL of the following files in the vault directory. Use the Write tool for each file.

### File 1: `.marrow` (guard file)

```
# Marrow vault marker + config
# Do not delete -- hooks only run when this file exists.

git: true
session_capture: true
```

### File 2: `.gitignore`

```
.marrow-commit-lock
```

### File 3: `marrow.yaml` (maintenance thresholds)

```yaml
maintenance:
  inbox_warning: 5
  observations_warning: 10
  stale_feature_days: 14
  stale_index_days: 30
  session_log_max: 8
  auto_commit_debounce_seconds: 300
```

### File 4: `self/identity.md` (PERSONALIZED)

Write this in the agent's voice. Use the identity, personality, and work style extracted from the conversation.

```markdown
---
description: Who I am and how I approach work with [NAME]
type: index
---

# identity

I am the agent for [NAME]'s knowledge vault. [NAME] is a [ROLE] who [WHAT_THEY_DO]. [PERSONALITY_DESCRIPTION -- how I communicate with them, derived from conversation].

## What I know about how they work

- [2-3 bullets derived from conversation]

## My approach

- Orient before acting -- never start work without reading the session state
- Park explicitly -- never leave a feature without writing its stopping point
- Capture immediately -- if something surfaces during work that belongs elsewhere, drop it in inbox/
```

### File 5: `self/methodology.md` (fixed template)

```markdown
---
description: How I process, connect, and maintain knowledge
type: index
---

# methodology

## Principles

- **Prose-as-title**: every note is a proposition -- a sentence that asserts something
- **Wiki links**: connections are edges in a graph, not folders in a hierarchy
- **Indexes**: navigation lives in index files, not folder structures
- **Inbox first**: nothing goes directly to notes/ -- everything routes through inbox/ first
- **Session rhythm**: orient, work, persist -- every session, no exceptions

## Session Rhythm

**Orient**: Read self/, check current session state, surface tasks and reminders, summarize back.

**Work**: One task at a time. Update notes as decisions are made. Drop discoveries in inbox/.

**Persist**: Update feature notes and goals, write session state, confirm state saved.
```

### File 6: `self/goals.md` (PERSONALIZED)

Seed from the conversation. The first project goes under Active Threads.

```markdown
---
description: Active threads -- what matters right now
type: index
---

# goals

## Active Threads

- **[FIRST_PROJECT_NAME]** -- [brief description from conversation]

## On Hold

(nothing yet)

## Completed

(nothing yet)
```

### File 7: `templates/note.md`

Replace `[AREAS]` with the user's domains joined by ` | ` (e.g. `design | engineering | learning`).

```markdown
---
description: [One sentence adding context the title doesn't]
type: note
area: [AREAS]
created: YYYY-MM-DD
topics: []
---

# [title as a proposition -- a sentence, not a label]

[content]

---

Topics:
- [[index-name]]
```

### File 8: `templates/index.md`

```markdown
---
description: Navigation index for [area/project/feature]
type: index
---

# [index name]

[content organized by topic]

---

Topics:
- [[parent-index]]
```

### File 9: `ops/tasks.md`

```markdown
# Tasks

## Active

(no tasks yet -- add your first with /tasks)

## Completed
```

### File 10: `ops/reminders.md`

```markdown
# Reminders

(no reminders yet)
```

### File 11: `ops/methodology/methodology.md`

```markdown
---
description: Index of earned lessons
type: index
---

# methodology

Lessons learned during sessions. Each note captures one behavioral rule.

(no lessons yet -- save your first with /remember)
```

### File 12: Empty directories

Create these directories (use `mkdir -p`):

- `ops/observations/`
- `ops/sessions/`
- `ops/queue/`
- `inbox/`
- `archive/`

Add a `.gitkeep` in each so git tracks them:

```bash
mkdir -p ops/observations ops/sessions ops/queue inbox archive
touch ops/observations/.gitkeep ops/sessions/.gitkeep ops/queue/.gitkeep inbox/.gitkeep archive/.gitkeep
```

### File 13: Area maps (PERSONALIZED) -- one per domain

For each domain extracted from the conversation, create `notes/[AREA].md`:

```markdown
---
description: Navigation index for [AREA_NAME]
type: index
---

# [AREA_NAME]

(no notes yet)
```

Example: if domains are "design", "engineering", "learning", create:
- `notes/design.md`
- `notes/engineering.md`
- `notes/learning.md`

### File 14: First project (PERSONALIZED)

Create `notes/[PROJECT]/[PROJECT].md`:

```markdown
---
description: Project index for [PROJECT_NAME]
type: index
---

# [PROJECT_NAME]

[Brief description from conversation]

## Status

Just started.

## Active

(nothing yet)
```

Use a slug for the folder name (lowercase, hyphens). Example: "My iOS App" becomes `notes/my-ios-app/my-ios-app.md`.

### File 15: `CLAUDE.md` (THE MOST IMPORTANT FILE -- PERSONALIZED)

This is ~250-300 lines. Personalize it with the user's name, personality, domains, and extraction categories.

Replace ALL variables in `[BRACKETS]`:

- `[USER_NAME]` -- the user's name
- `[PERSONALITY_PREAMBLE]` -- 2-3 sentences about agent personality, derived from conversation
- `[DOMAIN_LIST]` -- comma-separated domain names (e.g. "design, engineering, learning")
- `[AREAS]` -- domains joined by ` | ` for frontmatter (e.g. `design | engineering | learning`)
- `[EXTRACTION_CATEGORIES]` -- bulleted list of what insights to extract
- `[DOMAINS_SECTION]` -- one entry per domain with description

Here is the complete CLAUDE.md template:

````markdown
# [USER_NAME]'s Knowledge Vault

[PERSONALITY_PREAMBLE -- 2-3 sentences about agent personality, derived from conversation. Example: "You are direct, casual, and opinionated. When something looks wrong, say so. When there's a clear next step, recommend it."]

This vault is standalone -- it sits above all projects. [Brief description of what feeds into it based on domains].

---

## Session Rhythm

Every session follows three phases. Do not skip any of them.

### Orient (start of every session)

1. Read `self/identity.md`, `self/methodology.md`, `self/goals.md`
2. Read `ops/sessions/current.json` if it exists -- reconstruct where things were left
3. Read `ops/tasks.md` -- surface what is in flight
4. Check `ops/reminders.md` for anything due
5. Summarize back: "Here's where we are..." covering active threads and immediate next step

### Work (during session)

- One task at a time. Finish or explicitly park before switching.
- When a decision is made, note it immediately in the relevant note
- When something is discovered that doesn't belong to the current task, drop it in `inbox/`
- When switching away from a feature, update its parking state before moving on

### Persist (end of every session)

1. Update the active feature note or project index with current state
2. Update `self/goals.md` with any shifted priorities
3. Update `ops/tasks.md` -- mark done, add new
4. Update `ops/sessions/current.json` with notes_created, notes_modified, discoveries
5. The vault is committed automatically by the auto-save hook -- do not manually commit it.
6. Confirm: "Session saved."

---

## Note Design

Every note is a single idea expressed as a proposition -- a sentence, not a label.

Not: `Flutter navigation`
But: `nested navigation in Flutter breaks back-stack on Android`

Not: `Design system decisions`
But: `design tokens should be semantic not literal to survive theme changes`

The title IS the claim. If you can't write the title as a sentence, the idea isn't ready to be a note yet. Put it in `inbox/` first.

---

## Wiki Links

Use `[[note title]]` with relationship context: `[[note]] -- extends this`, `[[note]] -- contradicts above`, `[[note]] -- example of this pattern`. Cross-domain links are valuable -- follow them. Never leave dangling links -- create a stub or remove.

---

## Indexes

Indexes are navigation files, not knowledge files.

**Two levels:**

1. **Area maps** -- one per domain ([DOMAIN_LIST]) -- always at `notes/` root
2. **Project maps** -- one per active project -- in `notes/<project>/`

A note belongs to one project (folder) and one area (frontmatter field). Cross-project principles live at `notes/` root.

Feature indexes track: status, what's done/not done, decisions made with rationale, and the exact stopping point + next step. Every parked feature gets one.

---

## Memory Routing

| Content type                          | Goes to                          |
|---------------------------------------|----------------------------------|
| A new insight or claim                | `inbox/` then process to `notes/`|
| A parked feature state                | feature index in `notes/<project>/` |
| A cross-domain insight                | `notes/` root + linked from area map |
| Something half-formed                 | `inbox/`                         |
| A friction signal about this system   | `ops/observations/`              |
| A goal shift                          | `self/goals.md`                  |
| A reminder with a date                | `ops/reminders.md`               |
| A task or next action                 | `ops/tasks.md`                   |

**Never write directly to `notes/`.** Route through `inbox/` first.

---

## Processing

`inbox/` sources are processed with `/process`: extract insights (one per note), find connections, check quality.

**Extraction categories** -- when processing a source, look for:
[EXTRACTION_CATEGORIES]

`/process-all` batch-processes the entire inbox with fresh context per source.

---

## Schema

**Note frontmatter:**
```yaml
---
description: One sentence adding context the title doesn't
type: note
area: [AREAS]
created: YYYY-MM-DD
topics: []
---
```

**Index frontmatter:**
```yaml
---
description: Navigation index for [area/project/feature]
type: index
---
```

**Description rules:** Must add info the title doesn't. ~150 chars max. Answers "so what?"

---

## Maintenance

Condition-based, not scheduled. The orient hook surfaces triggered conditions automatically.

| Condition                                      | Action                    |
|------------------------------------------------|---------------------------|
| Inbox items exceed threshold                   | Run `/process`            |
| Disconnected notes accumulating                | Run `/connect`            |
| Feature note stale but still active            | Run `/revisit`            |
| Observations accumulating                      | Run `/review`             |
| Any dangling wiki links detected               | Fix immediately           |

Thresholds are configured in `marrow.yaml`.

---

## Skills Reference

| Skill | What it does |
|-------|-------------|
| `/process` | Process inbox source into connected notes |
| `/connect` | Find connections for a note, add wiki links |
| `/audit` | Check note structure across all notes |
| `/tasks` | View and manage the task stack |
| `/next` | Recommend the most valuable next action |
| `/revisit` | Update old notes with new context |
| `/remember` | Save a lesson so you don't repeat a mistake |
| `/process-all` | Batch process entire inbox |
| `/review` | Triage accumulated findings |

---

## Domains

[DOMAINS_SECTION]

---

## Common Pitfalls

- **Collector's Fallacy** -- capturing is not processing. If inbox grows, process before adding more.
- **Orphan Drift** -- run `/connect` after captures. Orphans that can't be connected shouldn't exist.
- **Temporal Staleness** -- feature notes untouched but still active = stale.
````

---

## Part 5: Initialize Git and Commit

After all files are generated, run:

```bash
cd [VAULT_PATH]
git init
git add -A
git commit -m "marrow: initial vault setup"
```

If git init fails (e.g. directory is already a repo), that's fine -- just add and commit.

---

## Part 6: Success Message

After everything is done, print:

> Your vault is ready at **[VAULT_PATH]**. Here's what I created:
>
> - **self/** -- your identity, methodology, and goals
> - **notes/** -- area maps for [DOMAIN_LIST], project folder for [PROJECT_NAME]
> - **ops/** -- tasks, reminders, and session tracking
> - **templates/** -- note and index structure
> - **inbox/** and **archive/** -- for processing sources
>
> The orient hook will load your context at the start of every session. The auto-commit hook saves changes to git automatically.
>
> Next time you open Claude Code in this folder, Marrow will greet you with your current state. Try adding a note to `inbox/` and running `/process` to see the pipeline in action.

---

## Extraction Guide

Use this reference when analyzing the user's Turn 1 response.

**Identity signals:**
- Name: "I'm [name]", "my name is [name]", or any self-identification
- Role: job titles, descriptions of what they do professionally
- What they do: projects mentioned, companies, freelance/employed

**Domain signals:**
- Explicit: "I work in design and engineering"
- Implicit: "I build apps and also do a lot of reading" -> engineering, learning
- Work vs life: "I want to track my fitness goals too" -> add a life/health domain
- Use short, lowercase slug names for domains: "design", "engineering", "learning", "finance", "health", "writing"

**Personality signals:**
- Direct statements: "I like tools that are blunt with me"
- Tone of their message: casual/formal, verbose/terse, warm/analytical
- Preferences: "don't sugarcoat", "be encouraging", "keep it brief"
- If no personality signal: default to clear, direct, and moderately casual

**Extraction category signals:**
- Explicit: "I want to capture design decisions"
- Implicit: "I keep forgetting why I made certain choices" -> decisions and rationale
- Role-based defaults if nothing explicit:
  - Engineer: technical decisions, architecture trade-offs, bugs and fixes, things learned
  - Designer: design decisions and rationale, patterns and anti-patterns, user insights
  - Researcher: key findings, methodology notes, open questions, connections to other work
  - General: decisions and rationale, things learned, open questions, patterns noticed

**First project signals:**
- "I'm currently working on [X]"
- "My main project is [X]"
- "I'm building [X]"
- If no project mentioned: ask in a follow-up turn
