# Run — auto (`/iflow-run auto`)

Read this to run an **unattended large-change flow** over a confirmed
epic: select a stage, drive it through `/iflow-run cycle`, record durable state in
`auto_status.md`, run adversarial inter-epoch review (`review`), then honour
the adversarial **loop budget** (re-queue or stop-and-ask).

**Review criteria** (used in step 4):

| Check | Pass when | Fail → action |
|---|---|---|
| Stage goal met | The stage's merged PRs together satisfy the stage goal | Reopen incomplete issues and/or create blocker issues |
| Epic goal progress | No clear regression against the epic `## Goal` / constraints | Same |
| Spec honesty | Landed work matches each issue's spec (no silent scope cut) | Reopen with the concrete remaining acceptance |
| Blast radius | No unplanned shared-file or API breaks outside the stage | Create blocker issues with spec, `Depends on`, and `Part of epic #<N>` |

Prefer `gh issue reopen <M>` (+ comment) when a stage issue still owns the gap; `gh issue create` only for cross-cutting work. Created blockers carry `Model: deep`.

## Input

- **`<N>`** — epic anchor issue number (requires `epic<N>_plan.md` with
  `Status: confirmed`).
- **`stage <k>`** — optional stage index; default = earliest unfinished published
  stage (`issue-flow agent epic-status <N> --json` → `current_stage`).
- **`loops:<n>`** — override adversarial loop budget for this run (baked default
  **2** from `[issueflow].auto_adversarial_loops`).
- **`nonyolo:merge|pr-only|stop`** — forwarded to `/iflow-run cycle`: how the
  stage's `yolo: no` issues land (baked default **`merge`** from
  `[issueflow].cycle_nonyolo`). A `yolo: no` judgment is **not** a stop by
  itself — cycle runs it on the non-yolo lane.
- **`review`** — run only the adversarial procedure for epic `<N>` (and optional
  `stage <k>`); skip cycle unless a full auto run is also intended.
- **`status`** — print `auto_status.md` / epic-status and stop (no confirm).
- **`dry-run`** — resolve stage + queue, show what would run, stop (no confirm).

## Instructions

1. **Resolve epic.** Require `.issueflows/05-epics/epic<N>_plan.md`
   with `Status: confirmed`. Run `issue-flow agent epic-status <N> --json`. If
   the plan is draft/missing, **stop** and point at `/iflow-issue epic <N>`.

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
   ordered queue (numbers + titles), that each issue runs the full chain +
   auto-merge via `/iflow-run cycle`, the **non-yolo issues** in the stage (queue
   payload `nonyolo`, or the plan's `yolo: no` judgments) and the `nonyolo`
   policy that applies to them, **loop budget**, and that adversarial review
   may **reopen or create** GitHub issues under that confirm. Require explicit
   yes.

7. **Write / update `auto_status.md`** at
   `.issueflows/01-current-issues/auto_status.md`:
   epic, stage, `loop_count` (`0` at start of full run), `budget`, ISO
   timestamp, last outcome `pending`, overnight authorization. Not an
   `issue<N>_*` group — sweeps leave it alone.

8. **Run the stage via `/iflow-run cycle`.** Follow
   `.cursor/skills/iflow-run/cycle.md` for `epic <N>` (the CLI queues
   the current stage; forward `nonyolo:<policy>` when given). The overnight
   confirm above covers cycle's consolidated confirm and the non-yolo lane —
   do not re-ask, and do not stop at a `yolo: no` issue (only `nonyolo:stop`
   halts there). Honour cycle stop conditions and `onfail:stop`. A merge that
   reports the PR is **already merged** is a success. Update `auto_status.md`
   with the cycle outcome.

9. **Adversarial procedure** (after cycle, or via `review`):

   a. Gather evidence (read-only first): stage issues + states from
      `epic-status`; merged PR titles/bodies via `gh pr list` /
      `gh pr view --repo <owner/repo>` for those issues; epic `## Goal` /
      Constraints and stage Goal / paragraph from `epic<N>_plan.md`.
   b. Apply the **review criteria** table above (stage goal, epic progress,
      spec honesty, blast radius).
   c. If **clear**: set `last_outcome: adversarial_clear` and a short findings
      summary in `auto_status.md`. Proceed to **Next-epoch gate** (step 11).
   d. If **gaps**: for each finding, prefer `gh issue reopen <M> --repo
      <owner/repo>` plus a comment with concrete remaining acceptance when an
      existing stage issue owns the gap; otherwise `gh issue create --repo
      <owner/repo>` with Spec, Goal, **`Model: deep`**, `Depends on`, and
      `Part of epic #<N>.` — no new label in v1. Record numbers + notes in
      `auto_status.md` with `last_outcome: adversarial_findings`.

**Multi-line GitHub text (PowerShell-safe).** Bash `<<'EOF'` heredocs fail in Windows PowerShell (`Missing file specification after redirection operator`). Write the text to a file and pass that file:

- `gh issue create`, `gh issue edit`, and `gh pr create` take `--body-file <path>`.
- `git commit` takes `-F <path>`.

```powershell
@'
line one

line two
'@ | Set-Content -Encoding utf8 body.md
gh issue create --repo owner/repo --title "title" --body-file body.md
```

Bash accepts the same `--body-file` / `-F` flags. Use that pattern for every multi-line body.

   e. No extra user prompts while acting under overnight / review confirm
      (except the budget ask in step 10).

10. **Loop control** (only after `adversarial_findings`):

    a. Increment `loop_count` in `auto_status.md` by 1 for this adversarial pass.
    b. Collect open work: reopened stage issues + newly created inter-epoch
       blockers still open (from the findings list / `epic-status`).
    c. If open work remains and `loop_count` **<** `budget`: re-queue those
       issue numbers via `/iflow-run cycle` (explicit numbers; overnight confirm
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
    path.

## Constraints

- Do not weaken yolo/cycle safeguards. The non-yolo lane changes how a PR
  lands, never which safeguards run.
- A `yolo: no` issue is not a stop unless `nonyolo:stop`.
- Do not run `/iflow-cleanup` from this skill.
- Never start stage `k+1` while stage `k` is not clear (`epoch_gated`).
- Compose `/iflow-issue epic` + `/iflow-run cycle` + `/iflow-run yolo`; do not fork them.
