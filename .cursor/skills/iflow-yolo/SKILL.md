---
name: iflow-yolo
description: >-
  Run the /iflow-yolo workflow: preflight (no default branch, clean tree,
  passing tests), single consolidated confirm, then chain init → plan → start
  → close yolo (hands-off close: auto changelog, PR merge, default-branch
  pull) for small, low-risk issues. Stops on any ambiguity.
disable-model-invocation: true
---

# issue-flow — issue yolo (`/iflow-yolo`)

Follow this skill when the user wants to **blast through a small, low-risk issue** in one shot.

Use only for minor fixes, doc tweaks, and similar low-risk changes. Anything non-trivial should go through the individual commands.

## When to use

- The user runs `/iflow-yolo`, `/issue-fast`, mentions **issue-yolo**, or asks to "just do it" for a small issue.
- The task is obviously small and the user has accepted that there will be no mid-run confirmation checkpoints.

## Preflight (abort on any failure)

1. **Refuse on default branch.** If the current branch is `main` / `master` / the detected default, **stop** and tell the user to create or switch to an issue branch first. Do not silently create one from yolo.

2. **Refuse with dirty unrelated changes.** Run `git status --porcelain`. If anything uncommitted is not clearly part of the target issue, ask once; if still unclear, **stop**. Suggest committing or stashing first.

3. **Tests must pass up front.** Run `uv run pytest` (or the repo's documented test command). On any failure, **stop** before the chain starts.

4. **Single consolidated confirm.** Present the full planned chain explicitly (issue reference, target branch, repo, downstream commands including any `bump` / `patch` / `draft` / `stay` flags). Require an explicit yes; any other input aborts. (When `/iflow-pick` routed here via the yolo issue label, its combined confirmation already covered this — do not ask twice.)

## Chain

Once preflight has passed and the user confirmed:

1. **`/iflow-init`** — capture the issue (or skip if `*_original.md` already exists for the focus issue).
2. **`/iflow-plan`** — write a **short** `issue<N>_plan.md` (Goal + Approach + Files to touch + Test strategy). Auto-confirm — the consolidated confirm above covered it. If the scope check reveals the change is not actually small, **abort the yolo chain** and tell the user to run the commands individually.
3. **`/iflow-start`** — implement the plan without an additional plan-mode prompt.
4. **Re-run tests.** `uv run pytest` again. On failure, **stop** before commit / push / PR.
5. **`/iflow-close yolo`** — run the close flow with the `yolo` token (plus forwarded `bump` / `log` / `nohistory` / `draft` / `stay` tokens). The `yolo` token makes close hands-off: changelog bullet written without a confirm prompt, PR **merged** via `gh pr merge --squash` (fall back to `--squash --auto` when branch protection or pending checks block it), then default-branch switch + `git pull --ff-only`. `draft` conflicts with auto-merge — when passed, skip the merge and say so. Do **not** chain `/iflow-cleanup` automatically — local branch deletion stays a user decision.

## Post-run

Report the PR URL, the merge result (merged, or queued via `--auto`), and the final branch. By default `/iflow-close yolo` merges the PR and switches back to the default branch with a pull; forwarded `stay` text leaves the user on the issue branch instead. Remind them that `/iflow-cleanup` will delete the now-merged local branch when they are ready.

## Constraints

- Do not override downstream commands' own constraints (no `-D`, no force-push, etc.). `/iflow-yolo` is a chain, not a free pass.
- If **any** downstream step requires a human decision (unrelated changes in `git status`, ambiguous version bump, merge conflict, failed test), **stop** and hand back to the user.
- Never run `/iflow-cleanup` from this skill. Branch deletion always needs the user to see the merged PR first.
