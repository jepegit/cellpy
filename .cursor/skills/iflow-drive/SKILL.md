---
name: iflow-drive
description: >-
  Compose-only orchestrator: draft an epic from an existing issue, publish
  every stage, run /iflow-auto each epoch, final review, then local -d
  cleanup and /iflow-status.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — drive (`/iflow-drive`)

Follow this skill to run a **compose-only** path from an existing GitHub
issue `<N>`: draft epic (auto-accept unless grill-me) → publish every
stage → `/iflow-auto` each epoch → final review (create leftover findings)
→ local cleanup **`-d` only** → `/iflow-status`.


Contract: `.issueflows/04-designs-and-guides/drive-mode.md`.

Do **not** fork yolo / cycle / auto / epic internals. Read and follow
those skills; this one only sequences them and records `drive_status.md`.

## Input

- **`<N>`** — existing GitHub issue that becomes the epic anchor
  (required). Drive never creates the anchor; if none exists, stop and
  point at `/iflow-issue epic <intent>`.
- **`grill` / `grill-me`** — run grill-me on the epic goal before
  confirming the draft. Else auto-set `Status: confirmed` after draft
  (also honour project `grill_me_default`).
- **`loops:<n>`** — forwarded to `/iflow-auto`.
- **`dry-run`** — resolve planned stages / queue, show what would run,
  **stop** (no confirm, no writes).
- **`abort` / `stop` / `cancel` / `halt` mid-run** — not start tokens.
  Any user message that *is* (or starts with) `abort` / `stop` /
  `cancel` / `halt` (case-insensitive, optional leading `/`) **stops**
  at the next stage or issue boundary. Record `aborted` in
  `drive_status.md`. Same floor as cycle `onfail:stop` (leave the repo
  on the default branch, clean).


**Invoke:** type `iflow drive` in chat, or `/iflow-drive` from the slash menu (`iflow-drive` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

1. **Require `<N>`.** If missing or not a positive integer, **stop** and
   ask. Run `gh issue view <N> --repo <owner/repo>` to confirm the
   issue exists.

2. **`dry-run`.** If the token is present: show whether
   `.issueflows/05-epics/epic<N>_plan.md` exists and
   its `Status`; list unpublished vs published specs; run
   `issue-flow agent epic-status <N> --json` when a plan exists; show
   the queue `issue-flow agent queue --epic <N> --json` would return;
   note that cleanup would be `local only` + skip A2 (`-d` / reachable
   only). **Stop** without confirm or writes.

3. **Drive confirm** (only planned interruption besides auto's budget
   ask and cycle/yolo stop conditions). Present in normal prose: issue
   `#<N>` as epic anchor; that this run will **draft-accept** (unless
   grill-me / `grill_me_default`), **publish every unpublished stage**,
   run **`/iflow-auto` for each unfinished published stage**, run a
   **final adversarial review** that may create/reopen GitHub issues,
   then **local cleanup `-d` only** (no Phase B, no `-D`), then
   `/iflow-status`. Require explicit yes. This confirm **covers**
   epic's plan-accept, per-stage publish confirms, auto's overnight
   confirm, final-review creates, and reachable-only cleanup — do not
   re-ask those mid-run.

4. **Write / update `drive_status.md`** at
   `.issueflows/01-current-issues/drive_status.md`:
   anchor `<N>`, checklist (`draft`, `publish`, `auto`, `final_review`,
   `cleanup`, `status`), `findings:` list (empty at start), last
   outcome `pending`, ISO timestamp. Not an `issue<N>_*` group —
   sweeps leave it alone.

5. **Abort check** (repeat at every stage / issue boundary below). If
   the latest user message is (or starts with) `abort` / `stop` /
   `cancel` / `halt` (case-insensitive, optional leading `/`): set
   `last_outcome: aborted` in `drive_status.md`, leave the repo on the
   default branch clean, **stop**. Do not start the next stage or
   issue.

6. **Draft epic.** Follow `.cursor/skills/iflow-epic/SKILL.md`
   for `/iflow-epic <N>` (write-free on GitHub).
   - If `epic<N>_plan.md` already has `Status: confirmed`, **skip**
     draft and publish; jump to step 8 (auto).
   - If a draft exists, reuse it unless the user asked to revise.
   - Grill only when the `grill` / `grill-me` token is present **or**
     `grill_me_default` is baked true. Else set `Status: confirmed`
     without a second plan-accept prompt (covered by the drive
     confirm).
   - Mark `draft` done in `drive_status.md`.

7. **Publish all stages.** Loop `/iflow-epic <N> publish` (same skill)
   until no unpublished specs remain. Honour `Published: #<M>`
   idempotency. The drive confirm replaces each per-stage publish
   confirm — do not re-ask. Commit `Published:` lines on a chore/issue
   branch or tiny PR — **not** unpushed on default (issue #303). Mark
   `publish` done in `drive_status.md`.

8. **Auto each part.** While `issue-flow agent epic-status <N> --json`
   reports an unfinished published stage: follow
   `.cursor/skills/iflow-auto/SKILL.md` for `/iflow-auto <N>`
   (forward `loops:<n>` when given). The drive confirm covers auto's
   overnight authorization — do not re-ask. Honour `epoch_gated`,
   cycle/yolo stop conditions, and auto's **budget ask** (accept /
   grant N more loops / abort) as a **planned pause**, not a drive
   failure. Append created/reopened numbers to `drive_status.md`
   `findings:`. Abort-check at each stage / issue boundary.

9. **Final review.** When every published stage is `done` (or the user
   **accepted** a budget ask): run `/iflow-auto <N> review` (same
   skill). Create/reopen GitHub issues for remaining gaps using the
   criteria table in
   `.issueflows/04-designs-and-guides/advanced-auto-mode.md`.
   The drive confirm covers those creates. Record numbers in
   `findings:`. Do **not** start another epoch unless the user later
   runs `/iflow-auto` themselves. Mark `final_review` done.

10. **Cleanup.** Follow `.cursor/skills/iflow-cleanup/SKILL.md`
    with trailing `local only` **and skip Phase A2**:
    - switch to default, `git pull --ff-only`, `git fetch --prune`;
    - `issue-flow agent worktree-remove` for **`reachable`** worktrees
      only;
    - `git branch -d` on **`reachable`** branches only.
    Leave `squash_landed`, `merged_pr_divergent`, and `unique_work`.
    Never `git branch -D`. Never Phase B (no remote deletes, no
    findings issue). The drive confirm covers this reachable-only
    pass — do not re-ask. Mark `cleanup` done.

11. **Report + status.** Summarize stages published, PRs merged,
    findings issues (created/reopened numbers), cleanup counts
    (`-d` deletions / worktrees removed / squash-landed left). Set
    `last_outcome: done` in `drive_status.md`. Then follow
    `.cursor/skills/iflow-status/SKILL.md` (`/iflow-status`).
    Mark `status` done.

## Constraints

- **Off-path:** `/iflow` never auto-dispatches here.
- Compose `/iflow-epic` + `/iflow-auto` + `/iflow-cycle` +
  `/iflow-yolo` + `/iflow-cleanup` + `/iflow-status`; do not fork them.
- Never rebase / force-push / push default.
- Cleanup never `git branch -D`, never Phase B.
- Do not leave `Published: #<M>` unpushed on home default (#303).
- Auto's budget ask remains a planned pause (accept / grant / abort).
- User abort tokens stop only at the next stage / issue boundary.
