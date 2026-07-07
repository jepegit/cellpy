---
name: iflow-pick
description: >-
  Front door: choose the next issue, create the issue branch, and run
  /iflow-init.
disable-model-invocation: true
---

# issue-flow — pick next issue (`/iflow-pick`)

Follow this skill to help the user **choose what to work on next** (parked work first, else ranked open GitHub issues) and get set up to start.

Do **not** use this skill from `/iflow`, `/iflow-start`, or `/iflow-close`. `/iflow-pick` is explicit-only because it creates GitHub issues and branches.

## Input

- **(nothing)** — survey candidates and ask which to pick.
- **`fix`** — create a **new** general-fixes GitHub issue (a fresh one every time) and use it.
- **a hint** (milestone / label / topic) — bias the candidate ranking.


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

### Phase 1 — choose the issue

1. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch + clean/dirty tree (`git status --porcelain`).
2. **`fix` shortcut.** If the user passed `fix`, skip selection and go to step 5 (create a new general-fixes issue), then Phase 2.
3. **Source candidates** (precedence):
   - **Parked work first** — list `issue<n>_*` groups in `.issueflows/02-partly-solved-issues/` as the primary candidates (already-started work to finish first).
   - **Else GitHub** — `gh issue list --state open --json number,title,labels,milestone,updatedAt` (add `--repo owner/repo` if ambiguous). Drop issues already captured under `01-current-issues/`, `02-partly-solved-issues/`, or `03-solved-issues/`.
4. **Rank and present.** Rank by **milestone** (nearest/active, honour any hint) + **labels** (match recent work / hint) + **topical similarity** to recently solved issues (skim `.issueflows/03-solved-issues/` and recent branch names). Show a numbered shortlist (~3–7) with number, title, labels, milestone, and **ask the user to confirm** the pick or override. Never pick silently.
5. **Create a `fix` issue (only when requested).** Use `gh issue create` (e.g. `chore: general fixes`), confirm title/body first, capture the new number. A fresh issue is created each time — never reuse an existing open general-fixes issue.
6. **Over-large issue (note only).** If the chosen issue is too big for one PR, **mention** that breaking it into sub-issues is possible and tracked as a follow-up (Phase B of issue #63). Do **not** auto-create sub-issues here.

7. **Label-driven yolo flow.** If the chosen issue carries the **`yolo`** label (case-insensitive), announce it and fold `/iflow-yolo`'s consolidated confirm into the pick confirmation (one prompt: branch + full `init → plan → start → close yolo` chain). On yes, run Phase 2 then follow the `iflow-yolo` skill **instead of** the Phase 3 handoff — its preflight still applies, but do not re-ask its confirm. Configurable via `label_flows` / `yolo_label` under `[issueflow]` in `.issueflows/config.toml` (re-run `issue-flow update` after changing).



### Phase 2 — create the branch

1. **Require a clean tree** (`git status --porcelain`). If dirty, **stop** and ask the user to commit/stash.
2. **Branch off the default** — switch to default, fast-forward, then `git switch -c <N>-<short-slug>` (GitHub numeric convention). Confirm a non-obvious slug.
3. **Run `/iflow-init`** for the now-known `<N>` by following the `iflow-init` skill. Do not duplicate its fetch/archive logic.

### Phase 3 — hand off

1. **Ask** whether to continue with `/iflow-plan`. Do not auto-run it.

2. **Exception:** when the `yolo`-label routing was confirmed in Phase 1, skip this handoff — the `iflow-yolo` chain (which includes `/iflow-init`) takes over after the branch is created.


## Constraints

- Off-path: never auto-dispatch from `/iflow`, `/iflow-start`, or `/iflow-close`.
- Never create a GitHub issue or branch without explicit confirmation; show what will be created first.
- Branch off the detected default; never force-push or delete branches from this skill.
- **Phase B is out of scope**: no automated sub-issue creation or sibling parking under `02-partly-solved-issues/`. Only mention the option.
- Delegate issue capture to `/iflow-init` rather than re-implementing it.
