---
name: iflow-close
description: >-
  Finish and land the focus issue: tests, optional version bump, changelog
  trailers, status update, commit, push, and PR. Modes: yolo (merge too),
  ops (no PR).
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — close (`/iflow-close`)

Finish and land the focus issue: tests, optional version bump, tracking updates, commit, push, PR. This skill never deletes branches; that is `/iflow-cleanup`.


**Invoke:** type `iflow close` in chat, or `/iflow-close` from the slash menu (`iflow-close` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).


## Input tokens

| Token | Effect |
|---|---|
| `bump` / `patch` / `minor` / `major` / `stable` / `alpha` / `beta` / `rc` / `post` / `dev` | Version bump (step 2). Natural language works too; ask once if unclear; never auto-pick `major`. |
| `nohistory` / `skip history` | Skip the changelog trailers (step 3). |
| `log "..."` / `note "..."` | Use this text as the changelog bullet. |
| `stay` / `stay on branch` / `don't switch` | Stay on the issue branch after the PR step. |
| `draft` | Open or keep a draft PR; skips the `yolo` merge. |
| `yolo` | Hands-off: decide the changelog without asking, merge the PR, switch back and pull. Used by `/iflow-run yolo`. |
| `ops` / `nopr` / `no-pr` | No PR. Read `ops.md` in this skill folder and follow it **instead of** the steps below. Cannot combine with `yolo` or `draft`; stop and ask if combined. |

## Side files (read only when the step needs them)

| File | When |
|---|---|
| `version.md` | Step 2: a bump was requested, or a `publish` label is on the issue. |
| `changelog.md` | Step 3: composing the changelog trailers. |
| `sync.md` | Step 6: replaying the branch onto the default branch. |
| `merge.md` | Step 8a: the `yolo` token is present. |
| `ci.md` | You need to list or wait on CI with `gh`. |
| `ops.md` | The `ops` / `nopr` / `no-pr` token is present. |

## Steps

1. **Sanity check.** Run the project test suite (e.g. `uv run pytest`) and any checks the repo relies on.
 **Essential tests:** run `pytest -m essential` (via the project's
 documented runner) as the required local sanity gate; *remind* that the full
 suite belongs on schedule/release CI when dual workflows exist (see
 `.issueflows/04-designs-and-guides/essential-tests.md`). If the project
 has no essential CI yet, still run essential locally and note the gap. Never
 skip a failing essential suite without explicit user agreement. If the project uses ruff, run `ruff check --fix` and `ruff format` through the project's runner before committing. Skim the diff and avoid bundling unrelated changes. Record any design decision from this issue under `.issueflows/04-designs-and-guides/`. After a large structural change, when `graphify-out/` exists, *suggest* `/iflow-status graph`.

1a. **Essential tests review.**

### Essential tests review (`essential_tests = true`)

Marker: `@pytest.mark.essential`. Contract:
`.issueflows/04-designs-and-guides/essential-tests.md`. Registry:
`.issueflows/04-designs-and-guides/test-registry.md`.

1. Confirm `[tool.pytest.ini_options]` (or `pytest.ini`) registers marker
   `essential`; if missing, add it (or ask) before marking tests.
2. List tests **added or changed by this issue** only (diff / status). For each:
   recommend mark vs leave unmarked; update the registry row; get confirm before
   editing many files.
3. Do **not** reclassify the whole suite here — that is `/iflow-status doctor`.


2. **Version bump (optional).** When a bump was requested or the issue carries a `publish` label, read `version.md` and follow it. Run the bump from the project root after step 1 and before the commit.

3. **Changelog trailers.** Unless `nohistory`, read `changelog.md` and put `Changelog`, `Changelog-Date`, and `Changelog-Id` trailers at the end of the commit message. **Never edit or stage `HISTORY.md` on the issue branch.** Do not ask for confirmation. Do this even when an early draft PR exists. Never offer a changelog update after close has finished or after merge.

4. **Issue tracking.** Update `issue<N>_status.md` (what is done, what remains). Tick `- [x] Done` only when fully resolved. Then move the `issue<N>_*` group to `.issueflows/03-solved-issues/` (done) or `.issueflows/02-partly-solved-issues/` (not done).

5. **Commit.** Check `git status`. If any change is not relevant to this issue, name it and ask whether to include it. Stage intentionally (include `pyproject.toml` / `uv.lock` after a bump). Write the message in full sentences: what changed and why.

6. **Sync with the default branch.** Run `issue-flow agent sync-branch --json`. It replays the branch onto `origin/<default>` and resolves additive bookkeeping conflicts. On exit 1, report its `notes` and **stop**. Read `sync.md` for stacked branches or when the CLI is missing.

7. **Push.** Push to `origin`. When step 6 rewrote the branch (`needs_force_push: true`), use `git push --force-with-lease`. Never a bare `--force`; never against the default branch.

8. **Pull request.** Always pass `--repo <owner/repo>`.
   - Run `gh pr list --repo <owner/repo> --head <branch> --state open --json number,url,isDraft` first. Update an existing PR (including an early draft) instead of opening a second one.
   - Else `gh pr create` (`--draft` with the `draft` token). The body explains the change, how to test it, and links the issue (`Closes #N`).
   - When the PR is a draft and the user did not pass `draft`, run `gh pr ready <number> --repo <owner/repo>`.
   - Report a one-shot `gh pr checks <number> --repo <owner/repo>` snapshot. Offer `issue-flow agent pr-ready <number> --watch` when the user wants to wait; do not run it unasked.
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



8a. **Merge (`yolo` only).** Read `merge.md` and follow it. Without `yolo`, merging is the user's decision.

9. **Switch back.** Unless `stay` was passed, run `issue-flow agent switchback --json` after the PR step (after the merge with `yolo`). It refuses on a dirty tree, switches home to the default branch, and runs `git pull --ff-only`. In a linked worktree (`in_worktree: true`) it skips the switch; pull from home with `-C <home>`. On exit 1, report its notes and stop.

If `git pull --ff-only` fails on default (or home default is ahead of origin), run `issue-flow agent default-sync --json` (classify-only) and print ahead/behind, the unique commits, and its `action`: `even` / `ff_only` → retry the pull; `report_ahead` → show the commits, never silent-push; `tracking_pr` / `replay_tracking` → move the commits to a chore branch and open a small PR; `stop_product` → stop, the user decides. Never rebase default, force-push default, or push default to skip CI.


9a. **Remove the issue worktree.** Skip when: no linked worktree for `<N>` (`inplace`); input included `stay`; the PR is still `draft`; a `yolo` merge failed or was only queued via `--auto`; the worktree is dirty (report paths and leave the folder — never `--force`).
   - Run from **home**: `issue-flow agent worktree-remove <N> -C <home> --json`.
   - This project has `auto_remove_worktree = true`: remove without asking.
   - Never delete the issue branch here. Continue from **home**.


10. **After review.** Without `yolo`, address feedback, push, and merge when approved and checks are green.

11. **Output.** Commit, push result, PR URL, final branch, worktree removal, merge result (with `yolo`), and the next step. When `epic_session.md` exists, hint `/iflow` for the next epic child.

## Constraints

- Do not skip failing tests without the user's explicit agreement.
- Never delete branches here. Never `gh pr merge --admin`, never skip CI, never force-push anything but the issue branch (`--force-with-lease`).
- Only additive bookkeeping conflicts are resolved automatically (step 6). Every other conflict stops the flow.
- The `ops` token never opens a PR.
