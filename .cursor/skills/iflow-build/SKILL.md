---
name: iflow-build
description: >-
  Implement the confirmed plan for the focus issue using the project's
  documented conventions.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — issue build (`/iflow-build`)

Follow this skill to **begin implementation** from issue notes and project rules. Planning itself lives in `/iflow-plan`; this skill is implementation-only. Stay aligned with `.cursor/rules/issueflow-rules.mdc` when present.


**Invoke:** type `iflow build` in chat, or `/iflow-build` from the slash menu (`iflow-build` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).

## Early PR tokens (command input)

- **`early`** or **`pr`** → open a draft PR during this build after the first successful push (force on for this run).
- **`noearly`** → skip early PR for this run even when `[issueflow].early_pr` is true.
- Precedence: trailing token > baked `early_pr` (currently **False**) > default `false`.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, use
> `issue-flow agent preflight` for the branch status preflight (step 2) and
> `issue-flow agent sweep --except <N>` for the stale sweep (step 3; add
> `--dry-run` to preview). The CLI is optional: if it is missing or errors,
> fall back to the manual instructions below. (`issue-flow` is only present
> when the user installed it, e.g. `uv tool install issue-flow`.)

1. **Select the issue** — Read `.issueflows/01-current-issues/`. If there is no `*_original.md` (or multiple ambiguous groups), **stop** and ask which issue to use.

2. **Branch status preflight** (non-destructive) — Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind counts vs `origin/<default>`. If on the default branch, propose creating an issue branch (`git switch -c <N>-<short-slug>`); ask before running. If the current branch matches `^(\d+)-.+` and files for that issue now live in `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, warn the branch looks stale and ask whether to switch back before continuing. If the branch is neither default nor an issue-style branch, warn and ask whether to continue. Never delete a branch from `/iflow-build`.

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
   - **Ruff (when present).** If the project uses ruff (`[tool.ruff]` in `pyproject.toml`, ruff in dev dependencies, or `.issueflows/04-designs-and-guides/python-quality-tools.md` exists), run auto-fix lint after substantive code changes — e.g. `uv run ruff check --fix …` then `uv run ruff format …` (match paths to what the project documents).
   - **Toolbox** — Before writing a one-off helper script, check `.issueflows/00-tools/` (start with its `README.md` index) for an existing tool. If you build something reusable during this issue, save it into `.issueflows/00-tools/` and add a one-line entry to that README's index (name, what it does, when to use it) for the next agent.
   - If `.issueflows/04-designs-and-guides/this-project.md` exists, read it for project-specific context before implementing; then skim relevant design docs under `.issueflows/04-designs-and-guides/`.
   - **Knowledge graph (optional).** If `graphify-out/GRAPH_REPORT.md` exists, skim it before grepping — god-nodes and surprising connections often point at the files you'll touch. If structure changed materially since the last build, *suggest* `/iflow-status graph` (do not run it automatically). If `graphify-out/` is absent, ignore this bullet.
   - As you iterate, re-read and keep `issue<N>_status.md` current — move items between **What's done** and **Remaining work**, leaving `- [ ] Done` unchecked until fully resolved.

8. **Early pull request (optional)** — After the **first successful push** of the issue branch (or when the branch already has a remote tip and no open PR), decide whether to open a PR now using the Early PR tokens above. When early PR is on:
   - Require an issue-style branch matching `^\d+-.+` (never the default branch) with a remote tracking ref.
   - Always pass `--repo <owner/repo>`. **List before create:** `gh pr list --repo <owner/repo> --head <branch> --state open --json number,url,title,isDraft`. If an open PR exists, note it and skip creating a second one.
   - Otherwise create a **draft**: `gh pr create --draft --repo <owner/repo> …` with a WIP-friendly body and **`Refs #N`** (not `Closes #N` yet).

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

   - Record `PR: <url> (#<n>, draft)` in `issue<N>_status.md`.
   - Do **not** write `HISTORY.md` here — `/iflow-close` owns the changelog bullet (even while a draft PR exists).

9. **Hand off** — When the implementation is ready to ship: follow `.cursor/skills/iflow-close/SKILL.md` immediately (forward any trailing `bump`/`patch`/`minor`/`major` / `stay` / `nohistory` / `draft` tokens). Close keeps its own confirms — this flag only skips the "please run `/iflow-close`" pause. If work is **not** ready (failing tests, open remaining work, user asked to park), do **not** chain — use `/iflow-pause` or stop and report. Parking work mid-stream goes through `/iflow-pause`.

10. **Reporting** — Summarize what changed, what remains, and where the issue docs live. Include any branch warnings from step 2, any group moves from step 3, whether an early PR was opened/reused, and whether the plan was followed or explicitly skipped.

## Constraints

- Do not invent issue text; treat `*_original.md` as a read-only source of requirements unless the user asks to edit it.
- The stale sweep in step 3 is the **only** automatic folder move `/iflow-build` performs, and it never touches the focus issue's own files.
- Never delete or force-update git branches from `/iflow-build`.
- Do not write or modify `issue<N>_plan.md` from here — changes to the plan go through `/iflow-plan`.
