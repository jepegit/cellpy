# Issue — iterative-fix session (`/iflow-issue fix`)

Read this for an **ongoing working session** of many small fixes (small bugs, typos, chores, polish) on one branch, landed via one PR — rather than a single well-defined deliverable.

It **coexists** with `/iflow-pick fix` (one-shot general-fixes setup into `/iflow-plan` → `/iflow-build`) and `/iflow-issue` (one well-specified normal issue). `/iflow-issue fix` stays and runs the loop until close.

## Input

- **a name** (e.g. `polish-cli-output`) — used for the issue title and branch slug.
- **(nothing)** — default the slug to `iterative-small-fixes` (made unique via the new issue number).
- **a description** during an active session — run the next fix in the loop.

## Instructions

### Phase 1 — set up the session (once)

1. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch + clean/dirty tree (`git status --porcelain`); if dirty with unrelated changes, ask to commit/stash first.
2. **Resolve the session name.** Baked `fix_auto_name = false`: use an explicit invoke name when given; otherwise default to `iterative-small-fixes`. If the invoke text is free-form (not already a slug) and you would invent a better name, **ask once** whether to use your proposed slug or keep the default — then proceed to create confirm.
3. **Create the GitHub issue (always, with confirmation).** Show the chosen title (e.g. `Iterative fixes: <name>`, or `Iterative small fixes`) and a body noting it is an interactive `/iflow-issue fix` session whose individual fixes are recorded in the status markdown and landed together via `/iflow-close`. Create it with `gh issue create` (add `--repo owner/repo` if ambiguous). Capture the returned number `N`. A fresh issue is created each time. Set the chat tab title to `Issue <N> <session name>`.

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

4. **Create the worktree (with confirmation).** Slug from the resolved name (kebab-case; default `iterative-small-fixes`); branch name `<N>-<slug>`. Require a clean tree.

**Worktree-first start (default).** After the dirty-tree gate and slug confirm — unless the user passed `inplace` / `no worktree`, or ops chose stay-on-current/default:

1. Home stays on the **default** branch. `git fetch --prune`. Do **not** `git switch -c` on home.
2. Run `issue-flow agent default-sync --json -C <home>`. If `action` is `even` or `ff_only`, `git pull --ff-only`. If home is ahead or diverged, **print** the classification and **still continue** — starting work must not wait for home to be ff-able.
3. `issue-flow agent worktree-add <N> --slug <slug> -C <home> --json` — use the `path` it returns: `../<repo>-<N>` by default, or `<worktrees_dir>/<repo>-<N>` when a common worktrees folder is configured (`location` in the payload says which rule applied; a `location_note` explains a fallback). Starts from fetched `origin/<default>`, not local default HEAD. On error, **stop and ask**; never silently fall back to inplace.
4. `issue-flow agent open-workspace <path> --json` (print-only). Tell the user the worktree path. Do **not** ask to open a window.
5. Capture the issue (`capture.md` in the `iflow-pick` skill) and run later plan/build/close with `-C <worktree-path>`. Continue the session in that folder.
6. Token `inplace` / `no worktree` keeps legacy `git switch -c <N>-<slug>` on home. Token `worktree` is a no-op when `worktree_first` is already on.


   On a non-default home branch → **ask** whether to FF/switch home to default first or use `inplace`.
5. **Capture locally.** Follow `capture.md` in the `iflow-pick` skill for `<N>`: write `.issueflows/01-current-issues/issue<N>_original.md` and run its archive sweep. Do not duplicate that logic.
6. **Seed the status file.** Create `.issueflows/01-current-issues/issue<N>_status.md` with a short header (interactive `/iflow-issue fix` session), an unchecked `- [ ] Done`, and an empty **`## Iterative fixes log`** section.

### Phase 2 — the fix loop (repeat)

For each proposed fix:

1. **Restate** the fix in one line.
2. **Short plan** — a few lines (intent + file(s)); never a full `issue<N>_plan.md`.
3. **Ask to proceed** — implement **only on confirmation**; otherwise revise or drop.
4. **Implement** the confirmed fix, focused on that one change.
5. **Record** it: append a dated bullet to **`## Iterative fixes log`** in `issue<N>_status.md`. Offer proactively; always update when asked.

If a "fix" is really a substantial feature or sprawls across unrelated areas, say so and suggest filing it as its own issue via `/iflow-issue` (then `/iflow-plan` → `/iflow-build`).

### Phase 3 — finish

When the user is done fixing, follow `.cursor/skills/iflow-close/SKILL.md` to land the session (close keeps its own confirms).

## Constraints

- Never create a GitHub issue or branch without explicit confirmation; show what will be created first.
- GitHub only (`gh`); GitLab is not supported.
- Branch off the detected default (or the current branch when chosen); never force-push or delete branches from this skill.
- Keep `- [ ] Done` unchecked during the session; `/iflow-close` flips it.
- Delegate local capture to `/iflow-pick` and finishing to `/iflow-close`; one fix per loop iteration, implemented only on explicit confirmation.
