---
name: iflow-start
description: >-
  Run the /iflow-start workflow: pick the current issue, read issue<N>_plan.md
  (offer to run /iflow-plan if missing), then implement with the project's
  documented conventions (e.g. uv run, or inside an activated conda env).
disable-model-invocation: true
---

# issue-flow — issue start (`/iflow-start`)

Follow this skill when the user wants to **begin implementation** from issue notes and project rules. Planning itself lives in `/iflow-plan`; this skill is now implementation-only.

## When to use

- The user runs `/iflow-start`, mentions **issue-start**, or asks to implement from `.issueflows/01-current-issues/`.
- Work should follow the issue-flow markdown workflow and stay aligned with `.cursor/rules/issueflow-rules.mdc` when present.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, use
> `issue-flow agent preflight` for the branch status preflight (step 2) and
> `issue-flow agent sweep --except <N>` for the stale sweep (step 3; add
> `--dry-run` to preview). The CLI is optional: if it is missing or errors,
> fall back to the manual instructions below. (`issue-flow` is only present
> when the user installed it, e.g. `uv tool install issue-flow`.)

1. **Select the issue** — Read `.issueflows/01-current-issues/`. If there is no `*_original.md` (or multiple ambiguous groups), **stop** and ask which issue to use.

2. **Branch status preflight** (non-destructive) — Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind counts vs `origin/<default>`. If on the default branch, propose creating an issue branch (`git switch -c <N>-<short-slug>`); ask before running. If the current branch matches `^(\d+)-.+` and files for that issue now live in `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, warn the branch looks stale and ask whether to switch back before continuing. If the branch is neither default nor an issue-style branch, warn and ask whether to continue. Never delete a branch from `/iflow-start`.

3. **Sweep stale current issues** (auto-safe) — Group files in `.issueflows/01-current-issues/` by `issueNN_` prefix. For every group **other than the focus issue**, move the whole group to `.issueflows/03-solved-issues/` if any of its status files contains `- [x] Done` (case-insensitive on `done`), otherwise move it to `.issueflows/02-partly-solved-issues/`. Never move the focus issue's files. Report every move.

4. **Plan precondition** — Look for `issue<N>_plan.md` in `.issueflows/01-current-issues/`.
   - **Plan present:** read it and treat it as the source of truth for scope and approach. Before writing new modules, read **`### Prior art`** under **`## Constraints`** if present (skip if absent or it says "None found").
   - **Plan missing:** do **not** hard-stop. Ask the user to choose one of:
     - **Run `/iflow-plan` now**, then continue into implementation after they confirm the plan.
     - **Proceed without a plan** — add a short `- Skipped /iflow-plan on <date>` note to `issue<N>_status.md` and continue.
     - **Abort.**

5. **Seed the status file up front** — Before writing code, create `issue<N>_status.md` under `.issueflows/01-current-issues/` (if missing) with an unchecked `- [ ] Done` checkbox and short **What's done** / **Remaining work** sections. It is a living document that should exist *during* the work, not only at `/iflow-close`.

6. **Implement** — Execute the plan (or the explicitly-acknowledged plan-less path). Prefer minimal, focused diffs. Match existing code style and tooling.

7. **Project conventions**
   - Use the project's **documented Python toolchain**, not bare `python`. Default to `uv run` (scripts, pytest, tools) and `uv add` / `uv remove` / `uv sync` for dependencies, **unless** the project documents otherwise — e.g. a conda project runs scripts and `pytest` inside the **activated conda environment** (`conda activate <env>` or `conda run -n <env> …`). Honour existing project rules over these defaults.
   - **Toolbox** — Before writing a one-off helper script, check `.issueflows/00-tools/` (start with its `README.md` index) for an existing tool. If you build something reusable during this issue, save it into `.issueflows/00-tools/` and add a one-line entry to that README's index (name, what it does, when to use it) for the next agent.
   - If `.issueflows/04-designs-and-guides/this-project.md` exists, read it for project-specific context before implementing; then skim relevant design docs under `.issueflows/04-designs-and-guides/`.
   - As you iterate, re-read and keep `issue<N>_status.md` current — move items between **What's done** and **Remaining work**, leaving `- [ ] Done` unchecked until fully resolved.

8. **Hand off** — When the implementation is ready to ship, tell the user to run `/iflow-close` (optionally with `bump`/`patch`/`minor`/`major`). Parking work mid-stream goes through `/iflow-pause`.

9. **Reporting** — Summarize what changed, what remains, and where the issue docs live. Include any branch warnings from step 2, any group moves from step 3, and whether the plan was followed or explicitly skipped.

## Constraints

- Do not invent issue text; treat `*_original.md` as a read-only source of requirements unless the user asks to edit it.
- The stale sweep in step 3 is the **only** automatic folder move `/iflow-start` performs, and it never touches the focus issue's own files.
- Never delete or force-update git branches from `/iflow-start`.
- Do not write or modify `issue<N>_plan.md` from here — changes to the plan go through `/iflow-plan`.
