---
name: iflow-auto
description: >-
  Unattended large-change orchestrator over a confirmed epic: cycle a stage,
  adversarial review, loop budget, next-epoch gate when the queue is clear.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — advanced auto (`/iflow-auto`)

Follow this skill to run an **unattended large-change flow** over a confirmed
epic: select a stage, drive it through `/iflow-cycle`, record durable state in
`auto_status.md`, run adversarial inter-epoch review (`review`), then honour
the adversarial **loop budget** (re-queue or stop-and-ask).


Contract: `.issueflows/04-designs-and-guides/advanced-auto-mode.md`
(criteria table, budget, outcomes).

## Input

- **`<N>`** — epic anchor issue number (requires `epic<N>_plan.md` with
  `Status: confirmed`).
- **`stage <k>`** — optional stage index; default = earliest unfinished published
  stage (`issue-flow agent epic-status <N> --json` → `current_stage`).
- **`loops:<n>`** — override adversarial loop budget for this run (baked default
  **2** from `[issueflow].auto_adversarial_loops`).
- **`review`** — run only the adversarial procedure for epic `<N>` (and optional
  `stage <k>`); skip cycle unless a full auto run is also intended.
- **`status`** — print `auto_status.md` / epic-status and stop (no confirm).
- **`dry-run`** — resolve stage + queue, show what would run, stop (no confirm).


**Invoke:** type `iflow auto` in chat, or `/iflow-auto` from the slash menu (`iflow-auto` also works).




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
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

1. **Resolve epic.** Require `.issueflows/05-epics/epic<N>_plan.md`
   with `Status: confirmed`. Run `issue-flow agent epic-status <N> --json`. If
   the plan is draft/missing, **stop** and point at `/iflow-epic <N>`.

2. **Select stage.** Use `stage <k>` if given; else `current_stage` from
   epic-status. If every published stage is done, report done and stop.

3. **Resolve loop budget.** Trailing `loops:<n>` (positive int) > baked
   **2** > default 2. Record the effective budget.

4. **`status` / `dry-run`.** If either token is present: show epic, stage, queue
   (`issue-flow agent queue --epic <N> --json`), budget, loop count from
   `auto_status.md` if present; **stop** without confirm or writes.

5. **`review`-only path.** If `review` is present and this is not a full
   overnight run: jump to **Adversarial procedure** (step 9). If
   `auto_status.md` lacks overnight authorization for this epic/stage, present
   one confirm (epic, stage, that create/reopen may happen) before proceeding.

6. **Overnight confirm** (full auto; only planned interruption before the
   budget ask). Present in normal prose: epic `#<N>`, stage index + title,
   ordered queue (numbers + titles), that each issue runs full yolo +
   auto-merge via `/iflow-cycle`, **loop budget**, and that adversarial review
   may **reopen or create** GitHub issues under that confirm. Require explicit
   yes.

7. **Write / update `auto_status.md`** at
   `.issueflows/01-current-issues/auto_status.md`:
   epic, stage, `loop_count` (`0` at start of full run), `budget`, ISO
   timestamp, last outcome `pending`, overnight authorization. Not an
   `issue<N>_*` group — sweeps leave it alone.

8. **Run the stage via `/iflow-cycle`.** Follow
   `.cursor/skills/iflow-cycle/SKILL.md` for `epic <N>` (the CLI queues
   the current stage). The overnight confirm above covers cycle's consolidated
   confirm — do not re-ask. Honour cycle stop conditions and `onfail:stop`.
   Update `auto_status.md` with the cycle outcome.

9. **Adversarial procedure** (after cycle, or via `review`):

   a. Gather evidence (read-only first): stage issues + states from
      `epic-status`; merged PR titles/bodies via `gh pr list` /
      `gh pr view --repo <owner/repo>` for those issues; epic `## Goal` /
      Constraints and stage Goal / paragraph from `epic<N>_plan.md`.
   b. Apply the criteria table in
      `.issueflows/04-designs-and-guides/advanced-auto-mode.md`
      (stage goal, epic progress, spec honesty, blast radius).
   c. If **clear**: set `last_outcome: adversarial_clear` and a short findings
      summary in `auto_status.md`. Proceed to **Next-epoch gate** (step 11).
   d. If **gaps**: for each finding, prefer `gh issue reopen <M> --repo
      <owner/repo>` plus a comment with concrete remaining acceptance when an
      existing stage issue owns the gap; otherwise `gh issue create --repo
      <owner/repo>` with Spec, Goal, **`Model: deep`**, `Depends on`, and
      `Part of epic #<N>.` — no new label in v1. Record numbers + notes in
      `auto_status.md` with `last_outcome: adversarial_findings`.
   e. No extra user prompts while acting under overnight / review confirm
      (except the budget ask in step 10).

10. **Loop control** (only after `adversarial_findings`):

    a. Increment `loop_count` in `auto_status.md` by 1 for this adversarial pass.
    b. Collect open work: reopened stage issues + newly created inter-epoch
       blockers still open (from the findings list / `epic-status`).
    c. If open work remains and `loop_count` **<** `budget`: re-queue those
       issue numbers via `/iflow-cycle` (explicit numbers; overnight confirm
       already covers cycle confirms — do not re-ask), then **return to step 9**
       (adversarial procedure). Keep yolo/cycle safeguards.
    d. If open work remains and `loop_count` **>=** `budget`: set
       `last_outcome: budget_ask` and **stop and ask** in normal prose — three
       options only:
       - **accept** current implementation (record `accepted`; do not re-queue)
       - **grant N more loops** (raise effective `budget` by N for this run;
         clear `budget_ask`; continue from 10c)
       - **abort** (record `aborted`; stop)
    e. If no open work remains after findings were addressed by a prior loop,
       treat as clear for loop purposes and go to step 11.
    f. After user **accept**, still run step 11 (gate will refuse advance if
       open work remains).

11. **Next-epoch gate** (after `adversarial_clear`, loops drained with no open
    work, or budget **accept**):

    a. Re-run `issue-flow agent epic-status <N> --json`. Stage `k` is clear
       only when that stage's `done` is true **and** no open inter-epoch
       blocker numbers remain in `auto_status.md` findings.
    b. If **not** clear: set `last_outcome: epoch_gated`, list open numbers /
       blockers, **do not** start stage `k+1`, go to step 12.
    c. If clear and a later unfinished published stage exists: under the same
       overnight authorization, set `auto_status.md` stage to that index,
       reset `loop_count` to `0`, `last_outcome: pending`, and **return to
       step 2** (select/run that stage). Do not re-ask overnight confirm.
    d. If every published stage is done: set `last_outcome: complete`.

12. **Report.** Epic, stage, cycle results (if any), adversarial outcome +
    issue numbers, `loop_count` / `budget`, gate result, `auto_status.md`
    path. Remind `/iflow-cleanup` after merges.

## Constraints

- **Off-path:** `/iflow` never auto-dispatches here.
- Do not weaken yolo/cycle safeguards.
- Do not run `/iflow-cleanup` from this skill.
- Never start stage `k+1` while stage `k` is not clear (`epoch_gated`).
- Compose `/iflow-epic` + `/iflow-cycle` + `/iflow-yolo`; do not fork them.
