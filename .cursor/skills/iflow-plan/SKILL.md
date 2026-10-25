---
name: iflow-plan
description: >-
  Draft a structured plan in issue<N>_plan.md and get explicit user
  confirmation before any implementation starts.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — issue plan (`/iflow-plan`)

Follow this skill to **design the approach** for the focus issue before touching code, and to get the plan confirmed ahead of `/iflow-build`.


**Invoke:** type `iflow plan` in chat, or `/iflow-plan` from the slash menu (`iflow-plan` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).


## Optional tokens (command input)

- **`nobuild`** — skip the `auto_build` chain for this run (after Accept, ask / tell the user to run `/iflow-build` even when `auto_build` is true).

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent preflight` for the branch status preflight (step 2). The
> CLI is optional: if it is missing or errors, fall back to the manual commands
> below. (`issue-flow` is only present when the user installed it, e.g.
> `uv tool install issue-flow`.)

1. **Find the focus issue.** Look in `.issueflows/01-current-issues/` for `issue<N>_original.md`. If it is missing or multiple groups are ambiguous, **stop** and ask. Suggest `/iflow-pick` first.

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

7. **Scope check.** If the plan is broad (many unrelated files, mixes refactors with feature work, multiple independent deliverables), propose `/iflow-issue split` (flat 2–5 children) or `/iflow-issue epic` (staged) before finalizing. Do not create children from this skill.

8. **Confirm with the user.** Present the plan and **stop**. Accept one of: **Accept** (ready for `/iflow-build`), **Revise** (update `issue<N>_plan.md` in place and re-confirm), or **Abort**.

   On **Accept** (and no trailing **`nobuild`**), follow the `iflow-build` skill immediately — briefly note that `auto_build` chained the handoff. Still write no code *before* Accept. With **`nobuild`**, or when the user only wants to park the accepted plan, tell them to run `/iflow-build` later instead of chaining.


9. **Conflict on existing `issue<N>_plan.md`.** Do not overwrite silently. Offer: update in place (after review), keep both (`issue<N>_plan.v2.md`), or leave as is.

## Constraints

- `/iflow-plan` is **read-only on source code** until Accept. The only file it writes before Accept is `.issueflows/01-current-issues/issue<N>_plan.md`.
- Do not move files between `01-` / `02-` / `03-` folders from `/iflow-plan`.
- Do not run tests or package managers from planning itself; that belongs to `/iflow-build` and `/iflow-close`.

- `auto_build` only skips the post-Accept pause; Accept / Revise / Abort stay gated. Trailing `nobuild` skips the chain once.

