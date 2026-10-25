# Close step 8a — merge the PR (`yolo` token)

Never `--delete-branch`; branch deletion stays in `/iflow-cleanup`.

1. If the user passed `draft`, **skip the merge** and say so.
2. Try `gh pr merge <number> --squash` immediately (repos with no required checks stay fast).
3. If GitHub refuses for pending/required checks, run `gh pr checks <number> --repo <owner/repo> --watch --fail-fast` under a hard wall-clock budget of **15 minutes** (`checks_watch_minutes`).
4. Watch succeeds within the cap → retry `gh pr merge <number> --squash`.
5. Watch fails (red) → stop hands-off behaviour, leave the PR open, report the failing check links.
6. Cap elapses while still pending, or checks never register → last resort `gh pr merge <number> --squash --auto`; report the merge as queued and continue. If `--auto` fails too, stop and leave the PR open.
7. **Refused as conflicted** (`CONFLICTING` / `DIRTY`): re-run `issue-flow agent sync-branch --json` (see `sync.md`). If it resolved the conflict, `git push --force-with-lease`, re-watch checks under the same budget, and retry the merge **once**. If the sync exits 1 or the retry is refused, stop and leave the PR open with the reason. Never `--admin`, never skip checks.
8. **Already merged** (someone landed it while checks ran) → success. Continue with step 9.

## After the merge (step 9 with `yolo`)

Pull the default branch from **home** (not the issue worktree). Then:

- **Planned release tag** (tag-derived version strategy only): if step 2 planned a tag, create it on the merge commit with `git tag <planned>` and `git push origin <planned>`. When the merge was only queued via `--auto`, leave the tag to `/iflow-cleanup` and say so.
- **Publish label release**: if step 2 recorded a publish label or planned version, run `gh release create "v<version>" --generate-notes` with the version that landed on default. Skip when the release already exists. When the merge was only queued, leave it to `/iflow-cleanup`.

Do not chain `/iflow-cleanup` automatically.
