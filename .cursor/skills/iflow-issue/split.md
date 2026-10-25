# Issue — split an over-large issue (`/iflow-issue split`)

Read this to **cut one over-large GitHub issue into 2–5 flat child issues**, link each as a GitHub native sub-issue of the parent, and optionally start the first child.

**Coexists** with:

- **`/iflow-issue`** — creates *one* new issue. Use split when an *existing* issue is too big for one PR.
- **`/iflow-issue epic`** — staged multi-issue work with `Depends on` and publish. If the cut needs stages or explicit deps, **stop** and point at `/iflow-issue epic` (create an anchor with `/iflow-issue epic` when missing). Do not create children here.

## Input

- **`<N>`** — parent issue number to split.
- **(nothing)** — use the focus issue in `.issueflows/01-current-issues/`, else the issue-style branch `^\d+-.+`. Ambiguous → ask.

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
4. **Size gate.** If the cut wants sequential stages or explicit `Depends on` lines → **stop**. Recommend `/iflow-issue epic`. Do not create.

### Phase 2 — create and link

5. **Consolidated confirm** (normal prose, never shortened). One prompt covering: parent `#N` stays **open** as the tracker; each listed child title will be created; each will be linked as a GitHub native sub-issue; a `- [ ] #<M>` task-list block will be appended on the parent under `## Sub-issues`. No yes → stop.
6. **Create + link (idempotent).** For each unpublished child:
   1. `gh issue create --repo <owner/repo>` (labels/milestones only if the user asked this turn). Capture number `M`.

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

8. **Ask** whether to start the first child: `/iflow-pick`-style branch `<M>-<slug>` off the default (clean-tree gate) + `/iflow-pick` for `M`. Do **not** auto-run `/iflow-plan` or `/iflow-build`. Declining leaves the children as open GitHub issues for a later pick.

## Constraints

- Never create a GitHub issue or sub-issue link without the consolidated confirm; show titles and bodies first.
- GitHub only (`gh` / `gh api`); GitLab is not supported.
- Parent stays open. Do not convert the parent into an epic plan file.
- Do not merge with `/iflow-issue epic` publish or `/iflow-issue` — different intents.
- Do not park generated children under `02-partly-solved-issues/`.
