---
name: issueflow-issue-plan
description: >-
  Run the /issue-plan workflow: read the focus issue in
  .issueflows/01-current-issues/, draft a structured plan
  in issue<N>_plan.md, and get explicit user confirmation before any
  implementation starts.
disable-model-invocation: true
---

# issue-flow — issue plan (`/issue-plan`)

Follow this skill when the user wants to **design the approach** for an issue before touching code, matching `.cursor/commands/issue-plan.md`.

## When to use

- The user runs `/issue-plan`, mentions **issue-plan**, or asks you to design the approach / write a plan for the current issue.
- You want a clear, confirmed plan before `/issue-start` begins editing code.

## Instructions

1. **Find the focus issue.** Look in `.issueflows/01-current-issues/` for `issue<N>_original.md`. If it is missing or multiple groups are ambiguous, **stop** and ask. Suggest `/issue-init` first.

2. **Branch status preflight** (non-destructive). Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind vs `origin/<default>`. If on the default branch, suggest creating an issue branch (`git switch -c <N>-<short-slug>`) but do **not** auto-run it — planning itself does not require a branch switch.

3. **Read context.** Load `issue<N>_original.md` and any existing `issue<N>_status.md`. Explore read-only: search code, read the files most likely to change, check existing tests.

4. **Write `issue<N>_plan.md`** under `.issueflows/01-current-issues/` with these sections:
   - **Goal** — one or two sentences.
   - **Constraints** — project rules, back-compat, scope limits.
   - **Approach** — concrete design, data flow, ordering.
   - **Files to touch** — path + what changes for each.
   - **Test strategy** — `uv run pytest` (or equivalents) and any new tests.
   - **Open questions** — anything that needs the user's call before coding.

   Keep it terse but specific. Use markdown links to files when useful.

5. **Scope check.** If the plan is broad (many unrelated files, mixes refactors with feature work, multiple independent deliverables), propose splitting into smaller issues or phased PRs before finalizing the plan.

6. **Confirm with the user.** Present the plan and **stop**. Accept one of: **Accept** (ready for `/issue-start`), **Revise** (update `issue<N>_plan.md` in place and re-confirm), or **Abort**.

7. **Conflict on existing `issue<N>_plan.md`.** Do not overwrite silently. Offer: update in place (after review), keep both (`issue<N>_plan.v2.md`), or leave as is.

## Constraints

- `/issue-plan` is **read-only on source code**. The only file it writes is `.issueflows/01-current-issues/issue<N>_plan.md`.
- Do not move files between `01-` / `02-` / `03-` folders from `/issue-plan`.
- Do not run tests or package managers; that belongs to `/issue-start` and `/issue-close`.
- Do not proceed to implementation from this skill. Hand off to `/issue-start` once the user confirms.
