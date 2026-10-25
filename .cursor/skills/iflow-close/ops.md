# Close — ops / no-PR lane (`/iflow-close ops`)

Use this lane for **work that does not deserve a PR**: promote staging→production, flip a feature flag, run an external deploy checklist, tag-only release steps with no issue-branch product diff, and similar ops.

Do **not** use this for product code changes — those go through the normal lifecycle (or `/iflow-run yolo` when small).

## Instructions

1. **Resolve the issue.** Prefer the focus issue under `.issueflows/01-current-issues/`. If missing, take a number/URL from the command input and run `/iflow-pick` first. Stop if still ambiguous.

2. **Preflight.** Prefer `issue-flow agent preflight --json` (`clean` / `dirty_paths` / `issueflows_only` / branch). Else `git fetch --prune` + `git status --porcelain`.
   - **Product-code dirty** (any path outside `.issueflows/`) → **stop**. Ops path refuses silent no-PR when product files changed; use normal `/iflow-close` or stash/discard.
   - **Issueflows-only dirty** or clean → continue.
   - **Default branch OK** for ops (unlike yolo). Optional issue branch: ask create `<N>-<slug>` vs stay on current/default when not already on a matching issue branch.

3. **Execute the ops work.** Follow the issue body / acceptance criteria (external CLIs, deploy consoles, flag tools). Confirm each risky step with the user. Record what ran in `issue<N>_status.md` (dated bullets under **What's done**).

4. **Close without a PR** (below). Forward any `log "..."` text the user supplied.

## Ops close path

1. **Safeguard — dirty tree.** If any dirty path is outside `.issueflows/`, **stop**: tell the user to use normal close or stash/discard product changes.
2. **Safeguard — unique commits.** If an issue-style branch `^\d+-.+` has commits not on `origin/<default>` that touch product files, **abort**; that work needs a normal PR. Tracking-only commits may proceed after confirm.
3. **Ops checklist confirm (always).** Show what ran, where, the result, and residual risk. Include the intent to `gh issue close <N>` and whether to commit `.issueflows/` tracking updates. Require an explicit yes.
4. Skip the test suite (no product change), the version bump, and the changelog unless the user passed `log "..."` / `note "..."`.
5. **Tracking.** Update `issue<N>_status.md` and move the group to `03-solved-issues/` or `02-partly-solved-issues/` per the Done checkbox.
6. **Optional commit** of `.issueflows/` changes on the current branch after confirm (default branch allowed). Never open a PR.
7. **Close on GitHub.** `gh issue close <N> --repo <owner/repo>`.
8. If on `<N>-*` with no unique commits, offer a switch to default (no delete).
9. **Output.** Checklist, archive path, tracking commit (if any), GitHub close result, and that **no PR** was opened.

## Constraints

- Never open a PR from this skill.
- Never force-push or delete branches.
- If unique unpushed product commits appear on the branch, **abort** and send the user to normal close — ops cannot skip review for those.
- When both `ops` and `yolo` labels are present, **ops wins** (announce the conflict).
