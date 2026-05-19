---
name: issueflow-issue-yolo
description: >-
  Run the /issue-yolo workflow: preflight (no default branch, clean tree,
  passing tests), single consolidated confirm, then chain init → plan → start
  → close for small, low-risk issues. Stops on any ambiguity.
disable-model-invocation: true
---

# issue-flow — issue yolo (`/issue-yolo`)

Follow this skill when the user wants to **blast through a small, low-risk issue** in one shot, matching `.cursor/commands/issue-yolo.md`.

Use only for minor fixes, doc tweaks, and similar low-risk changes. Anything non-trivial should go through the individual commands.

## When to use

- The user runs `/issue-yolo`, `/issue-fast`, mentions **issue-yolo**, or asks to "just do it" for a small issue.
- The task is obviously small and the user has accepted that there will be no mid-run confirmation checkpoints.

## Preflight (abort on any failure)

1. **Refuse on default branch.** If the current branch is `main` / `master` / the detected default, **stop** and tell the user to create or switch to an issue branch first. Do not silently create one from yolo.

2. **Refuse with dirty unrelated changes.** Run `git status --porcelain`. If anything uncommitted is not clearly part of the target issue, ask once; if still unclear, **stop**. Suggest committing or stashing first.

3. **Tests must pass up front.** Run `uv run pytest` (or the repo's documented test command). On any failure, **stop** before the chain starts.

4. **Single consolidated confirm.** Present the full planned chain explicitly (issue reference, target branch, repo, downstream commands including any `bump` / `patch` / `draft` flags). Require an explicit yes; any other input aborts.

## Chain

Once preflight has passed and the user confirmed:

1. **`/issueflow-issue-init`** — capture the issue (or skip if `*_original.md` already exists for the focus issue).
2. **`/issueflow-issue-plan`** — write a **short** `issue<N>_plan.md` (Goal + Approach + Files to touch + Test strategy). Auto-confirm — the consolidated confirm above covered it. If the scope check reveals the change is not actually small, **abort the yolo chain** and tell the user to run the commands individually.
3. **`/issueflow-issue-start`** — implement the plan without an additional plan-mode prompt.
4. **Re-run tests.** `uv run pytest` again. On failure, **stop** before commit / push / PR.
5. **`/issueflow-issue-close`** — run the full close flow (optional version bump if the user passed `bump` / `patch` / `minor` / `major`, issue-folder update, commit, push, PR). Do **not** chain `/issueflow-issue-cleanup` automatically — the PR has not merged yet.

## Post-run

Leave the user on the issue branch with the PR URL. Remind them to re-run `/issue-cleanup` once the PR merges.

## Constraints

- Do not override downstream commands' own constraints (no `-D`, no force-push, etc.). `/issue-yolo` is a chain, not a free pass.
- If **any** downstream step requires a human decision (unrelated changes in `git status`, ambiguous version bump, merge conflict, failed test), **stop** and hand back to the user.
- Never run `/issue-cleanup` from this skill. Branch deletion always needs the user to see the merged PR first.
