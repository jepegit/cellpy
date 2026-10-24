# Issue — create one normal issue (`/iflow-issue`)

Read this to **author and create one well-specified GitHub issue** (a single deliverable), then optionally set up the normal lifecycle (branch + `/iflow-pick` → hand off to `/iflow-plan`).

## Input

- **free text** — seed for the issue title and/or short description (e.g. `iflow issue add dry-run flag to doctor`).
- **epic-anchor mode** — set by the router for `epic <free text>`: title prefixed with `Epic:`, and apply the `epic` label when it exists (`gh label list`). After create, offer to draft the staged plan (`epic.md`) for the new number.
- **(nothing)** — ask for a one-line intent before drafting.

## Instructions

### Phase 1 — draft and create

1. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch + clean/dirty tree (`git status --porcelain`).
2. **Parse input.** In epic-anchor mode the text after `epic` is the seed.
3. **Draft title + body.** Propose a title and a body with this light structure (not a full `/iflow-plan`):
   - **Problem / context**
   - **Spec** (what to change)
   - **Acceptance criteria**
   - **Out of scope** (optional; omit the heading when empty)
   Refine with the user until they confirm the text. If the draft is clearly over-large for one PR, **offer** `/iflow-issue split` (flat parent/child) or `/iflow-issue epic` (staged) — do **not** auto-create sub-issues.
4. **Create (confirm first).** Show the final title and body (and, in epic-anchor mode, the planned `epic` label when present). On yes: `gh issue create --repo <owner/repo>` (add `--label epic` only when epic-anchor mode is on **and** `gh label list` shows `epic`). Capture number `N`. Set the chat tab title to `Issue <N> <short title>`. Optional labels/milestones other than the epic-anchor label: only if the user asked for them in this turn — do not invent them.

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


### Phase 2 — optional lifecycle setup

5. **Offer branch + init (default path).** Ask whether to start work now. On yes (require a clean tree; if dirty, stop and ask to commit/stash):
   - Slug from the title (kebab-case); branch `<N>-<slug>`. Confirm a non-obvious slug.

**Worktree-first start (default).** After the dirty-tree gate and slug confirm — unless the user passed `inplace` / `no worktree`, or ops chose stay-on-current/default:

1. Home stays on the **default** branch. `git fetch --prune`. Do **not** `git switch -c` on home.
2. Run `issue-flow agent default-sync --json -C <home>`. If `action` is `even` or `ff_only`, `git pull --ff-only`. If home is ahead or diverged, **print** the classification and **still continue** — starting work must not wait for home to be ff-able.
3. `issue-flow agent worktree-add <N> --slug <slug> -C <home> --json` — use the `path` it returns: `../<repo>-<N>` by default, or `<worktrees_dir>/<repo>-<N>` when a common worktrees folder is configured (`location` in the payload says which rule applied; a `location_note` explains a fallback). Starts from fetched `origin/<default>`, not local default HEAD. On error, **stop and ask**; never silently fall back to inplace.
4. `issue-flow agent open-workspace <path> --json` (print-only). Tell the user the worktree path. Do **not** ask to open a window.
5. Capture the issue (`capture.md` in the `iflow-pick` skill) and run later plan/build/close with `-C <worktree-path>`. Continue the session in that folder.
6. Token `inplace` / `no worktree` keeps legacy `git switch -c <N>-<slug>` on home. Token `worktree` is a no-op when `worktree_first` is already on.


   - On a non-default **home** branch → **ask** whether to FF/switch home to default first (required for worktree-add) or use `inplace` from current.
   - Capture `<N>` by following `capture.md` in the `iflow-pick` skill folder, with `-C <worktree>` (or home if `inplace`). Do not duplicate its fetch/archive logic.
   - **Ask** whether to continue with `/iflow-plan`. Do **not** auto-run it.
6. **Create-only.** If the user declines Phase 2, stop after create. Remind them they can start it later with `/iflow-pick <N>`.

## Constraints

- Never create a GitHub issue or branch without explicit confirmation; show what will be created first.
- GitHub only (`gh`); GitLab is not supported.
- Branch off the detected default (or the current branch when chosen); never force-push or delete branches from this skill.
- Do not write `issue<N>_plan.md` here.
