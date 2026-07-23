---
name: iflow-issue
description: >-
  Create one well-specified normal GitHub issue, then optionally branch and
  run /iflow-init into the standard lifecycle.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — create a normal issue (`/iflow-issue`)

Follow this skill to **author and create one well-specified GitHub issue** (a single deliverable), then optionally set up the normal lifecycle (branch + `/iflow-init` → hand off to `/iflow-plan`).

Do **not** use this skill from `/iflow`, `/iflow-build`, or `/iflow-close`. `/iflow-issue` is explicit-only because it creates GitHub issues (and optionally branches).

**Coexists** with:

- **`/iflow-pick fix`** — one-shot *general-fixes chore bucket* into plan/start.
- **`/iflow-fix`** — iterative small-fixes *session* that stays in a loop.
- **`/iflow-epic`** — staged multi-issue work; use `/iflow-issue` first when the epic **anchor** does not exist yet.

## Input

- **free text** — seed for the issue title and/or short description (e.g. `iflow issue add dry-run flag to doctor`).
- **`epic`** (alone or as a leading token, e.g. `epic Large rewrite`) — epic-anchor mode: title prefixed with `Epic:`, and apply the `epic` label when it exists (`gh label list`).
- **(nothing)** — ask for a one-line intent before drafting.


**Invoke:** type `iflow issue` in chat, or `/iflow-issue` from the slash menu (`iflow-issue` also works).




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
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

### Phase 1 — draft and create

1. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch + clean/dirty tree (`git status --porcelain`).
2. **Parse input.** If the first token is `epic` (case-insensitive), enable epic-anchor mode and treat the remainder as the seed. Bare `epic` with no remainder → ask for the epic intent.
3. **Draft title + body.** Propose a title and a body with this light structure (not a full `/iflow-plan`):
   - **Problem / context**
   - **Spec** (what to change)
   - **Acceptance criteria**
   - **Out of scope** (optional; omit the heading when empty)
   Refine with the user until they confirm the text. If the draft is clearly over-large for one PR, **mention** splitting via `/iflow-epic` — do **not** auto-create sub-issues.
4. **Create (confirm first).** Show the final title and body (and, in epic-anchor mode, the planned `epic` label when present). On yes: `gh issue create --repo <owner/repo>` (add `--label epic` only when epic-anchor mode is on **and** `gh label list` shows `epic`). Capture number `N`. Set the chat tab title to `Issue <N> <short title>`. Optional labels/milestones other than the epic-anchor label: only if the user asked for them in this turn — do not invent them.

### Phase 2 — optional lifecycle setup

5. **Offer branch + init (default path).** Ask whether to start work now. On yes (require a clean tree; if dirty, stop and ask to commit/stash):
   - Slug from the title (kebab-case); branch `<N>-<slug>`. Confirm a non-obvious slug.
   - On the default branch → `git switch -c <N>-<slug>`. On a non-default branch → **ask** whether to branch from current or default.
   - Run `/iflow-init` (or the `iflow-init` skill) for `<N>`. Do not duplicate its fetch/archive logic.
   - **Ask** whether to continue with `/iflow-plan`. Do **not** auto-run it.
6. **Create-only.** If the user declines Phase 2, stop after create. Remind them they can pick it up later with `/iflow-pick` / `/iflow-init`.

## Constraints

- Off-path: never auto-dispatch from `/iflow`, `/iflow-build`, or `/iflow-close`.
- Never create a GitHub issue or branch without explicit confirmation; show what will be created first.
- GitHub only (`gh`); GitLab is not supported.
- Branch off the detected default (or the current branch when chosen); never force-push or delete branches from this skill.
- Delegate local capture to `/iflow-init`; do not write `issue<N>_plan.md` here.
- Do not merge with `/iflow-fix` or `/iflow-pick fix` — different intents.
