# Close step 3 — changelog trailers

Read this to decide the changelog bullet as part of `/iflow-close`. It never runs on its own schedule; it is driven by the "update HISTORY" step, and does not run when the user passed `nohistory` / `skip history`. The bullet lands in the close commit as trailers. **Do not edit** `HISTORY.md` on the issue branch — `issue-flow changelog release` writes that file later, on the default branch, when a version is cut.

## Preconditions

1. Compose the bullet even if `HISTORY.md` is missing at the project root. Never create the file from this skill.
2. Do **not** open or edit `HISTORY.md`. A version bump in step 2 of `/iflow-close` does **not** promote or append a heading.

## Inputs from `/iflow-close`

| From | Used for |
|---|---|
| Issue number `N` | Reference suffix on the bullet, e.g. `(#42)`. |
| Issue title (from `.issueflows/01-current-issues/issue<N>_original.md`) | Default bullet summary. |
| `log "..."` / `note "..."` input token | Override the bullet summary verbatim. |
| Today's date | `Changelog-Date` (`YYYY-MM-DD`). A sort key inside the next release, not a filing date. |

## Trailers

1. Compose the bullet sentence:

   ```text
   <summary>. (#<N>)
   ```

   Summary = `log "..."` override if provided, else the issue title with sentence case, trailing period trimmed before the `.` we add. Do not prefix the trailer value with `- `.

2. Generate `Changelog-Id` with 12 lowercase hex characters (one per bullet; do not invent it by hand and do not reuse the issue number or the commit SHA):

   ```bash
   uv run python -c "import secrets; print(secrets.token_hex(6))"
   ```

3. Hand this block back to `/iflow-close` so it is the end of the commit message body (use `git commit -F`, not a shell heredoc):

   ```text
   Changelog: <summary>. (#<N>)
   Changelog-Date: YYYY-MM-DD
   Changelog-Id: <12 hex>
   ```

   The same issue may emit several blocks (several ids). `nohistory` emits none.
4. Put the trailers in the commit without a confirm prompt (`confirm_changelog_update` is false) so the bullet is in the PR commit. Still report the text.

5. Do this **even when a draft PR already exists** from `/iflow-build` early PR — the trailers must land in the close commit that updates that PR. **Never** propose a changelog update after close has finished or after merge.

`HISTORY.md` is rebuilt only by `issue-flow changelog release <version>` on the default branch. That command prepends one `## [<version>] - <date>` section from the trailers (and, the first time, folds any leftover `## [Unreleased]` bullets). It does not run during `/iflow-close`.

## Conflict resolution — keep both bullet sets

Repos that still have `## [Unreleased]` can still conflict when two PRs edit it. That repair path stays. New closes do not add bullets there, so they do not create that conflict. When an unrelated PR lands on the default branch while this issue is in flight and both sides did append, git cannot merge it. That is bookkeeping, not a design decision, so it has exactly one documented answer — used by `/iflow-close`'s sync step and by `/iflow-run cycle`'s parallel coordinator.

**Resolvable only when all of these hold:**

1. the conflicted file is `HISTORY.md` and **nothing else** is conflicted;
2. every conflict region sits under `## [Unreleased]`;
3. both sides contain **only** list items (plus blank / wrapped continuation lines).

**Resolution:** keep **all** bullets. The bullets already on the default branch keep their positions; this issue's bullet goes **last**. Byte-identical bullets collapse to one.

**Refuse and stop** (a human decides) when the conflict touches any other file, an existing bullet was edited or deleted, a heading was renamed, or a `## [Unreleased]` section was promoted to a release section on either side.

**Fast path:** `issue-flow agent sync-branch --json` applies exactly this rule during the rebase in `/iflow-close` and aborts on anything else. Prefer it over hand-editing conflict markers.

**Same rule, other bookkeeping files.** The keep-both resolver also covers `.issueflows/04-designs-and-guides/*.md` and `issue<N>_status.md` files — additive **bullets and table rows** only. `sync-branch` picks the resolver per path (payload `resolvers`); product code is never touched.

## Staging

When `/iflow-close` reaches its commit step:

- Do **not** stage `HISTORY.md`. The trailers are in the commit message, not in the diff.
- If a version bump also ran, stage `pyproject.toml` (and `uv.lock` if it changed) without promoting `HISTORY.md`.

## Constraints

- Do **not** read or write `HISTORY.md` from this skill. Compose the trailers only.
- `defer_changelog` no longer selects a write path. Do not record `### Deferred changelog` and do not run `issue-flow agent apply-changelog` from close or cleanup. That command remains for a status file that already has the old block.
- Never create `HISTORY.md` from scratch.
- **Timing:** this skill runs only from `/iflow-close` step 3 (before commit / push / PR update), including when a draft was opened earlier via early PR. **Never** propose updating `HISTORY.md` after close has finished or after merge.

- The bullet's `(#<N>)` suffix is the focus issue's GitHub number.
