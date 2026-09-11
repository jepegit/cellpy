---
name: iflow-cleanup
description: >-
  Post-merge branch hygiene: switch to the default branch and delete landed
  local branches (reachable via -d; squash-landed via -D behind its own
  confirm). Optional GitHub remote audit via trailing "include GitHub" or
  baked cleanup_include_github. Never --force, never deletes unique work.
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
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Input

Optional free-form text after the command:

- **No extra text** — Phase A: detect the current branch's PR, clean that up, plus any other local branches already merged into the default. Phase B stays off unless a GitHub-audit token is present.
- A **branch name** — Phase A targets that branch instead of the current one (e.g. `/iflow-cleanup 42-fix-login`).
- **GitHub remote audit (opt-in tokens)** — trailing text containing (case-insensitive) `include github`, `include gh`, `with github`, or a standalone `github` token enables **Phase B** after Phase A.
- **GitHub remote audit (opt-out tokens)** — trailing `no github`, `local only`, or `local-only` (case-insensitive) **skips Phase B** even when `cleanup_include_github` is baked true.

**Phase B enable rule:** run Phase B when (`cleanup_include_github` is baked true **or** an opt-in GitHub token is present) **and** no opt-out token is present.

## Instructions

1. **Detect the default branch.** Prefer `gh repo view <owner/repo> --json defaultBranchRef -q .defaultBranchRef.name` (repo is **positional** on `gh repo view` — not `--repo`), else `git -C <project_root> symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`.

2. **Identify the target branch.** If the user named a branch after `/iflow-cleanup` (ignoring GitHub-audit / opt-out tokens), use it. Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 7 (folder sweep only) for Phase A.

3. **Check PR / merge state.** Prefer `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`. If `gh` is unavailable, approximate with `git fetch --prune` then `git cherry origin/<default> <branch>` (all commits marked `-` means squash-merged).
   - **If not merged:** remind the user that the working copy is still on the issue branch; suggest `git switch <default>` before unrelated work and re-run `/iflow-cleanup` after the PR merges. **Stop Phase A.** Do not delete anything locally. If Phase B is enabled (see Input), you may still offer Phase B alone (remote audit does not require the issue branch to be merged).
   - **If merged:** continue Phase A.

4. **Classify the local branches.** Prefer the CLI fast path; fall back to manual `git`/`gh` when it is missing.
   - **CLI:** `issue-flow agent local-branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Buckets: `reachable`, `squash_landed`, `merged_pr_divergent`, `unique_work`, `skipped`. Every entry carries a `tip` short SHA.
   - **Manual fallback**, per local branch (skipping the current branch and the default):
     1. `git merge-base --is-ancestor <branch> origin/<default>` — exit 0 → **`reachable`**.
     2. Else `git cherry origin/<default> <branch>` — no `+` lines → **`squash_landed`** (every commit has an equivalent patch upstream).
     3. Else `gh pr list --repo <owner/repo> --state all --head <branch> --json number,state,mergedAt,url`. With a merged PR, compare `git log --no-merges --format=%cI origin/<default>..<branch>` against its `mergedAt`: no commit **newer** than the merge → **`merged_pr_divergent`** (the squash rewrote these commits); any newer commit → **`unique_work`** (real work pushed after the PR merged).
     4. Anything else → **`unique_work`**.
     5. Record `git rev-parse --short <branch>` for every branch you might delete.

   > **Why the extra buckets:** this project merges PRs with **squash**, which lands a *new* commit on the default branch. A squash-merged branch tip is therefore never an ancestor of the default, so `git branch -d` refuses it forever — `-d` alone can never prune landed branches here.

5. **Consolidated confirm (Phase A1 — local)** — one yes/no prompt listing every action:
   - `git switch <default>`
   - `git pull --ff-only`
   - `git fetch --prune`
   - `git branch -d <branch>` for each **`reachable`** branch, listed explicitly by name first. If `-d` still refuses, report that branch and move on.
   - **Planned release tag (tag-derived projects only).** When `/iflow-close` planned a tag it did not create — check the focus issue's status file and the newest `HISTORY.md` release section for a version whose tag is missing from `git tag -l` — include creating it here: `git tag <planned>` then `git push origin <planned>` (or `gh release create <planned> --generate-notes`). Run it **after** the pull so the tag lands on the merged squash commit.

6. **Force-delete confirm (Phase A2 — only when `squash_landed` or `merged_pr_divergent` is non-empty).** A **separate** yes/no prompt; Phase A1's yes never implies it. Skip this step entirely when both buckets are empty.
   - State plainly that these branches need `git branch -D` because a squash merge leaves no reachable tip, and that `-D` skips git's own safety check.
   - List **`squash_landed`** as `<name>  <tip>` with the evidence (every commit patch-equivalent to the default; merged PR number when known).
   - List **`merged_pr_divergent`** *separately*, each with its `<tip>`, merged PR link, and unique-commit subjects — these are landed per GitHub but their tips differ, so the user should eyeball the subjects before agreeing.
   - Show the recovery line: any deletion is undone with `git branch <name> <tip>`.
   - On yes, try `git branch -d <name>` first and only fall back to `git branch -D <name>` when it refuses — `-d` also accepts a branch merged into its own upstream, so it sometimes still works while the remote-tracking ref survives. Report each `<name> <tip>` and which flag was used, so the SHAs stay in the transcript. On no, leave every branch in place.
   - **Never** include a `unique_work` or `skipped` branch in this prompt, even if the user asks to "delete them all" — point at the branch's unique commits instead and let them delete it by hand.

7. **Optional folder sweep** (safe; no destructive git). In `.issueflows/01-current-issues/`, for each `issue<N>_*` group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`. Leave groups without a checked `Done` in place — routing them to `.issueflows/02-partly-solved-issues/` is `/iflow-pause`'s job.

8. **Epic stage gate (offer only).** If the just-merged issue belongs to an epic — its number appears in a `- Published: #<N>` line of an `epic<M>_plan.md` under `.issueflows/05-epics/` — check whether that closed the stage: run `issue-flow agent epic-status <M> --json` and see if the issue's stage now has no open issues left. If the stage just completed, **offer** (do not do automatically) to (a) post a short stage-summary comment on the epic anchor issue and (b) run `/iflow-epic <M> publish` to publish the next stage. Both are the user's explicit call — never auto-publish or auto-comment.

9. **Phase B — GitHub remote audit** (only when Phase B is enabled per the Input enable rule). Prefer the CLI fast path; fall back to manual `git`/`gh` when the CLI is missing.
   - **CLI:** `issue-flow agent branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Payload buckets: `deletable`, `unique_work`, `skipped`.
   - **Manual fallback:** `git fetch --prune`; list `refs/remotes/origin/*` (skip `HEAD` and the default); for each tip run `git cherry origin/<default> origin/<branch>` (`+` = unique); `git log --oneline origin/<default>..origin/<branch>` (cap ~20) + `git diff --shortstat`; `gh pr list --repo <owner/repo> --state all --head <branch> --json number,title,state,url,mergedAt`. Treat open-PR heads as unique work (never deletable). Protected branches (when `gh api …/branches/<name>` reports `protected: true`) go to skipped.
   - **Report** the three buckets. For unique-work branches, summarise commit subjects (and open PR titles/URLs) in prose for the user.
   - **Second consolidated confirm** (never folded into Phase A's yes): list every proposed action, then ask once:
     - Optional: for each **deletable** name, `git push origin --delete <branch>` (or `gh api -X DELETE repos/<owner>/<repo>/git/refs/heads/<branch>`). Never `--force`. Never delete the default. On push failure (e.g. protection), report and continue.
     - Optional: create a findings issue with `gh issue create --repo <owner/repo>` after showing the draft title/body (deletable list + unique-work summaries). Suggested title: `chore: remote branch audit (<YYYY-MM-DD>)`. Create only on yes.
   - Phase B is **read-only until that second confirm**. Declining leaves remotes untouched.

10. **Report.** Summarize: default branch, PR/merge status, Phase A1 commands and `-d` deletions, Phase A2 `-D` deletions with their tip SHAs (or "declined" / "none offered"), branches left alone as unique work, folder sweep, epic stage-gate offer, and (when run) Phase B bucket counts, remote deletes, findings issue URL or "skipped". If `issue-flow agent resolve --json` reports `sibling_roots`, list them and remind the user that **each scaffolded repo needs its own `/iflow-cleanup`** — do not loop automatically in this step.

## Constraints

- Never use `git push --force`.
- `git branch -D` is allowed **only** for `squash_landed` / `merged_pr_divergent` branches, **only** after the Phase A2 confirm, and **only** with their tip SHAs reported. Never `-D` a branch holding unique work, a branch you could not classify, or the current branch. In Phase A1, a `-d` refusal is reported and left alone — it is never a licence to force-delete.
- Never delete the default branch (local or remote).
- Remote deletes and findings-issue creation require the **Phase B** confirm; the Phase A1 and A2 yeses must not imply them (nor each other).
- If anything is ambiguous (detached HEAD, multiple remotes, missing tracking info), report and stop rather than guess.
- Do not open or update PRs. Do not bump version fields — pyproject bumps belong to `/iflow-close`. The only version action allowed here is creating a release tag that `/iflow-close` **planned** (tag-derived strategy), inside the Phase A consolidated confirm.
- Do **not** offer to update `HISTORY.md` / CHANGELOG here — that belongs in `/iflow-close` before the PR.
