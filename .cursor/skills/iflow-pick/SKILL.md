---
name: iflow-pick
description: >-
  Front door: choose the next issue (or take <N> directly), create the issue
  branch or worktree, and capture the issue locally as issue<N>_original.md.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — pick and capture (`/iflow-pick`)

Help the user **choose what to work on next** (parked work first, else ranked open GitHub issues), create the branch, and capture the issue under `.issueflows/01-current-issues/`.

`/iflow` dispatches here only to capture an already-known issue `<N>` (no selection, no new GitHub issue).

## Input

- **(nothing)** — survey candidates and ask which to pick.
- **`<N>`, a URL, or `owner/repo#N`** — the issue is chosen: skip Phase 1 and go to Phase 2. On an issue-style branch `<N>-<slug>` with nothing captured yet, only capture (Phase 2 step 3).
- **`capture [<N>]`** — capture only: read `capture.md` in this skill folder and follow it (no branch, no hand-off). With no `<N>`, it infers the number from the branch after asking.
- **`fix`** — create a **new** general-fixes GitHub issue (a fresh one every time) and use it.
- **`label:<L>`** — **hard filter**: only open issues carrying label `<L>` (case-insensitive). Empty → stop (“no open issues with label `<L>`”). Never auto-pick, even a single match. Batch twin: `/iflow-run cycle label:<L>`.
- **a hint** (milestone / topic) — soft-biases the ranking; only the `label:` token filters.
- **`noplan`** — skip the `auto_plan` chain for this run (ask before `/iflow-plan` even when `auto_plan` is true).


**Invoke:** type `iflow pick` in chat, or `/iflow-pick` from the slash menu (`iflow-pick` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).

## Instructions

### Phase 1 — choose the issue

1. **Preflight.** Detect the default branch, `git fetch --prune`, report the current branch and whether the tree is clean.
2. **`fix` shortcut.** If the user passed `fix`, skip selection and go to step 5 (create a new general-fixes issue), then Phase 2.
3. **Source candidates** (precedence):
   - Announce an active `label:<L>` filter in the shortlist header; apply it to every source below.
   - **Parked work first** — `issue<n>_*` groups in `.issueflows/02-partly-solved-issues/`.
   - **Active epic next** — for an epic plan under `.issueflows/05-epics/` with open issues (or one the user named), `issue-flow agent epic-status <N> --json` → `next_candidates` (open, unblocked, current stage) go to the top.
   - **Else GitHub** — `gh issue list --state open --json number,title,labels,milestone,updatedAt` (plus `--label <L>` when filtering). Drop issues already tracked locally.
4. **Rank and present.** Rank by epic membership, milestone, labels, and similarity to recently solved work. Show a numbered shortlist (~3–7: number, title, labels, milestone, epic + stage) and **ask the user to confirm**. Never pick silently, even a single entry.
5. **Create a `fix` issue (only when requested).** `gh issue create` (e.g. `chore: general fixes`) after confirming title and body. Always a fresh issue.

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

6. **Over-large issue (offer only).** If the chosen issue is too big for one PR, **mention** `/iflow-issue split` (flat parent/child) or `/iflow-issue epic` (staged) and ask. Default is proceed with the whole issue. Do **not** create children here.

7. **`ops` label.** Fold the ops lane into the pick confirm (branch or stay on default, ops work, `close ops`). On yes, run Phase 2 (default branch allowed), then follow `ops.md` in the `iflow-close` skill instead of Phase 3. With both `ops` and `yolo`, **ops wins**; say so.


8. **`yolo` label** (and not ops). Fold the yolo confirm into the pick confirm (branch + `capture → plan → build → close yolo`). On yes, run Phase 2, then follow `yolo.md` in the `iflow-run` skill instead of Phase 3: its preflight still applies; do not re-ask its confirm.


9. **Model label.** `deep` → announce the **reasoning** profile for the session; `fast` → **economy**; both → reasoning.


### Phase 2 — create the branch

1. **Working-tree gate** — Prefer `issue-flow agent preflight --json` (fields
   `clean`, `dirty_paths`, `issueflows_only`); else `git status --porcelain`
   and treat paths as issueflows-only when every path is under
   `.issueflows/`.
   - **Clean** — continue.
   - **Issueflows-only dirty** (typical after `/iflow-status doctor` repair) — one
     consolidated prompt with **commit housekeeping on the current branch** as
     the **recommended default** (message pattern:
     `chore: doctor housekeeping — archive/sweep .issueflows groups`,
     or a short edit). Alternatives: stash / abort. On commit: stage **only**
     those paths, commit, **no push**, then continue. Do not branch on top of
     the dirty tree.
   - **Mixed / code dirty** — **stop**; list non-`.issueflows/` paths;
     ask commit / stash / abort. Do **not** auto-offer “commit everything”.
2. **Issue worktree (default)** — confirm a non-obvious slug (`<N>-<short-slug>`).

**Worktree-first start (default).** After the dirty-tree gate and slug confirm — unless the user passed `inplace` / `no worktree`, or ops chose stay-on-current/default:

1. Home stays on the **default** branch. `git fetch --prune`. Do **not** `git switch -c` on home.
2. Run `issue-flow agent default-sync --json -C <home>`. If `action` is `even` or `ff_only`, `git pull --ff-only`. If home is ahead or diverged, **print** the classification and **still continue** — starting work must not wait for home to be ff-able.
3. `issue-flow agent worktree-add <N> --slug <slug> -C <home> --json` — use the `path` it returns: `../<repo>-<N>` by default, or `<worktrees_dir>/<repo>-<N>` when a common worktrees folder is configured (`location` in the payload says which rule applied; a `location_note` explains a fallback). Starts from fetched `origin/<default>`, not local default HEAD. On error, **stop and ask**; never silently fall back to inplace.
4. `issue-flow agent open-workspace <path> --json` (print-only). Tell the user the worktree path. Do **not** ask to open a window.
5. Capture the issue (`capture.md` in the `iflow-pick` skill) and run later plan/build/close with `-C <worktree-path>`. Continue the session in that folder.
6. Token `inplace` / `no worktree` keeps legacy `git switch -c <N>-<slug>` on home. Token `worktree` is a no-op when `worktree_first` is already on.


   **Ops exception:** when Phase 1 confirmed ops routing, ask whether to create the issue worktree/branch or stay on current/default; default branch is allowed (no worktree).
3. **Capture** the now-known `<N>`: read `capture.md` in this skill folder and follow it (fetch, comment triage via `comments.md`, sweep, write `issue<N>_original.md`).

### Phase 3 — hand off


1. **Chain into `/iflow-plan`** (this project has `auto_plan = true`). After Phase 2, follow the `iflow-plan` skill immediately — briefly note that `auto_plan` chained the handoff. Trailing **`noplan`** (or the user declining on confirm) skips the chain once and falls back to asking.


2. **Exception (ops):** when the `ops`-label routing was confirmed in Phase 1, skip this handoff: `ops.md` in the `iflow-close` skill takes over after capture.


3. **Exception (yolo):** when the `yolo`-label routing was confirmed in Phase 1 (and ops did not win), skip this handoff — the `iflow-run yolo` chain (which includes capture) takes over after the branch is created.


## Constraints

- Never create a GitHub issue or branch without explicit confirmation; show what will be created first.
- Branch off the detected default; never force-push or delete branches from this skill.
- Over-large splits are **offer-only**: never create child issues from this skill. Point at `/iflow-issue split` (flat) or `/iflow-issue epic` (staged).
- `auto_plan` only skips the post-init pause; pick confirm and label routing stay gated.
