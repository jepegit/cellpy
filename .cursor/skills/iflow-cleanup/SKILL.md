---
name: iflow-cleanup
description: >-
  Post-merge branch hygiene: switch to the default branch and delete landed
  local branches (reachable via -d; squash-landed via -D behind its own
  confirm). Optional GitHub remote audit (include github). Modes: all (workspace),
  prs (refresh DIRTY PRs), archive (condense solved issues). Never --force.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — cleanup (`/iflow-cleanup`)

Post-merge branch hygiene after a PR has landed.


**Invoke:** type `iflow cleanup` in chat, or `/iflow-cleanup` from the slash menu (`iflow-cleanup` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).

## Input

| Trailing text | Effect |
|---|---|
| nothing | Phase A: the current branch's PR plus every other local branch already landed on the default. |
| a branch name | Phase A targets that branch instead of the current one. |
| `include github` / `with github` / `github` | Also run Phase B, the remote audit (`github.md`). `no github` / `local only` skips it. |
| `self-update` / `bleeding edge` | Upgrade the tool after a successful pull. `skip self-update` / `no bleeding` skips it. |
| `ask a1` / `ask a2` | Force that phase's prompt even when its `cleanup_yes_*` knob is on. |
| `drive` / `landed` | Orchestrator token from `/iflow-run drive`: its earlier confirm already covered `-D` on landed branches, so A1/A2 run without re-asking. A2 narrows to `squash_landed`, plus `merged_pr_divergent` with no commit newer than the PR's `mergedAt`; never `unique_work` / `skipped`. A human never passes it. |
| `all` / `workspace` | Every scaffolded workspace member (step 4b, `workspace.md`). At most three confirms in total (A1, A2, Phase B). |
| `prs` | Refresh open PRs that went `DIRTY` after another merge: read `prs.md` instead of the steps below. |
| `archive` | Condense old solved issue groups: read `archive.md` instead of the steps below. |

**Ask rules.** Phase A1: ask yes/no first. Phase A2: a **separate** yes/no before any `git branch -D`. A1's yes never implies A2, and neither implies Phase B.

## Instructions

1. **Detect the default branch.** Prefer `gh repo view <owner/repo> --json defaultBranchRef -q .defaultBranchRef.name` (repo is **positional** on `gh repo view` — not `--repo`), else `git -C <project_root> symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`.

2. **Identify the target branch.** If the user named a branch after `/iflow-cleanup` (ignoring GitHub-audit / opt-out tokens), use it. Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 7 (folder sweep only) for Phase A.

3. **Check PR / merge state.** `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName` (without `gh`: `git cherry origin/<default> <branch>`, all `-` means landed). Not merged → say so, suggest re-running after the merge, and **stop Phase A** (Phase B may still run). Merged → continue.

4. **Classify the local branches.** Prefer the CLI fast path; fall back to manual `git`/`gh` when it is missing.
   - **CLI:** `issue-flow agent local-branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Buckets: `reachable`, `squash_landed`, `merged_pr_divergent`, `unique_work`, `skipped`. Every entry carries a `tip` short SHA.
   - **Manual fallback** (no CLI): read `classify.md` in this skill folder.

4b. **Workspace mode** (only with an `all` / `workspace` token): read `workspace.md` in this skill folder; it replaces steps 2–6 for every scaffolded workspace member.

5. **Consolidated confirm (Phase A1 — local)** — one yes/no prompt listing every action:
   - `git switch <default>` (home only; skip if already on default)
   - `git pull --ff-only` — if it fails, **stop** A1 steps that assume default is current (release tag, self-update) and recover via `default-sync` (see below).
   - **Self-update (when enabled).** After a successful pull, on **home**: `issue-flow agent self-update --json -C <home>`. Report a skip or failure; never roll back branch deletes.
   - `git fetch --prune`
   - `issue-flow agent worktree-list --json`, then `issue-flow agent worktree-remove <path>` for each linked worktree on a **`reachable`** branch, **before** deleting the branch. Never remove a worktree whose branch is `unique_work`.
   - `git branch -d <branch>` for each **`reachable`** branch, listed explicitly by name first. If `-d` still refuses, report that branch and move on.
   - **Planned release.** When `/iflow-close` planned a tag or recorded a publish label (status file) and the tag or GitHub release is missing, create it **after** the pull: `gh release create "v<version>" --generate-notes`, or `git tag <planned>` + `git push origin <planned>` for tag-only projects. Never invent a release for an ordinary bump.

If `git pull --ff-only` fails on default (or home default is ahead of origin), run `issue-flow agent default-sync --json` (classify-only) and print ahead/behind, the unique commits, and its `action`: `even` / `ff_only` → retry the pull; `report_ahead` → show the commits, never silent-push; `tracking_pr` / `replay_tracking` → move the commits to a chore branch and open a small PR; `stop_product` → stop, the user decides. Never rebase default, force-push default, or push default to skip CI.


6. **Force-delete confirm (Phase A2 — only when `squash_landed` or `merged_pr_divergent` is non-empty).** A **separate** yes/no; A1's yes never implies it. With `drive` / `landed`, the orchestrator's confirm replaces the prompt (narrowed scope; still print every `<name> <tip>`).
   - Explain that a squash merge leaves no reachable tip, so these need `git branch -D`, which skips git's safety check.
   - List `squash_landed` as `<name>  <tip>` with the evidence, and `merged_pr_divergent` **separately** with tip, merged PR link, and unique-commit subjects for the user to eyeball.
   - Print the recovery line: `git branch <name> <tip>` undoes a deletion.
   - On yes, `worktree-remove` linked clean worktrees on these branches, then try `git branch -d <name>` and fall back to `-D` only when it refuses. Report each `<name> <tip>` and the flag used. On no, leave everything in place.
   - **Never** include a `unique_work` or `skipped` branch, even when asked to "delete them all"; point at its unique commits instead.

7. **Optional folder sweep** (safe; no destructive git). In `.issueflows/01-current-issues/`, for each `issue<N>_*` group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`. Leave groups without a checked `Done` in place — routing them to `.issueflows/02-partly-solved-issues/` is `/iflow-pause`'s job.

8. **Epic stage gate (offer only).** If the merged issue is a `- Published: #<N>` child in an `epic<M>_plan.md` and `issue-flow agent epic-status <M> --json` shows its stage has no open issues left, **offer** a stage-summary comment on the anchor and `/iflow-issue epic <M> publish` for the next stage. Never do either automatically.

9. **Phase B — GitHub remote audit** (only when enabled per the Input rule): read `github.md` in this skill folder and follow it. It is read-only until its own confirm.

10. **Report.** Default branch, PR state, A1 commands and `-d` deletions, A2 `-D` deletions with tip SHAs, branches kept as unique work, folder sweep, epic offer, self-update result, and Phase B results when run. In workspace mode, report each member. Otherwise, when `issue-flow agent resolve --json` lists `sibling_roots`, remind the user that each repo needs its own cleanup; do not loop unless invoked with `all`. If other open PRs still show `DIRTY` / CONFLICTING (often `HISTORY.md`), **offer** `/iflow-cleanup prs` — do not auto-run it.

## Constraints

- Never `git push --force`; never rebase, force-push, or push the default branch; never delete the default branch.
- `git branch -D` only for `squash_landed` / `merged_pr_divergent`, only after the A2 confirm (or `cleanup_yes_a2`, or the `drive` / `landed` token), and only with tip SHAs reported. Never `-D` unique work, an unclassified branch, or the current branch. A `-d` refusal in A1 is reported, never a licence to force.
- `issue-flow workspace cleanup` classifies only: `--apply` only after the workspace A1 yes, `--apply --yes-delete-squash-landed` only after the A2 yes.
- Remote deletes and the findings issue need the Phase B confirm.
- Ambiguous state (detached HEAD, several remotes, missing tracking info) → report and stop.
- No PRs, no version bumps, no `HISTORY.md` edits here. The only version action is the release `/iflow-close` planned (step 5).
