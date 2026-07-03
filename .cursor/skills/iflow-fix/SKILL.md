---
name: iflow-fix
description: >-
  Run the /iflow-fix interactive session: set up one long-lived branch + GitHub
  issue for a stream of small iterative fixes, then loop — each fix gets a short
  plan, is implemented only on confirmation, and is recorded as a dated bullet in
  issue<N>_status.md. Finish with /iflow-close. Off-path: never auto-dispatched by
  /iflow. Always creates a GitHub issue (gh); GitLab is not supported.
disable-model-invocation: true
---

# issue-flow — interactive iterative-fix session (`/iflow-fix`)

Follow this skill when the user wants an **ongoing working session** for many small fixes on one branch, rather than a single well-defined deliverable.

## When to use

- The user runs `/iflow-fix`, mentions "iterative fixes", "small fixes session", or "let's just fix things on a branch".
- They have a bucket of little improvements (small bugs, typos, chores, polish) to knock out together and land via one PR.

Do **not** use this skill from `/iflow`, `/iflow-start`, or `/iflow-close`. `/iflow-fix` is explicit-only because it creates GitHub issues and branches and drives an open-ended loop. While a session is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`.

It **coexists** with `/iflow-pick fix`: that command is a one-shot setup back into the normal `/iflow-plan` → `/iflow-start` flow, whereas `/iflow-fix` stays and runs the loop until close.

## Input

- **a name** (e.g. `polish-cli-output`) — used for the issue title and branch slug.
- **(nothing)** — default the slug to `iterative-small-fixes` (made unique via the new issue number).
- **a description** during an active session — run the next fix in the loop.

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
