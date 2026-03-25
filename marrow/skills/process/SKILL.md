---
name: marrow:process
description: End-to-end source processing. Chains queue, extract, connect, and check -- each phase in a fresh subagent. The full pipeline in one command. Triggers on "/process", "/process [file]", "process this end to end".
user-invocable: true
context: fork
model: sonnet
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task
argument-hint: "[file] -- path to source file to process end-to-end"
---

## EXECUTE NOW

**Target: $ARGUMENTS**

Parse immediately:
- Source file path: the file to process (required)
- If target is empty: list files in `inbox/` and ask which to process

**START NOW.** Run the full pipeline.

---

## Pipeline Overview

The pipeline chains four phases. Each phase runs in a fresh subagent for clean context. State lives in the queue file -- the pipeline is stateless orchestration on top of stateful queue entries.

```
Source file
    |
    v
Phase 1: /queue -- create extract task, move source to archive
    |
    v
Phase 2: /extract -- extract notes from source
    |
    v
Phase 3: /connect -- find connections, add wiki links, update indexes
    |
    v
Phase 4: /check -- validate schema on each created note
    |
    v
Phase 5: Archive -- move task files, generate summary
    |
    v
Complete
```

---

## Phase 1: Queue

Invoke /queue on the target file to create the extract task, check for duplicates, and move the source to its archive folder.

**How to invoke:**

Use the Task tool to spawn a subagent:
```
Task(
  prompt = "Run /queue {file_path}",
  description = "queue: {source-name}"
)
```

Or execute the /queue workflow directly if Task tool is unavailable.

**Capture from queue output:**
- **Batch ID**: the source basename (used for filtering in subsequent steps)
- **Archive folder path**: where the source was moved
- **next_note_start**: the note numbering start

Report: `> Queued: {source-name}`

**If queue reports the file was already processed:** Ask the user whether to proceed or skip. Do NOT auto-skip -- the user may want to re-process with different scope.

---

## Phase 2: Extract

Process the extract task. This spawns a subagent that runs /extract, pulling notes from the source and creating task entries in the queue.

**How to invoke:**

```
Task(
  prompt = "Run /extract on the task for batch {batch_id} in ops/queue/",
  description = "extract: {batch_id}"
)
```

After completion, read the queue to count extracted notes and enrichments.

Report:
```
> Extracted: {N} notes, {M} enrichments
  Processing {total_tasks} tasks through the pipeline...
```

**If zero notes extracted:** Report the issue. Ask the user whether to retry with different scope or skip.

---

## Phase 3: Connect

For each note created in the extract phase, find connections and add wiki links.

**How to invoke:**

```
Task(
  prompt = "Run /connect on these notes: {list of created note paths}",
  description = "connect: {batch_id} ({N} notes)"
)
```

This phase:
- Finds related notes via keyword search across `notes/`
- Adds wiki links to the Relevant Notes footer
- Updates area indexes and project indexes with the new notes
- Adds relationship context to every link ("-- extends this", "-- contradicts above")

Report:
```
> Connected: {N} notes linked, {M} indexes updated
```

---

## Phase 4: Check

Validate schema on each created note to catch quality issues early.

**How to invoke:**

```
Task(
  prompt = "Run /check on these notes: {list of created note paths}",
  description = "check: {batch_id} ({N} notes)"
)
```

This phase runs the full schema check suite:
- Required fields (description, topics)
- Description quality
- YAML validity
- Link health
- Composability

Report:
```
> Checked: {N} notes -- {P} PASS, {W} WARN, {F} FAIL
```

**If any FAIL results:** Report which notes failed and why. These need manual fixes before the batch is considered complete.

---

## Phase 5: Archive Batch

When all phases are complete, archive the batch.

1. Move all task files from `ops/queue/` to `ops/queue/archive/{date}-{batch_id}/`
2. Generate a batch summary file: `{batch_id}-summary.md`
3. Mark completed entries in the queue as archived

The summary should include:
- Source file name and original location
- Number of notes extracted
- Number of enrichments
- List of created notes with titles
- Check results summary (PASS/WARN/FAIL counts)

---

## Phase 6: Final Report

```
--=={ process }==--

Source: {source_file}
Batch: {batch_id}

Extraction:
  Notes extracted: {N}
  Enrichments identified: {M}

Connections:
  Wiki links added: {C}
  Indexes updated: {T}

Quality:
  Check results: {P} PASS, {W} WARN, {F} FAIL

Archive: ops/queue/archive/{date}-{batch_id}/
Summary: {batch_id}-summary.md

Notes created:
- [[note title 1]]
- [[note title 2]]
- ...
```

---

## Error Handling

**Phase failure at any stage:**
1. Report the failure with context (which phase, which task, what error)
2. Show the current queue state for this batch
3. Suggest remediation
4. Do NOT attempt to continue automatically past failures

**The pipeline is resumable.** Queue state persists across sessions:
- /queue detects prior processing and asks whether to proceed
- Subsequent phases pick up from the last completed phase (queue is the source of truth)

**Queue failure:** If /queue fails (file not found, duplicate detected and user declines), stop the pipeline entirely.

**Extract failure:** If /extract finds zero notes, report and stop. Do not proceed to an empty connect phase.

**Connect failure:** If connecting fails, the notes are still created. Only the linking is missing -- re-run /connect manually.

**Check failure:** If checking fails, notes and connections exist. Only the quality validation is missing -- re-run /check manually.

---

## Resumability

The pipeline is designed to be interrupted and resumed at any point:

| Interrupted At | How to Resume |
|----------------|---------------|
| Before queue | Run /process again (starts fresh) |
| After queue, before extract | /extract {batch_id} |
| After extract, before connect | /connect on created notes |
| After connect, before check | /check on created notes |
| After check, before archive | Archive manually |

State lives in the queue file. The pipeline reads queue state, not session state. This means you can interrupt, close the session, and resume later.

---

## Edge Cases

**No target file:** List `inbox/` candidates, suggest the best one based on age.

**Source already queued:** /queue detects this and asks the user. If they decline, the pipeline stops cleanly.

**Large source (2500+ lines):** /extract handles chunking automatically. The pipeline does not need special handling.

---

## Critical Constraints

**never:**
- Skip the queue phase (duplicate detection is important)
- Continue past a failed phase automatically
- Archive a batch with incomplete tasks

**always:**
- Run each phase in a fresh subagent when Task tool is available
- Report progress at each phase boundary
- Verify all phases are done before archiving
- Show the user what was created (list of notes)
- Suggest next steps if interrupted
