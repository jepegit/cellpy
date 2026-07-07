---
name: iflow-fix
description: >-
  Interactive session: one long-lived branch + GitHub issue for a stream of
  small iterative fixes, landed together via /iflow-close.
disable-model-invocation: true
---

# issue-flow — interactive iterative-fix session (`/iflow-fix`)

Follow this skill for an **ongoing working session** of many small fixes (small bugs, typos, chores, polish) on one branch, landed via one PR — rather than a single well-defined deliverable.

Do **not** use this skill from `/iflow`, `/iflow-start`, or `/iflow-close`. `/iflow-fix` is explicit-only because it creates GitHub issues and branches and drives an open-ended loop. While a session is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`.

It **coexists** with `/iflow-pick fix`: that command is a one-shot setup back into the normal `/iflow-plan` → `/iflow-start` flow, whereas `/iflow-fix` stays and runs the loop until close.

## Input

- **a name** (e.g. `polish-cli-output`) — used for the issue title and branch slug.
- **(nothing)** — default the slug to `iterative-small-fixes` (made unique via the new issue number).
- **a description** during an active session — run the next fix in the loop.


### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

### Phase 1 — set up the session (once)

1. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch + clean/dirty tree (`git status --porcelain`); if dirty with unrelated changes, ask to commit/stash first.
2. **Create the GitHub issue (always, with confirmation).** Show the proposed title (e.g. `Iterative fixes: <name>`, or `Iterative small fixes`) and a body noting it is an interactive `/iflow-fix` session whose individual fixes are recorded in the status markdown and landed together via `/iflow-close`. Create it with `gh issue create` (add `--repo owner/repo` if ambiguous). Capture the returned number `N`. A fresh issue is created each time. Set the chat tab title to `Issue <N> <session name>`.
3. **Create the branch (with confirmation).** Slug from the name (kebab-case; default `iterative-small-fixes`); branch name `<N>-<slug>`. On the default branch → `git switch -c <N>-<slug>`. On a non-default branch → **ask** whether to branch from the current branch or the default. Require a clean tree before switching.
4. **Capture locally.** Delegate to the `/iflow-init` flow (or the `iflow-init` skill) for `<N>`: write `.issueflows/01-current-issues/issue<N>_original.md` and run its archive sweep. Do not duplicate that logic.
5. **Seed the status file.** Create `.issueflows/01-current-issues/issue<N>_status.md` with a short header (interactive `/iflow-fix` session), an unchecked `- [ ] Done`, and an empty **`## Iterative fixes log`** section.

### Phase 2 — the fix loop (repeat)

For each proposed fix:

1. **Restate** the fix in one line.
2. **Short plan** — a few lines (intent + file(s)); never a full `issue<N>_plan.md`.
3. **Ask to proceed** — implement **only on confirmation**; otherwise revise or drop.
4. **Implement** the confirmed fix, focused on that one change.
5. **Record** it: append a dated bullet to **`## Iterative fixes log`** in `issue<N>_status.md`. Offer proactively; always update when asked.

If a "fix" is really a substantial feature or sprawls across unrelated areas, say so and suggest handling it as its own issue via `/iflow-init` → `/iflow-plan` → `/iflow-start`.

### Phase 3 — finish

Tell the user to run **`/iflow-close`** to land the session (tests, optional bump, status update, commit, push, PR). Do not auto-run it. Remind them to run `/iflow-cleanup` after the PR merges.

## Constraints

- Off-path: never auto-dispatch from `/iflow`, `/iflow-start`, or `/iflow-close`.
- Never create a GitHub issue or branch without explicit confirmation; show what will be created first.
- GitHub only (`gh`); GitLab is not supported.
- Branch off the detected default (or the current branch when chosen); never force-push or delete branches from this skill.
- Keep `- [ ] Done` unchecked during the session; `/iflow-close` flips it.
- Delegate local capture to `/iflow-init` and finishing to `/iflow-close`; one fix per loop iteration, implemented only on explicit confirmation.
