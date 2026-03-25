---
name: marrow:extract
description: Extract structured notes from source material. Comprehensive extraction is the default -- every insight that serves the vault gets extracted. For relevant sources, skip rate must be below 10%. Zero extraction from a relevant source is a BUG. Triggers on "/extract", "/extract [file]", "extract insights", "mine this".
user-invocable: true
context: fork
model: sonnet
allowed-tools: Read, Write, Grep, Glob, Bash
---

## EXECUTE NOW

**Target: $ARGUMENTS**

Parse immediately:
- If target contains a file path: extract insights from that file
- If target contains a batch ID: look up the extract task in `ops/queue/` and process its source
- If target is empty: scan `inbox/` for unprocessed items, pick one

**Execute these steps:**

1. Read the source file fully -- understand what it contains
2. **Source size check:** If source exceeds 2500 lines, STOP. Plan chunks of 350-1200 lines. Process each chunk with fresh context. See "Large Source Handling" section below.
3. Hunt for insights (see extraction categories below)
4. For each candidate: run keyword grep duplicate checks against `notes/`
5. Classify as OPEN (needs more investigation) or CLOSED (standalone, ready)
6. Output extraction report with titles, classifications, extraction rationale
7. Wait for user approval before creating files

**START NOW.** Reference below explains methodology -- use to guide, not as output.

---

## The Mission

You are the extraction engine. Raw source material enters. Structured, atomic notes exit. Everything between is your judgment -- and that judgment must err toward extraction, not rejection.

### The Core Distinction

| Concept | What It Means |
|---------|---------------|
| **Having knowledge** | The vault contains information |
| **Articulated reasoning** | The vault explains WHY something works as a traversable note |

**Having knowledge is not the same as articulating it.** Even if information is embedded in the system, the vault may lack the externalized reasoning explaining WHY it works. That reasoning is what you extract.

### The Extraction Question (ask for EVERY candidate)

**"Would a future session benefit from this reasoning being a retrievable note?"**

If YES -> extract to appropriate category
If NO -> verify it is truly off-topic before skipping

### INVALID Skip Reasons (these are BUGS)

- "validates existing approach" -- validations ARE evidence. Extract them.
- "already captured in system config" -- config is implementation, not articulation. The WHY needs a note.
- "we already do this" -- DOING is not EXPLAINING. The explanation needs externalization.
- "obvious" -- obvious to whom? Future sessions need explicit reasoning.
- "near-duplicate" -- near-duplicates almost always add detail. Create enrichment task.
- "not a claim" -- is it an implementation idea? tension? validation? Those ARE extractable.

### VALID Skip Reasons (rare)

- Completely off-topic (unrelated to the vault's domains)
- Too vague to act on (applies to everything, disagrees with nothing)
- Pure summary with zero extractable insight
- LITERALLY identical text already exists (not "same topic" -- IDENTICAL)

**For relevant sources: skip rate < 10%. Zero extraction = BUG.**

---

## Extraction Categories

| Category | What to Find | Output Type |
|----------|--------------|-------------|
| Core notes | Direct assertions about the domain | note |
| Patterns | Recurring structures across sources | note |
| Comparisons | How different approaches compare, trade-offs | note |
| Tensions | Contradictions, conflicts, unresolved trade-offs | tension note |
| Anti-patterns | What breaks, what to avoid, failure modes | problem note |
| Enrichments | Content that adds detail to existing notes | enrichment task |
| Open questions | Unresolved questions worth tracking | note (open) |
| Implementation ideas | Techniques, workflows, features to build | methodology note |
| Validations | Evidence confirming an approach works | note |

Categories 1-9 extract directly. No additional filtering needed for on-topic content.

### Category Detection Signals

**Core signals:**
- Direct assertions: "the key insight is...", "this means that...", "the pattern is..."
- Evidence: "research shows...", "data indicates..."
- Named methods: any named system, technique, or framework

**Comparison signals:**
- "X vs Y", "trade-off between...", "prefer X when...", "unlike Y, this..."

**Tension signals:**
- "contrary to...", "however...", "the problem with...", "fails when..."

**Enrichment signals:**
- Content covering ground similar to an existing note
- New examples, evidence, or framing for an established claim
- Deeper explanation of something already captured shallowly

**Implementation signals:**
- "we could build...", "would enable...", "a tool that...", "pattern for..."

**Validation signals:**
- "this supports...", "evidence shows...", "validates...", "confirms..."

---

## Workflow

### 1. Orient

Before reading the source, understand what already exists:

```bash
# Get descriptions from existing notes
for f in notes/*.md notes/**/*.md; do
  [[ -f "$f" ]] && echo "=== $(basename "$f" .md) ===" && rg "^description:" "$f" -A 0
done
```

Scan descriptions to understand current notes. This prevents duplicate extraction and helps identify enrichment opportunities.

### 2. Read Source Fully

Read the ENTIRE source. Understand what it contains, what it argues, what domain it serves.

**Planning the extraction:**
- How many notes do you expect from this source?
- What categories will be represented?
- Is this relevant (comprehensive extraction) or general (be more selective)?

**Hunt for:**
- Assertions that could be argued for or against
- Patterns that apply beyond this specific source
- Insights that change how you think about something

### 3. Categorize FIRST, Then Route

**STOP. Before ANY filtering, determine the category of each candidate.**

| Category | How to Identify | Route To |
|----------|-----------------|----------|
| Core note | Direct assertion about a domain | -> note (no extra filtering) |
| Implementation idea | Describes a feature, tool, workflow | -> methodology note (no extra filtering) |
| Tension | Describes a conflict, risk, trade-off | -> tension note (no extra filtering) |
| Validation | Evidence confirming an approach | -> note (no extra filtering) |
| Near-duplicate | Keyword search finds related vault note | -> evaluate for enrichment task |
| Off-topic | General insight unrelated to vault domains | -> apply selectivity check |

### 4. Duplicate Detection

For each candidate, run duplicate detection via keyword grep:

```bash
grep -rl "{key terms}" notes/ 2>/dev/null | head -5
```

**The Enrichment Judgment (DEFAULT TO ENRICHMENT):**

| Situation | Action |
|-----------|--------|
| Exact text already exists | SKIP (truly identical -- RARE) |
| Same claim, source adds nothing new | SKIP (verify by re-reading existing note) |
| Same claim, source has MORE detail/examples | -> ENRICHMENT TASK |
| Same topic, DIFFERENT claim | -> EXTRACT as new note |
| Related mechanism, different scope | -> EXTRACT as new note |

**DEFAULT TO ENRICHMENT.** If source mentions the same topic, it almost certainly adds something. Truly identical content is RARE.

### 5. Classify Each Extraction

Every extracted candidate gets classified:

- **CLOSED** -- standalone claim, ready for processing as-is
- **OPEN** -- needs more investigation, testable hypothesis, requires evidence

### 6. Present Findings

Report what you found by category. **Include counts:**

```
Extraction scan complete.

SUMMARY:
- notes: N
- implementation ideas: N
- tensions: N
- enrichment tasks: N
- validations: N
- open questions: N
- skipped: N
- TOTAL OUTPUTS: N

---

NOTES:
1. [note as sentence] -- connects to [[existing note]]
2. [note as sentence] -- extends [[existing note]]
...

IMPLEMENTATION IDEAS:
1. [feature/pattern] -- what it enables, why it matters
...

TENSIONS:
1. [X vs Y] -- the conflict, why it matters
...

ENRICHMENT TASKS:
1. [[existing note]] -- source adds [what is missing]
...

SKIPPED:
- [description] -- why nothing extractable
```

**Wait for user approval before creating files.** Never auto-extract.

### 7. Extract (With User Approval)

For each approved note:

**a. Craft the title**

The title IS the claim. Express the concept in exactly the words that capture it.

Test: "this note argues that [title]"
- Must make grammatical sense
- Must be something you could agree or disagree with
- Lowercase with spaces
- No punctuation that breaks filesystems: . * ? + [ ] ( ) { } | \ ^

**b. Write the note**

```markdown
---
description: [~150 chars elaborating the claim, adds info beyond title]
type: [note | methodology | problem | learning | tension]
area: [area from vault domains]
created: YYYY-MM-DD
topics: []
---

# [prose-as-title proposition]

[Body: 150-400 words showing reasoning]

Use connective words: because, but, therefore, which means, however.
Acknowledge uncertainty where appropriate.
Show the path to the conclusion, not just the conclusion.

---

Source: [[source filename]]

Relevant Notes:
- [[related note]] -- [why it relates: extends, contradicts, builds on]

Topics:
- [[relevant index]]
```

**c. Verify before writing**

- Title passes the claim test ("this note argues that [title]")
- Description adds information beyond the title (not a restatement)
- Body shows reasoning, not just assertion
- At least one relevant note connection identified
- At least one index link
- Source attribution present

**d. Create the file**

Write to: `notes/[title].md`

---

## Large Source Handling

**For sources exceeding 2500 lines: chunk processing is MANDATORY.**

| Source Size | Chunk Count | Chunk Size |
|-------------|------------|------------|
| 2500-4000 lines | 3-4 chunks | 700-1200 lines |
| 4000-6000 lines | 4-5 chunks | 800-1200 lines |
| 6000+ lines | 5+ chunks | 1000-1500 lines |

**Chunk boundaries:** Split at natural section breaks (headings, topic transitions). Never split mid-paragraph.

When processing in chunks:
1. Keep a running list of extracted notes across chunks
2. Later chunks check against earlier chunks' extractions (not just existing vault notes)
3. The final extraction report covers ALL chunks combined

---

## Enrichment Detection

When source content adds value to an EXISTING note rather than creating a new one, create an enrichment task instead.

| Signal | Action |
|--------|--------|
| Source has better examples for an existing note | Enrichment: add examples |
| Source has deeper framing or context | Enrichment: strengthen reasoning |
| Source has citations or evidence | Enrichment: add evidence base |
| Source has a different angle on the same claim | Enrichment: add perspective |
| Source has concrete implementation details | Enrichment: add actionable specifics |

**The enrichment default:** When in doubt between "new note" and "enrichment to existing note", lean toward enrichment. The existing note already has connections and integration. Adding to it compounds existing value.

---

## Quality Gates

### Calibration Check (REQUIRED Before Finishing)

**STOP before outputting results.** Count your outputs by category:

**Expected yields by source size:**

| Source Size | Expected Outputs | Skip Rate |
|-------------|------------------|-----------|
| ~100 lines | 5-10 outputs | varies by relevance |
| ~350 lines | 15-30 outputs | < 10% for relevant sources |
| ~500+ lines | 25-50+ outputs | < 10% for relevant sources |

**Zero extraction from a relevant source is a BUG.**

### Red Flags: Extraction Too Tight

If you catch yourself doing ANY of these, STOP and recalibrate:

1. **"validates existing approach" as skip reason** -- Validations ARE valuable. Extract as note with evidence framing.
2. **"already captured in config" as skip reason** -- Config is implementation. Notes explain WHY it works.
3. **"we already do this" as skip reason** -- DOING is not EXPLAINING. The reasoning needs externalization.
4. **"obvious" as skip reason** -- Obvious to whom? Future sessions need explicit reasoning.
5. **Treating near-duplicates as skips instead of enrichments** -- Near-duplicates almost always add value.

### Red Flags: Extraction Too Loose

- Extracting vague observations with no actionable content
- Titles that are topics, not claims ("knowledge management" instead of "knowledge management fails without active maintenance")
- Body text that is pure summary without reasoning

---

## Note Design Reference

### Titles

Titles are claims that work as prose when linked:

```
since [[explicit structure beats implicit convention]], the question becomes...
the insight is that [[small differences compound through repeated selection]]
```

The claim test: "this note argues that [title]"

### Description

One field. ~150 characters. Must add NEW information beyond the title -- scope, mechanism, or implication.

### Body

Show reasoning. Use connective words. Acknowledge uncertainty.

Bad:
> Quality matters. When creation is easy, curation becomes the work.

Good:
> The easy part is capture. We bookmark things, save screenshots, clip articles we never open again. The hard part is doing something with it all. Since [[structure without processing provides no value]], the question becomes: who does the selecting?

### Footer

```markdown
---

Source: [[source filename]]

Relevant Notes:
- [[related note]] -- extends this by adding the temporal dimension

Topics:
- [[relevant index]]
```

---

## Task File Mode (when called from /process)

When invoked as part of the /process pipeline (a task file exists in `ops/queue/`), also:

1. Update the extract task's "Execution Notes" and "Outputs" sections
2. For EACH note, create a task file in `ops/queue/` named `{source}-NNN.md`
3. For EACH enrichment, create a task file continuing the numbering
4. Update `ops/queue/queue.json`: mark extract task done, add per-note entries

**Task file structure for notes:**

```markdown
---
claim: "[the note as a sentence]"
classification: closed | open
source_task: [source-basename]
---

# Note NNN: [note title]

Source: [[source filename]]

## Extract Notes
Extracted from [source_task]. This is a [CLOSED/OPEN] note.
Rationale: [why this was extracted, what it contributes]

---

## Connect
(to be filled by /connect phase)

## Check
(to be filled by /check phase)
```

---

## Critical Constraints

Never auto-extract. Always present findings and wait for user approval.

**When in doubt, extract.** For relevant sources, err toward capturing. Implementation ideas, tensions, validations, open questions, and near-duplicates all have value.

**Remember:**
- Implementation ideas are NOT "not claims" -- they are roadmap
- Tensions are NOT "not claims" -- they are wisdom
- Enrichments are NOT "duplicates" -- they add detail
- Validations are NOT "already known" -- they are evidence

**For relevant sources: skip rate < 10%. Zero extraction = BUG.**
