---
name: iflow-split
description: >-
  Split one over-large GitHub issue into linked child issues (native
  sub-issues), then optionally start the first child.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — split an over-large issue (`/iflow-split`)

Follow this skill to **cut one over-large GitHub issue into 2–5 flat child issues**, link each as a GitHub native sub-issue of the parent, and optionally start the first child.

Do **not** use this skill from `/iflow`, `/iflow-build`, or `/iflow-close`. `/iflow-split` is explicit-only because it creates GitHub issues and parent/child links.

**Coexists** with:

- **`/iflow-issue`** — creates *one* new issue. Use split when an *existing* issue is too big for one PR.
- **`/iflow-epic`** — staged multi-issue work with `Depends on` and publish. If the cut needs stages or explicit deps, **stop** and point at `/iflow-epic` (create an anchor with `/iflow-issue epic` when missing). Do not create children here.

## Input

- **`<N>`** — parent issue number to split.
- **(nothing)** — use the focus issue in `.issueflows/01-current-issues/`, else the issue-style branch `^\d+-.+`. Ambiguous → ask.


**Invoke:** type `iflow split` in chat, or `/iflow-split` from the slash menu (`iflow-split` also works).




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

## Instructions

### Phase 1 — draft children

1. **Resolve parent `N`.** Trailing number, else the single `issue<n>_original.md` in `.issueflows/01-current-issues/`, else leading digits of a `^\d+-.+` branch. Ambiguous or missing → **stop and ask**.
2. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch + clean/dirty tree. Creating children does **not** require a clean tree; branching onto a child later does.
3. **Draft 2–5 children.** Propose titles + light bodies (not a full `/iflow-plan`):
   - **Problem / context**
   - **Spec**
   - **Acceptance criteria**
   - **Out of scope** (optional; omit the heading when empty)
   Each body **ends with** `Sub-issue of #<N>.` Refine until the user confirms the set.
4. **Size gate.** If the cut wants sequential stages or explicit `Depends on` lines → **stop**. Recommend `/iflow-epic`. Do not create.

### Phase 2 — create and link

5. **Consolidated confirm** (normal prose, never shortened). One prompt covering: parent `#N` stays **open** as the tracker; each listed child title will be created; each will be linked as a GitHub native sub-issue; a `- [ ] #<M>` task-list block will be appended on the parent under `## Sub-issues`. No yes → stop.
6. **Create + link (idempotent).** For each unpublished child:
   1. `gh issue create --repo <owner/repo>` (labels/milestones only if the user asked this turn). Capture number `M`.
   2. Link as a native sub-issue. Prefer the CLI fast path:
      `issue-flow agent sub-issue-add <N> <M> -C <project_root> [--repo owner/repo] --json`
      Fields: `linked`, `skipped` (already a child), `error`. On CLI missing or `error` set, fall back to the REST recipe below — then if that also fails (404 / permission / plan), **keep the created issue** and rely on the parent task list.
   3. **REST recipe** (single source — other skills point here; do not copy):
      `sub_issue_id` is the child's numeric **database id**, not the issue number. `gh api -f` stringifies and **422s**. Send JSON:

      ```bash
      CHILD_ID=$(gh api repos/<owner>/<repo>/issues/<M> --jq .id)
      echo "{\"sub_issue_id\": ${CHILD_ID}}" | \
        gh api repos/<owner>/<repo>/issues/<N>/sub_issues -X POST --input -
      ```

      Re-runs: `GET repos/<owner>/<repo>/issues/<N>/sub_issues` (or the CLI `skipped` field) — skip children already linked.
   4. Append `- [ ] #<M>` under a `## Sub-issues` heading on the parent (`gh issue edit <N> --body-file`, append/patch only — never rewrite the user's own body). Task list is the fallback when the sub-issue API is unavailable.
   5. Record created numbers in the parent's local status file (create it if missing) so a later re-run can skip them.
7. **Local parent.** If `issue<N>_*` is in `.issueflows/01-current-issues/`, move the whole group to `.issueflows/02-partly-solved-issues/`. Status checkbox stays `- [ ] Done`. Do **not** close the GitHub parent. Do **not** write `issue<M>_*` groups for children.

### Phase 3 — optional handoff

8. **Ask** whether to start the first child: `/iflow-pick`-style branch `<M>-<slug>` off the default (clean-tree gate) + `/iflow-capture` for `M`. Do **not** auto-run `/iflow-plan` or `/iflow-build`. Declining leaves the children as open GitHub issues for a later pick.

## Constraints

- Off-path: never auto-dispatch from `/iflow`, `/iflow-build`, or `/iflow-close`.
- Never create a GitHub issue or sub-issue link without the consolidated confirm; show titles and bodies first.
- GitHub only (`gh` / `gh api`); GitLab is not supported.
- Parent stays open. Do not convert the parent into an epic plan file.
- Do not merge with `/iflow-epic` publish or `/iflow-issue` — different intents.
- Do not park generated children under `02-partly-solved-issues/`.
