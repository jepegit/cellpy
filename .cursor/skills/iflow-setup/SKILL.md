---
name: iflow-setup
description: >-
  Get a project ready for issue-flow: uv project, git repo, GitHub remote,
  scaffold. Mode harness: cold-start or refresh the scaffold (init / update /
  workspace bootstrap), also from a parent folder with no scaffold yet.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — guided project setup (`/iflow-setup`)

Follow this skill to get a project **ready to use issue-flow** — for someone who may never have driven an agentic workflow before.

It covers both entry paths from a standing start:

- **New project** — an empty (or nearly empty) folder that needs a Python project, a git repo, and a GitHub remote.
- **Existing project** — real code already, but some piece is missing (no remote, `gh` not authenticated, no issue-flow scaffold).

This is **not** the issue-capture step; that is `/iflow-pick`.

**Harness mode.** When the input is `harness`, or the user only wants to scaffold / refresh issue-flow (`issue-flow init` / `update` / `workspace bootstrap`, including from a parent folder of repos), read `harness.md` in this skill folder and follow it instead of the steps below.


**Invoke:** type `iflow setup` in chat, or `/iflow-setup` from the slash menu (`iflow-setup` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).


## Input

- **(nothing)** — inspect the current directory and guide from there.
- **`new`** — treat this as a brand-new project (skip the new-vs-existing question).
- **`existing`** — treat this as an existing project.
- **`check`** — report readiness only; change nothing, run nothing, ask nothing.
- **`harness`** — scaffold / refresh only (`harness.md`).

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent setup-status --json` for the whole readiness picture
> (tools on `PATH`, git repo / remote / commits, `gh` authentication, Python
> project, existing scaffold) plus an ordered `blockers` list where each entry
> carries the exact `fix` command. It never prompts, never mutates, and exits 0
> even when the project is not ready. If the CLI is missing, run the equivalent
> probes by hand (`git rev-parse --is-inside-work-tree`, `git remote get-url
> origin`, `gh auth status`, and file checks for `pyproject.toml` /
> `.issueflows/`).

1. **Read the state.** Run the readiness check and summarise it in a few plain lines — what is already fine, what is missing. Do not use issue-flow jargon the user has not met yet.

2. **Stop early when nothing is missing.** If the verdict is `ready`, say so, point at the next step (step 6), and stop. Never re-run setup steps on a healthy project.

3. **Decide new vs existing — and confirm it.** Infer from the readiness payload (a `pyproject.toml`, a git history, or source files means *existing*), then **state your inference and ask the user to confirm** before acting. A wrong guess here is the one that leads to `uv init` scribbling into a real project. `new` / `existing` in the input skips the question.

4. **Walk the blockers in order, one confirmation per group.** Show exactly what you intend to run before running it, and run nothing the user has not approved. Stop the walk at the first blocker you cannot clear.

   | Missing | What to do |
   |---|---|
   | `uv` | **Print** the install command (`curl -LsSf https://astral.sh/uv/install.sh \| sh`, or `winget install --id=astral-sh.uv -e` on Windows) and **stop** — you cannot install a package manager for the user. Ask them to run it and re-invoke `/iflow-setup`. |
   | Python project (new) | `uv init` (confirm the project name and whether they want a package or a script layout first), then `uv sync`. |
   | Python project (existing, no `pyproject.toml`) | Do **not** run `uv init` blind. Ask what the project uses; if it documents conda / poetry / plain venv, record that and move on — issue-flow defers to the project's toolchain. |
   | git repo | `git init`, then a first commit (`git add -A && git commit -m "Initial commit"`) once the user has seen what would be committed. Offer a `.gitignore` if none exists. |
   | `gh` | **Print** the install hints and **stop** that branch — the GitHub CLI cannot be installed for them. |
   | `gh` not authenticated | Tell the user to run **`gh auth login`** themselves in a terminal. It is an interactive browser flow: **never** try to drive it, pipe into it, or run it in the background. Wait for them to confirm, then re-check. |
   | no `origin` remote | Offer `gh repo create <name> --source=. --private --remote=origin --push`. Confirm the name and the private/public choice explicitly — this creates a repository on their GitHub account. |
   | no issue-flow scaffold | `issue-flow init` (see step 5 for the mode choice). |

5. **Choose a starting mode when scaffolding.** For someone new to agentic coding, recommend **`issue-flow init --mode novice`**: it installs the linear lifecycle plus the safety nets (`/iflow`, `/iflow-setup`, `/iflow-pick`, `/iflow-setup`, `/iflow-pick`, `/iflow-issue`, `/iflow-plan`, `/iflow-build`, `/iflow-pause`, `/iflow-close`, `/iflow-cleanup`, `/iflow-status`, `/iflow-status doctor`) and leaves out the hands-off and batch machinery, and it seeds settings that ask before each step instead of chaining. Mention that `issue-flow init --mode standard` adds everything later — switching mode is just a re-run.

6. **Hand off — never auto-dispatch.** End with the single next thing to type:
   - GitHub issues already exist → **`/iflow-pick`** (`iflow pick` in chat).
   - No issues yet → **`/iflow-issue`** to write a good first one.
   - Then the ordinary path: `/iflow-plan` → `/iflow-build` → `/iflow-close`.

7. **Report.** Summarise what was run, what the user still has to do themselves (`uv` / `gh` installs, `gh auth login`), and the one command to type next.

## Constraints

- **Confirm before every mutation.** `uv init`, `uv sync`, `git init`, the first commit, `gh repo create`, and `issue-flow init` each need explicit approval. Group related steps into one confirmation rather than asking a novice eight separate questions.
- **Never run `gh auth login` yourself**, and never install `uv` or `gh` on the user's behalf — print the command and stop.
- **Never run `uv init` in a directory that already holds a project.** When in doubt, ask.
- **`check` is read-only.** With that token, report and stop: no prompts, no commands.
- **Off-path.** Never auto-dispatch this skill from `/iflow`, `/iflow-plan`, or `/iflow-build`; the user invokes it. It never captures an issue, creates a branch, or opens a PR — that is `/iflow-pick` onward.
- **Plain language.** Assume the user has not read the workflow doc. Explain what each command will do to their machine or their GitHub account before asking.
