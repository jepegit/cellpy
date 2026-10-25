# Run — drive (`/iflow-run drive`)

Read this to run a **compose-only** path from an existing GitHub
issue `<N>`: draft epic (auto-accept unless grill-me) → publish every
stage → `/iflow-run auto` each epoch → final review (create leftover findings)
→ local cleanup (`-d` reachable + `-D` squash-landed) → `/iflow-status`.

Do **not** fork yolo / cycle / auto / epic internals. Read and follow
those skills; this one only sequences them and records `drive_status.md`.

## Input


- **`<N>`** — existing GitHub issue that becomes the epic anchor
  (required). Drive never creates the anchor; if none exists, stop and
  point at `/iflow-issue epic <intent>`.

- **`grill` / `grill-me`** — run grill-me on the epic goal before
  confirming the draft. Else auto-set `Status: confirmed` after draft
  (also honour project `grill_me_default`).
- **`loops:<n>`** — forwarded to `/iflow-run auto`.
- **`nonyolo:merge|pr-only|stop`** — forwarded to `/iflow-run auto` →
  `/iflow-run cycle`: how the epic's `yolo: no` issues land (default from
  config **`merge`**). Drive is a carry-through path; a
  `yolo: no` judgment is **not** a stop by itself.
- **`dry-run`** — resolve planned stages / queue, show what would run
  (including the non-yolo issues per stage), **stop** (no confirm, no
  writes).
- **`abort` / `stop` / `cancel` / `halt` mid-run** — not start tokens.
  Any user message that *is* (or starts with) `abort` / `stop` /
  `cancel` / `halt` (case-insensitive, optional leading `/`) **stops**
  at the next stage or issue boundary. Record `aborted` in
  `drive_status.md`. Same floor as cycle `onfail:stop` (leave the repo
  on the default branch, clean).

## Instructions


1. **Require `<N>`.** If missing or not a positive integer, **stop** and
   ask. Run `gh issue view <N> --repo <owner/repo>` to confirm the
   issue exists.


2. **`dry-run`.** If the token is present: show whether
   `.issueflows/05-epics/epic<N>_plan.md` exists and
   its `Status`; list unpublished vs published specs; run
   `issue-flow agent epic-status <N> --json` when a plan exists; show
   the queue `issue-flow agent queue --epic <N> --json` would return,
   with its `nonyolo` list and the `nonyolo` policy that would apply
   (from the plan's per-issue `yolo:` judgments when nothing is
   published yet); note that cleanup would be `local only`, `-d` on
   reachable branches plus `-D` on squash-landed ones (step 10). **Stop**
   without confirm or writes.


3. **Drive confirm** (only planned interruption besides auto's budget
   ask and cycle/yolo stop conditions). Present in normal prose: issue
   `#<N>` as epic anchor; that this run will **draft-accept** (unless
   grill-me / `grill_me_default`), **publish every unpublished stage**,
   run **`/iflow-run auto` for each unfinished published stage**, run a
   **final adversarial review** that may create/reopen GitHub issues,
   then **local cleanup** (`-d` on reachable branches, `-D` on
   squash-landed ones; no Phase B), then `/iflow-status`. List the
   **non-yolo issues** (from the plan's `yolo: no` judgments / the queue
   payload's `nonyolo`) and the `nonyolo` policy — with `merge` say
   plainly that their PRs are auto-merged like the yolo ones. Require
   explicit yes. This confirm **covers** epic's plan-accept, per-stage
   publish confirms, auto's overnight confirm, the non-yolo lane,
   final-review creates, and the local cleanup (both `-d` and `-D`) —
   do not re-ask those mid-run.


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

6. **Draft epic.** Follow `.cursor/skills/iflow-issue/epic.md`
   for `/iflow-issue epic <N>` (write-free on GitHub).
   - If `epic<N>_plan.md` already has `Status: confirmed`, **skip**
     draft and publish; jump to step 8 (auto).
   - If a draft exists, reuse it unless the user asked to revise.
   - Grill only when the `grill` / `grill-me` token is present **or**
     `grill_me_default` is baked true. Else set `Status: confirmed`
     without a second plan-accept prompt (covered by the drive
     confirm).
   - Mark `draft` done in `drive_status.md`.

7. **Publish all stages.** Loop `/iflow-issue epic <N> publish` (same skill)
   until no unpublished specs remain. Honour `Published: #<M>`
   idempotency. The drive confirm replaces each per-stage publish
   confirm — do not re-ask. Commit `Published:` lines on a chore/issue
   branch or tiny PR — **not** unpushed on default. Mark
   `publish` done in `drive_status.md`.

8. **Auto each part.** While `issue-flow agent epic-status <N> --json`
   reports an unfinished published stage: follow
   `.cursor/skills/iflow-run/auto.md` for `/iflow-run auto <N>`
   (forward `loops:<n>` and `nonyolo:<policy>` when given). The drive
   confirm covers auto's overnight authorization and the non-yolo lane
   — do not re-ask, and do not stop at a `yolo: no` issue (cycle runs it
   on the non-yolo lane; only `nonyolo:stop` halts there). Honour
   `epoch_gated` and cycle/yolo stop conditions. Auto's **budget ask**
   (accept / grant N more loops / abort) stays a **planned pause**, not a
   drive failure. A merge that reports the PR is **already merged** is a
   success, not a stop. Append created/reopened numbers to
   `drive_status.md` `findings:`. Abort-check at each stage / issue
   boundary.

9. **Final review.** When every published stage is `done` (or the user
   **accepted** a budget ask): run `/iflow-run auto <N> review` (same
   skill). Create/reopen GitHub issues for remaining gaps using the
   review-criteria table in `auto.md`.
   The drive confirm covers those creates. Record numbers in
   `findings:`. Do **not** start another epoch unless the user later
   runs `/iflow-run auto` themselves. Mark `final_review` done.

10. **Cleanup.** Follow `.cursor/skills/iflow-cleanup/SKILL.md`
    with trailing `local only`, running **both** Phase A1 and A2 under
    the drive confirm (pass the `drive` token so cleanup does not
    re-ask):
    - switch to default, `git pull --ff-only`, `git fetch --prune`;
    - `issue-flow agent worktree-remove` for **`reachable`** and
      **`squash_landed`** worktrees;
    - `git branch -d` on **`reachable`** branches;
    - `git branch -D` on **`squash_landed`** branches, and on
      `merged_pr_divergent` ones whose only divergence is commits
      **older** than the PR's `mergedAt` (nothing newer than the merge
      — `issue-flow agent local-branches --json` shows the tip SHA and
      merge time; leave any branch with a commit after it).
    Leave `unique_work` untouched, always. Never Phase B (no remote
    deletes, no findings issue). Print the tip SHAs of everything
    deleted with `-D` in the report so the user can `git branch <name>
    <sha>` to recover. This is the carry-through the drive confirm
    authorized — do not re-ask. Mark `cleanup` done.

11. **Report + status.** Summarize stages published, PRs merged,
    findings issues (created/reopened numbers), cleanup counts
    (`-d` / `-D` deletions with tip SHAs, worktrees removed). Set
    `last_outcome: done` in `drive_status.md`. Then follow
    `.cursor/skills/iflow-status/SKILL.md` (`/iflow-status`).
    Mark `status` done.

## Constraints

- Compose `/iflow-issue epic` + `/iflow-run auto` + `/iflow-run cycle` +
  `/iflow-run yolo` + `/iflow-cleanup` + `/iflow-status`; do not fork them.
- Never rebase / force-push / push the **default branch**. Issue
  branches are different: close / pr-sync may rebase them onto
  `origin/<default>` (`issue-flow agent sync-branch`, optionally
  `--base <parent>` for a child stacked on a squash-landed parent) and
  `git push --force-with-lease` them — that is the normal PR-queue
  sync, not a violation.
- A `yolo: no` issue is not a stop: it runs on cycle's non-yolo lane
  under the `nonyolo` policy (`merge` unless a token
  overrides). Only `nonyolo:stop` halts there.
- Cleanup: `-d` on reachable, `-D` on squash-landed (and
  merged-PR-divergent with nothing newer than the merge) — both under
  the drive confirm; never `unique_work`, never Phase B.
- Do not leave `Published: #<M>` unpushed on home default.

- Auto's budget ask remains a planned pause (accept / grant / abort).

- User abort tokens stop only at the next stage / issue boundary.
