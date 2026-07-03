---
name: iflow-plan
description: >-
  Run the /iflow-plan workflow: read the focus issue in
  .issueflows/01-current-issues/, draft a structured plan
  in issue<N>_plan.md, and get explicit user confirmation before any
  implementation starts.
disable-model-invocation: true
---

# issue-flow — issue plan (`/iflow-plan`)

Follow this skill when the user wants to **design the approach** for an issue before touching code.

## When to use

- The user runs `/iflow-plan`, mentions **issue-plan**, or asks you to design the approach / write a plan for the current issue.
- You want a clear, confirmed plan before `/iflow-start` begins editing code.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent preflight` for the branch status preflight (step 2). The
> CLI is optional: if it is missing or errors, fall back to the manual commands
> below. (`issue-flow` is only present when the user installed it, e.g.
> `uv tool install issue-flow`.)

1. **Find the focus issue.** Look in `.issueflows/01-current-issues/` for `issue<N>_original.md`. If it is missing or multiple groups are ambiguous, **stop** and ask. Suggest `/iflow-init` first.

2. **Branch status preflight** (non-destructive). Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind vs `origin/<default>`. If on the default branch, suggest creating an issue branch (`git switch -c <N>-<short-slug>`) but do **not** auto-run it — planning itself does not require a branch switch.

3. **Read context.** Load `issue<N>_original.md` and any existing `issue<N>_status.md`. If `.issueflows/04-designs-and-guides/this-project.md` exists, read it for project-specific context, then skim `.issueflows/04-designs-and-guides/` for relevant design docs.

4. **Prior-art discovery** (before drafting the plan):
   - **Toolbox:** Skim `.issueflows/00-tools/` (start with its `README.md` index) for an existing helper that already does part of the work, so the plan reuses it instead of proposing a new script.
   - **Graph (optional):** If `graphify-out/GRAPH_REPORT.md` exists, skim **God Nodes**, **Communities**, and **Suggested Questions** whose names touch the affected area; note community numbers. If absent, skip (grep-only is fine).
   - **Grep:** Search for sibling helpers / functions adjacent to the new work (domain prefixes like `filter_*`, `remove_*`, or names from the issue / graph).
   - **Record:** Under **`## Constraints`**, add **`### Prior art`** listing each hit (function + module, convention, mirror / coexist / migrate later). If nothing relevant: `- None found (toolbox + grep + graph checked).`
   - **Strong overlap:** Put merge-vs-coexist decisions in **`## Open questions`**, not silent choices in Approach.

5. **Explore read-only** — search code, read files most likely to change, check existing tests; keep research proportional to the issue.


5a. **Grill the approach** (planning interview). The [`grill-me`](../grill-me/SKILL.md) skill is available to stress-test the approach before drafting: ask the user to "grill me" (or turn it on by default with `grill_me_default = true` in `.issueflows/config.toml`). It interviews one question at a time until every decision branch is resolved, then feeds the conclusions into the plan.


6. **Write `issue<N>_plan.md`** under `.issueflows/01-current-issues/` with these sections:
   - **Goal** — one or two sentences.
   - **Constraints** — project rules, back-compat, scope limits; include **`### Prior art`** (from step 4).
   - **Approach** — concrete design, data flow, ordering.
   - **Files to touch** — path + what changes for each.
   - **Test strategy** — the project's documented test command (e.g. `uv run pytest`, or `pytest` inside the activated conda env) and any new tests.
   - **Open questions** — anything that needs the user's call before coding.

   Keep it terse but specific. Use markdown links to files when useful.

7. **Scope check.** If the plan is broad (many unrelated files, mixes refactors with feature work, multiple independent deliverables), propose splitting into smaller issues or phased PRs before finalizing the plan.

8. **Confirm with the user.** Present the plan and **stop**. Accept one of: **Accept** (ready for `/iflow-start`), **Revise** (update `issue<N>_plan.md` in place and re-confirm), or **Abort**.

9. **Conflict on existing `issue<N>_plan.md`.** Do not overwrite silently. Offer: update in place (after review), keep both (`issue<N>_plan.v2.md`), or leave as is.

## Constraints

- `/iflow-plan` is **read-only on source code**. The only file it writes is `.issueflows/01-current-issues/issue<N>_plan.md`.
- Do not move files between `01-` / `02-` / `03-` folders from `/iflow-plan`.
- Do not run tests or package managers; that belongs to `/iflow-start` and `/iflow-close`.
- Do not proceed to implementation from this skill. Hand off to `/iflow-start` once the user confirms.
