---
name: iflow-cleanup
description: >-
  Post-merge branch hygiene: switch to the default branch and delete merged
  local branches under one consolidated confirm. Optional GitHub remote audit
  via trailing "include GitHub". Never -D / --force.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — issue cleanup (`/iflow-cleanup`)

Follow this skill to **run post-merge branch hygiene** after a PR has been merged (typically the PR opened by `/iflow-close`).


**Invoke:** type `iflow cleanup` in chat, or `/iflow-cleanup` from the slash menu (`iflow-cleanup` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



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

## Input

Optional free-form text after the command:

- **No extra text** — Phase A only: detect the current branch's PR, clean that up, plus any other local branches already merged into the default.
- A **branch name** — Phase A targets that branch instead of the current one (e.g. `/iflow-cleanup 42-fix-login`).
- **GitHub remote audit** — if the trailing text contains (case-insensitive) `include github`, `include gh`, `with github`, or a standalone `github` token, also run **Phase B** after Phase A: classify `origin/*` remotes, summarise unique work, and optionally delete deletable remotes and/or file a findings issue (second confirm).

## Instructions

1. **Detect the default branch.** Prefer `gh repo view --repo <owner/repo> --json defaultBranchRef -q .defaultBranchRef.name`, else `git -C <project_root> symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`.

2. **Identify the target branch.** If the user named a branch after `/iflow-cleanup` (ignoring GitHub-audit tokens), use it. Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 4 (folder sweep only) for Phase A.

3. **Check PR / merge state.** Prefer `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`. If `gh` is unavailable, approximate with `git fetch --prune` then `git cherry origin/<default> <branch>` (all commits marked `-` means squash-merged).
   - **If not merged:** remind the user that the working copy is still on the issue branch; suggest `git switch <default>` before unrelated work and re-run `/iflow-cleanup` after the PR merges. **Stop Phase A.** Do not delete anything locally. If a GitHub-audit token was present, you may still offer Phase B alone (remote audit does not require the issue branch to be merged).
   - **If merged:** continue Phase A.

4. **Consolidated confirm (Phase A — local)** — one yes/no prompt listing every action:
   - `git switch <default>`
   - `git pull --ff-only`
   - `git fetch --prune`
   - Every local branch whose tip is already reachable from `origin/<default>` (include squash-merges via `git cherry`). List them explicitly before running `git branch -d <branch>` for each. Never use `-D`; if `-d` refuses, report the branch and move on.
   - **Planned release tag (tag-derived projects only).** When `/iflow-close` planned a tag it did not create — check the focus issue's status file and the newest `HISTORY.md` release section for a version whose tag is missing from `git tag -l` — include creating it here: `git tag <planned>` then `git push origin <planned>` (or `gh release create <planned> --generate-notes`). Run it **after** the pull so the tag lands on the merged squash commit.

5. **Optional folder sweep** (safe; no destructive git). In `.issueflows/01-current-issues/`, for each `issue<N>_*` group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`. Leave groups without a checked `Done` in place — routing them to `.issueflows/02-partly-solved-issues/` is `/iflow-pause`'s job.

6. **Epic stage gate (offer only).** If the just-merged issue belongs to an epic — its number appears in a `- Published: #<N>` line of an `epic<M>_plan.md` under `.issueflows/05-epics/` — check whether that closed the stage: run `issue-flow agent epic-status <M> --json` and see if the issue's stage now has no open issues left. If the stage just completed, **offer** (do not do automatically) to (a) post a short stage-summary comment on the epic anchor issue and (b) run `/iflow-epic <M> publish` to publish the next stage. Both are the user's explicit call — never auto-publish or auto-comment.

7. **Phase B — GitHub remote audit** (only when an Input GitHub-audit token was present). Prefer the CLI fast path; fall back to manual `git`/`gh` when the CLI is missing.
   - **CLI:** `issue-flow agent branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Payload buckets: `deletable`, `unique_work`, `skipped`.
   - **Manual fallback:** `git fetch --prune`; list `refs/remotes/origin/*` (skip `HEAD` and the default); for each tip run `git cherry origin/<default> origin/<branch>` (`+` = unique); `git log --oneline origin/<default>..origin/<branch>` (cap ~20) + `git diff --shortstat`; `gh pr list --repo <owner/repo> --state all --head <branch> --json number,title,state,url,mergedAt`. Treat open-PR heads as unique work (never deletable). Protected branches (when `gh api …/branches/<name>` reports `protected: true`) go to skipped.
   - **Report** the three buckets. For unique-work branches, summarise commit subjects (and open PR titles/URLs) in prose for the user.
   - **Second consolidated confirm** (never folded into Phase A's yes): list every proposed action, then ask once:
     - Optional: for each **deletable** name, `git push origin --delete <branch>` (or `gh api -X DELETE repos/<owner>/<repo>/git/refs/heads/<branch>`). Never `--force`. Never delete the default. On push failure (e.g. protection), report and continue.
     - Optional: create a findings issue with `gh issue create --repo <owner/repo>` after showing the draft title/body (deletable list + unique-work summaries). Suggested title: `chore: remote branch audit (<YYYY-MM-DD>)`. Create only on yes.
   - Phase B is **read-only until that second confirm**. Declining leaves remotes untouched.

8. **Report.** Summarize: default branch, PR/merge status, Phase A commands/branches deleted or skipped, folder sweep, epic stage-gate offer, and (when run) Phase B bucket counts, remote deletes, findings issue URL or "skipped". If `issue-flow agent resolve --json` reports `sibling_roots`, list them and remind the user that **each scaffolded repo needs its own `/iflow-cleanup`** — do not loop automatically in this step.

## Constraints

- Never use `git branch -D` or `git push --force`.
- Never delete the default branch (local or remote).
- Remote deletes and findings-issue creation require the **Phase B** confirm; Phase A's yes must not imply them.
- If anything is ambiguous (detached HEAD, multiple remotes, missing tracking info), report and stop rather than guess.
- Do not open or update PRs. Do not bump version fields — pyproject bumps belong to `/iflow-close`. The only version action allowed here is creating a release tag that `/iflow-close` **planned** (tag-derived strategy), inside the Phase A consolidated confirm.
- Do **not** offer to update `HISTORY.md` / CHANGELOG here — that belongs in `/iflow-close` before the PR.
