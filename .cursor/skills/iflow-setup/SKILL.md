---
name: iflow-setup
description: >-
  Guide a new user from an empty folder or an unprepared existing project to
  a working issue-flow setup: uv project, git repo, GitHub remote, and scaffold.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — guided project setup (`/iflow-setup`)

Follow this skill to get a project **ready to use issue-flow** — for someone who may never have driven an agentic workflow before.

It covers both entry paths from a standing start:

- **New project** — an empty (or nearly empty) folder that needs a Python project, a git repo, and a GitHub remote.
- **Existing project** — real code already, but some piece is missing (no remote, `gh` not authenticated, no issue-flow scaffold).

This is **not** the issue-capture step. Capturing a GitHub issue into `.issueflows/01-current-issues/` is `/iflow-capture`; picking what to work on is `/iflow-pick`. `/iflow-init` only cold-starts the harness.


**Invoke:** type `iflow setup` in chat, or `/iflow-setup` from the slash menu (`iflow-setup` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.


## Input

- **(nothing)** — inspect the current directory and guide from there.
- **`new`** — treat this as a brand-new project (skip the new-vs-existing question).
- **`existing`** — treat this as an existing project.
- **`check`** — report readiness only; change nothing, run nothing, ask nothing.

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

5. **Choose a starting mode when scaffolding.** For someone new to agentic coding, recommend **`issue-flow init --mode novice`**: it installs the linear lifecycle plus the safety nets (`/iflow`, `/iflow-setup`, `/iflow-pick`, `/iflow-init`, `/iflow-capture`, `/iflow-issue`, `/iflow-plan`, `/iflow-build`, `/iflow-pause`, `/iflow-close`, `/iflow-cleanup`, `/iflow-status`, `/iflow-doctor`) and leaves out the hands-off and batch machinery, and it seeds settings that ask before each step instead of chaining. Mention that `issue-flow init --mode standard` adds everything later — switching mode is just a re-run.

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
- **Off-path.** Never auto-dispatch this skill from `/iflow`, `/iflow-plan`, or `/iflow-build`; the user invokes it. It never captures an issue, creates a branch, or opens a PR — that is `/iflow-capture` onward.
- **Plain language.** Assume the user has not read the workflow doc. Explain what each command will do to their machine or their GitHub account before asking.
