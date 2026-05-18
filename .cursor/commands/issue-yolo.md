# All-in-one flow for small, low-risk issues

Chains `/issue-init` → `/issue-plan` → `/issue-start` → `/issue-close` in a single run, with safeguards. Use this **only** for minor fixes, docs tweaks, and similar low-risk changes where a full plan/review loop would be overkill.

For anything non-trivial, use the individual commands so you get confirmation checkpoints.

The chained commands still consult and update `.issueflows/04-designs-and-guides/` (design docs, decisions, good practices) — but if a yolo run uncovers a decision worth recording, that alone is usually a signal the change is **not** small enough for `/issue-yolo`: consider aborting and running the commands individually.

## Input

Same as `/issue-init` (issue number, URL, or empty to infer from the branch). Optional extra tokens are forwarded to the downstream commands:

- `bump` / `patch` / `minor` / `major` — forwarded to `/issue-close` for the version bump.
- `nohistory` / `skip history` — forwarded to `/issue-close` to skip the `HISTORY.md` update step.
- `log "..."` / `note "..."` — forwarded to `/issue-close` as the `HISTORY.md` bullet summary.
- `draft` — open a draft PR in `/issue-close`.
- Free-form notes — used as the plan/commit context.

## Preflight (abort on any failure)

1. **Refuse on default branch.** If the current branch is `main` / `master` / the detected default, **stop** and tell the user to create or switch to an issue branch first. Do not offer to create one silently from `/issue-yolo`.

2. **Refuse with dirty unrelated changes.** Run `git status --porcelain`. If anything is uncommitted that is **not** obviously related to the target issue (ask the user if it's not clear), **stop**. Suggest committing / stashing first.

3. **Tests must pass up front.** Run `uv run pytest` (or the repo's documented test command). If any test fails, **stop** before the chain starts. Yolo never ships on a broken baseline.

4. **Single consolidated confirm.** Present the full planned chain explicitly, for example:

   ```
   /issue-yolo will run, without further prompts:

     1. /issue-init 123
     2. /issue-plan         (auto-confirmed, short plan)
     3. /issue-start        (implement directly)
     4. /issue-close patch  (tests, bump, commit, push, PR)

   Target branch: 123-fix-typo
   Repo: owner/repo

   Proceed? [y/N]
   ```

   Require an explicit yes. Any other input aborts.

## Chain

Once the preflight has passed and the user confirmed:

1. **`/issue-init`** — capture the issue (or skip if the `*_original.md` already exists for the focus issue).

2. **`/issue-plan`** — auto-confirmed. Write a **short** `issue<N>_plan.md` (Goal + Approach + Files to touch + Test strategy). Do not stop for user confirmation; the consolidated confirm above already covered it. If the scope check reveals the change is not actually small (touches many unrelated files, mixes refactors, etc.), **abort** the yolo chain and tell the user to run the commands individually.

3. **`/issue-start`** — implement the plan. No additional plan-mode prompt.

4. **Tests again.** Re-run `uv run pytest`. If anything fails, **stop**. Do not commit, push, or open a PR. Tell the user what failed and point at the work in progress.

5. **`/issue-close`** — run the full close flow (optional version bump if the user passed `bump`/`patch`/`minor`/`major`, issue-folder update, commit, push, PR). Do **not** chain `/issue-cleanup` automatically — the PR has not merged yet.

## Post-run

- Leave the user on the issue branch with the PR URL.
- Remind them to re-run `/issue-cleanup` once the PR is merged.

## Output

Report, in order:
- preflight results (default-branch check, dirty tree check, initial test run)
- which downstream commands ran and where they stopped (if any)
- final state: commit SHA, PR URL (or reason the chain aborted)

## Constraints

- Do not override any of the downstream commands' own constraints (no `-D` in `/issue-cleanup`, etc.). `/issue-yolo` is a chain, not a free pass.
- If **any** downstream step requires a decision (unrelated changes in `git status`, ambiguous version bump, merge conflict, failed test), **stop** and hand back to the user. Never paper over a prompt just because the chain is running.
- Never run `/issue-cleanup` from `/issue-yolo`. Branch deletion always needs the user to see the merged PR first.
