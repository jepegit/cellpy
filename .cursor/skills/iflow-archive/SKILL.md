---
name: iflow-archive
description: >-
  Condense old solved issue groups into one dated summary file, then delete
  the originals. Destructive, one consolidated confirm.
disable-model-invocation: true
---

# issue-flow — archive solved issues (`/iflow-archive`)

Follow this skill to **shrink the solved-issues archive**:
old `issue<N>_*` groups under `.issueflows/03-solved-issues/` are
summarised into one dated markdown file and the originals are deleted (they
stay recoverable through git history).

Do **not** use this to park or close an active issue — that is `/iflow-pause` / `/iflow-close`. This skill only touches `.issueflows/03-solved-issues/`.

## Input

- **(nothing)** — smart default: propose archiving every solved group **except the 5 most recent** (highest issue numbers).
- **`keep <K>`** — same, but keep the `<K>` most recent groups instead.
- **an explicit list** (e.g. `12 13 24`) — archive exactly those issues.
- **`all`** — archive every solved group.


### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.



## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, the
> mechanical deletion step has a deterministic shortcut:
> `issue-flow agent archive <N> [<N> ...]` (add `--dry-run` to preview,
> `--json` for a machine-readable object). It removes the chosen groups'
> files and reports the pre-archive HEAD sha — you still select candidates,
> confirm with the user, and write the summary file yourself. The CLI is
> optional: if it is missing or errors, fall back to the manual instructions
> below.

1. **Preflight.** Require a **clean working tree** (`git status --porcelain`); if dirty, **stop** and ask the user to commit or stash first — the recovery ref is only meaningful when the deletion lands as its own commit. Capture the pre-archive ref: `git rev-parse HEAD`.

2. **Select candidates.** List every `issue<N>_*` group in `.issueflows/03-solved-issues/` with its number and title (from the `# Issue #N: <title>` heading of `issue<N>_original.md`). Apply the input rule (default: all except the 5 most recent by issue number). Show the resulting candidate list — number, title, file names — and let the user add/remove issues.

3. **Consolidated confirm** (destructive — written in normal prose, never shortened). One prompt covering exactly: which issues get summarised, that their files will be **deleted**, and that recovery relies on git history via the recorded ref. Do not proceed without a clear yes.

4. **Summarise (before deleting).** Append to `.issueflows/03-solved-issues/YYYY-MM-DD_archived_issues.md` (today's date; create the file if missing). Structure:

   ```markdown
   # Archived issues — YYYY-MM-DD

   Pre-archive git ref: `<sha>`
   Recover any archived file with `git show <sha>:<path>` (or browse `git log -- <path>`).

   ## Issue #<N>: <title>

   - Source: <GitHub issue URL, from the original file>
   - Archived files: issue<N>_original.md, issue<N>_plan.md, issue<N>_status.md
   - Summary: 2–4 sentences distilled from the original / plan / status files —
     what the issue was, what was done, and the outcome.
   ```

   One `## Issue` section per archived issue. If the dated file already exists (same-day rerun), append a `---` separator followed by a fresh `Pre-archive git ref:` line for this run, then the new issue sections. The dated filename deliberately does **not** match `issue<N>_*`, so it never interferes with issue grouping.

5. **Delete.** Remove the archived groups' files — CLI fast path (`issue-flow agent archive ...`), or manually `git rm .issueflows/03-solved-issues/issue<N>_*` per issue.

6. **Commit offer.** Propose a single commit, e.g. `chore(iflow): archive <count> solved issues (pre-archive ref <short-sha>)`, including the new/updated dated file and the deletions. Ask before committing; never push from this skill.

7. **Report.** Summarise: how many issues were archived, the dated file path, the pre-archive ref, and the one-line recovery recipe.

## Constraints

- **Off-path.** Never auto-dispatch from `/iflow`, `/iflow-start`, or `/iflow-close`. The user opts in explicitly.
- **Destructive, so gated.** Never delete anything before the consolidated confirm in step 3, and never delete files that were not summarised in step 4.
- Only `.issueflows/03-solved-issues/` is touched — never `01-current-issues/`, `02-partly-solved-issues/`, `00-tools/`, or `04-designs-and-guides/`.
- Requires a clean working tree; the deletion should land as its own commit so `git show <ref>:<path>` recovery always works.
- Summaries are interpretive (agent judgment); the CLI only ever does the mechanical deletion.
