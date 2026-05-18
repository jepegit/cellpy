---
name: issueflow-iflow
description: >-
  Run the /iflow smart dispatcher: detect where the focus issue stands in the
  lifecycle (via files in .issueflows/01-current-issues/ and
  status markers) and dispatch to /issue-init, /issue-plan, /issue-start, or
  /issue-close. Forwards trailing args verbatim. Never auto-dispatches to
  /issue-pause, /issue-cleanup, or /issue-yolo.
disable-model-invocation: true
---

# issue-flow — iflow smart dispatcher (`/iflow`)

Follow this skill when the user wants to run **the right next step** in the issue-flow lifecycle without remembering which specific command applies. Matches `.cursor/commands/iflow.md`.

## When to use

- The user runs `/iflow`, mentions **iflow**, or asks "what's the next step?" during an issue-flow lifecycle.
- You want a single entry point that routes to `/issue-init`, `/issue-plan`, `/issue-start`, or `/issue-close` based on current state.

Do **not** use this skill for `/issue-pause`, `/issue-cleanup`, or `/issue-yolo`. Those are explicit-only commands.

## Instructions

1. **Resolve the focus issue number `N`.**
   - `git branch --show-current`. If it matches `^(\d+)-.+`, the leading digits are the **authoritative** `N`.
   - List `issue<n>_*` groups in `.issueflows/01-current-issues/`, and also check `.issueflows/02-partly-solved-issues/` and `.issueflows/03-solved-issues/` for archived groups matching `N`.
   - Pick `N` by precedence:
     1. **Branch-derived `N` wins**, regardless of whether a group for `N` exists in `01-current-issues/`. State **A** will apply when no `issue<N>_*` files are present yet. If `issue<N>_*` is archived under `02-partly-solved-issues/` or `03-solved-issues/`, warn the user that `/issue-init`'s archived-issue guard will ask for an explicit confirmation before re-opening.
     2. No branch-derived `N`, exactly one group exists in `01-current-issues/` → use it.
     3. No branch-derived `N`, no groups at all → state **A** (dispatch `/issue-init`; it will ask for a number).
     4. No branch-derived `N`, multiple groups → **stop and ask**.

2. **Detect state and choose the dispatch target** (first match wins):

   - **A** — no `issue<N>_original.md` (or no focus issue) → dispatch to **`/issueflow-issue-init`**. Reason: "no `*_original.md` yet".
   - **B** — original exists, no `issue<N>_plan.md` → dispatch to **`/issueflow-issue-plan`**. Reason: "no plan file yet".
   - **C** — plan exists, and status file is missing or its `- [x] Done` is unchecked → dispatch to **`/issueflow-issue-start`**. Reason: "plan is confirmed but status is not `- [x] Done`".
   - **D** — status file contains `- [x] Done` (case-insensitive on `done`) → dispatch to **`/issueflow-issue-close`**. Reason: "status marks the issue `- [x] Done`".

3. **Announce and dispatch.** Print one line like `/iflow -> /issue-plan  (issue #N: no plan file yet)` and then follow the chosen command's playbook. Forward the user's trailing text verbatim.

4. **Respect downstream checkpoints.** Never suppress the downstream command's own prompts (plan confirmation, unrelated-changes prompt, etc.). `/iflow` adds no new confirmation layer of its own.

5. **Report.** Summarize: focus issue `N` and how it was resolved, which command was dispatched and why, the downstream output, and a one-line hint when an off-path command is the natural next step:
   - state **D** + PR likely merged → "after the PR merges, run `/issue-cleanup`"
   - mid-stream context switch needed → "to park this work, run `/issue-pause`"
   - tiny fix that would benefit from a single-shot chain → "consider `/issue-yolo` next time"

## Constraints

- Never auto-dispatch to `/issue-pause`, `/issue-cleanup`, or `/issue-yolo`.
- If the focus issue cannot be resolved (multiple groups, branch ambiguous), stop and ask.
- Do not modify files beyond what the downstream command would normally modify. `/iflow` itself writes nothing — all file changes come from the dispatched command.
- Dispatch to at most one command per `/iflow` invocation.
