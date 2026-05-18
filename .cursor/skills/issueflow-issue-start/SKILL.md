---
name: issueflow-issue-start
description: >-
  Run the /issue-start workflow: pick the current issue, read issue<N>_plan.md
  (offer to run /issue-plan if missing), then implement with project conventions
  (e.g. uv run).
disable-model-invocation: true
---

# issue-flow — issue start (`/issue-start`)

Follow this skill when the user wants to **begin implementation** from issue notes, matching `.cursor/commands/issue-start.md` and project rules. Planning itself lives in `/issue-plan`; this skill is now implementation-only.

## When to use

- The user runs `/issue-start`, mentions **issue-start**, or asks to implement from `.issueflows/01-current-issues/`.
- Work should follow the issue-flow markdown workflow and stay aligned with `.cursor/rules/issueflow-rules.mdc` when present.

## Instructions

1. **Select the issue** — Read `.issueflows/01-current-issues/`. If there is no `*_original.md` (or multiple ambiguous groups), **stop** and ask which issue to use.

2. **Branch status preflight** (non-destructive) — Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind counts vs `origin/<default>`. If on the default branch, propose creating an issue branch (`git switch -c <N>-<short-slug>`); ask before running. If the current branch matches `^(\d+)-.+` and files for that issue now live in `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, warn the branch looks stale and ask whether to switch back before continuing. If the branch is neither default nor an issue-style branch, warn and ask whether to continue. Never delete a branch from `/issue-start`.

3. **Sweep stale current issues** (auto-safe) — Group files in `.issueflows/01-current-issues/` by `issueNN_` prefix. For every group **other than the focus issue**, move the whole group to `.issueflows/03-solved-issues/` if any of its status files contains `- [x] Done` (case-insensitive on `done`), otherwise move it to `.issueflows/02-partly-solved-issues/`. Never move the focus issue's files. Report every move.

4. **Plan precondition** — Look for `issue<N>_plan.md` in `.issueflows/01-current-issues/`.
   - **Plan present:** read it and treat it as the source of truth for scope and approach.
   - **Plan missing:** do **not** hard-stop. Ask the user to choose one of:
     - **Run `/issue-plan` now**, then continue into implementation after they confirm the plan.
     - **Proceed without a plan** — add a short `- Skipped /issue-plan on <date>` note to `issue<N>_status.md` and continue.
     - **Abort.**

5. **Implement** — Execute the plan (or the explicitly-acknowledged plan-less path). Prefer minimal, focused diffs. Match existing code style and tooling.

6. **Project conventions**
   - Run Python via **`uv run`** (scripts, pytest, tools), not bare `python`, unless the user overrides.
   - Manage dependencies with **`uv add` / `uv remove` / `uv sync`** only.
   - After meaningful progress, update or create `issue<N>_status.md` under `.issueflows/01-current-issues/` with an explicit `- [ ] Done` checkbox that stays unchecked until fully resolved. Record what has landed and what remains.

7. **Hand off** — When the implementation is ready to ship, tell the user to run `/issue-close` (optionally with `bump`/`patch`/`minor`/`major`). Parking work mid-stream goes through `/issue-pause`.

8. **Reporting** — Summarize what changed, what remains, and where the issue docs live. Include any branch warnings from step 2, any group moves from step 3, and whether the plan was followed or explicitly skipped.

## Constraints

- Do not invent issue text; treat `*_original.md` as a read-only source of requirements unless the user asks to edit it.
- The stale sweep in step 3 is the **only** automatic folder move `/issue-start` performs, and it never touches the focus issue's own files.
- Never delete or force-update git branches from `/issue-start`.
- Do not write or modify `issue<N>_plan.md` from here — changes to the plan go through `/issue-plan`.
