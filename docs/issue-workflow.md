# issue-flow command reference

This project uses **Cursor**. Each command is an Agent Skill under `.cursor/skills/<name>/SKILL.md`. Issue state lives in `.issueflows/`. Background: [Concepts](https://issue-flow.readthedocs.io/en/latest/concepts/). Full manual: [https://issue-flow.readthedocs.io/en/latest](https://issue-flow.readthedocs.io/en/latest/).

## How to invoke

Type `iflow <step> [args]` in chat (letters and spaces only, handy on keyboards without an easy `/`), or `/iflow-<step>` from the slash menu. `iflow-<step>` also works. Plain `iflow` runs the dispatcher, which works out the next step for the focus issue.

Merged commands take a **mode** as their first word, for example `iflow run cycle label:yolo` or `iflow issue epic 42 publish`. Each mode's instructions live in a separate file inside the skill folder, so an agent reads only what the mode needs.


## Commands

| Command | Modes | What it does | Installed in |
|---|---|---|---|
| `/iflow` | — | Dispatcher: run the next of capture / plan / build / close. | standard, novice, simple |
| `/iflow-setup` | `harness`, `check` | Get a project ready (uv, git, GitHub, scaffold). | standard, novice, simple |
| `/iflow-pick` | `<N>`, `capture`, `fix`, `label:<L>` | Choose an issue, branch, and capture it. | standard, novice, simple |
| `/iflow-plan` | — | Write the plan and stop for approval. | standard, novice, simple |
| `/iflow-build` | — | Implement the approved plan. | standard, novice, simple |
| `/iflow-pause` | — | Park unfinished work with resume notes. | standard, novice, simple |
| `/iflow-close` | `yolo`, `ops`, `draft`, `bump` | Tests, bump, changelog trailers, commit, push, PR. | standard, novice |
| `/iflow-cleanup` | `all`, `github`, `prs`, `archive` | After merge: default branch, pull, delete landed branches. | standard, novice |
| `/iflow-run` | `yolo`, `cycle`, `auto`, `drive` | Hands-off runs under one up-front confirm. | standard |
| `/iflow-issue` | `fix`, `epic`, `split`, `review` | Create and shape GitHub issues. | standard, novice |
| `/iflow-status` | `doctor`, `git`, `graph` | Read-only overview of every issue. | standard, novice, simple |


## The core loop

1. **`/iflow-pick`** chooses the next issue (parked work first, then ranked open GitHub issues), creates the branch in a sibling worktree, and captures the issue as `issue<N>_original.md`. `/iflow-pick <N>` skips the choice.
2. **`/iflow-plan`** writes `issue<N>_plan.md` and **stops for your approval** before any code changes.
3. **`/iflow-build`** implements the approved plan and keeps `issue<N>_status.md` current.
4. **`/iflow-close`** runs the tests, optionally bumps the version, adds changelog trailers to the commit (it never edits `HISTORY.md` on the branch), commits, pushes, and opens the PR. `close yolo` also merges; `close ops` finishes without a PR.
5. **`/iflow-cleanup`**, after the merge, switches to the default branch, pulls, and deletes landed local branches behind explicit confirms.

`/iflow` runs whichever of capture / plan / build / close is next. It never runs any other command for you. `/iflow-pause` parks unfinished work in `02-partly-solved-issues/`.

## Where the agent stops to ask

- Before creating a GitHub issue, label, branch, or PR.
- After drafting a plan (`/iflow-plan`).
- Before deleting anything: local branches (`-d` and, separately, `-D` for squash-landed branches), remote branches, archived issue files.
- Hands-off modes (`/iflow-run …`) ask **once** up front and then stop only when a human decision is needed.

## Status file contract

`issue<N>_status.md` always carries one checkbox line: `- [x] Done` when the issue is fully resolved, `- [ ] Done` otherwise. Capture, build, and close route issue files to `03-solved-issues/` or `02-partly-solved-issues/` by that line.

## Files issue-flow owns

`issue-flow update` rewrites the skills, the `AGENTS.md` managed block, and this page from the installed package, and removes files that a newer version retired. It never touches your issue markdown, `04-designs-and-guides/`, or `00-tools/README.md`. Each `SKILL.md` carries `issue-flow-version` in its frontmatter; when it differs from `issue-flow --version`, run `issue-flow update`.

Configuration knobs live in `.issueflows/config.toml` (`issue-flow config show`); see [Configuration](https://issue-flow.readthedocs.io/en/latest/configuration/).
