# Start working with the current issue

`/issue-start` **implements** the plan that `/issue-plan` already wrote. Planning itself now lives in `/issue-plan` — this command no longer produces the plan.

The issue should already be explained in `.issueflows/01-current-issues/issue<N>_original.md` (from `/issue-init`) and a confirmed plan in `issue<N>_plan.md` (from `/issue-plan`).

## Input

If additional input is added, use that as implementation hints (scope, constraints, design preferences). It does **not** replace the plan file — update `issue<N>_plan.md` via `/issue-plan` first if the plan itself needs to change.

## Steps

0. **Find the focus issue.** Look in `.issueflows/01-current-issues/` for `issue<N>_original.md`. If missing or multiple groups are ambiguous, ask. Could the user have skipped `/issue-init`?

0.5 **Branch status preflight** (non-destructive — report, do not delete).
   - Detect the default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. If `gh` is unavailable, use `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else fall back to `main`.
   - Run `git fetch --prune` so tracking info is fresh.
   - Report: current branch, clean/dirty working tree (`git status --porcelain`), and ahead/behind counts vs `origin/<default>` (`git rev-list --left-right --count origin/<default>...HEAD`).
   - Classify the current branch:
     - On default (`main`/`master`/etc.): propose switching to or creating an issue branch before implementing, e.g. `git switch -c <N>-<short-slug>` where `N` is the focus issue number. Ask before running.
     - Matches `^(\d+)-.+`: treat the leading digits as issue number `N`. Cross-check `.issueflows/01-current-issues/`, `.issueflows/02-partly-solved-issues/`, and `.issueflows/03-solved-issues/`. If `issueN_*` is already under `02-partly-solved-issues/` or `03-solved-issues/`, warn that the branch looks stale and ask whether to switch back to default before continuing. Never delete a branch from `/issue-start`.
     - Any other branch name: warn that the branch does not look like an issue branch and ask whether to continue on it.

0.6 **Sweep stale current issues** (auto-safe file moves — no destructive git).
   - Group files in `.issueflows/01-current-issues/` by issue number (`issueNN_*`).
   - For every group **other than the focus issue**:
     - If any status markdown for that group contains `- [x] Done` (case-insensitive on `done`), move the whole group to `.issueflows/03-solved-issues/`.
     - Otherwise, move the whole group to `.issueflows/02-partly-solved-issues/`.
   - Never move the focus issue's own files.
   - Report every move (source -> destination, grouped by issue number) in the opening summary.

1. **Plan precondition.** Look for `issue<N>_plan.md` in `.issueflows/01-current-issues/`.
   - **Plan file present:** read it. Treat it as the source of truth for scope and approach. Continue to step 2.
   - **Plan file missing:** **do not hard-stop.** Ask the user:
     > "No plan file found for issue #N. How should I proceed?
     >  (a) Run `/issue-plan` now, then continue into implementation once you confirm the plan.
     >  (b) Proceed without a plan — I'll implement directly and note the skipped plan in the status file.
     >  (c) Abort."
     Wait for an explicit choice. On **(a)**, run the `/issue-plan` flow first (including its user-confirmation stop), then return here. On **(b)**, add a short `- Skipped /issue-plan on <date>` note to `issue<N>_status.md` and continue. On **(c)**, stop.

2. **Implement** the plan. Prefer minimal, focused diffs. Match existing code style and tooling. Follow project rules under `.cursor/rules/issueflow-rules.mdc` (e.g. `uv run` for Python, `uv add` / `uv remove` / `uv sync` for dependencies).
   - **Knowledge graph (optional).** If `graphify-out/GRAPH_REPORT.md` exists, skim it before grepping the codebase — it lists god-nodes and surprising connections that often point straight at the files you'll touch. If the project's structure has changed materially since the last graph build, consider running `/build` (or `issue-flow build`) before diving in. If `graphify-out/` does not exist, ignore this step (the integration is opt-in).
   - **Designs and guides.** Read any relevant files under `.issueflows/04-designs-and-guides/` before making non-trivial decisions. When the work produces a new design decision or establishes a project good-practice (one the plan flagged, or one that only became clear during implementation), add or update a short markdown file under `.issueflows/04-designs-and-guides/`: context, the decision, alternatives considered, and a link back to this issue. Keep it terse.

3. **Update the status file.** After meaningful progress, update (or create) `issue<N>_status.md` under `.issueflows/01-current-issues/` with a `- [ ] Done` checkbox that stays unchecked until fully resolved. Record what has landed and what remains so `/issue-pause` or `/issue-close` has accurate context.

4. **Hand off.** When the implementation is ready to ship, tell the user to run `/issue-close` (optionally with `bump`/`patch`/`minor`/`major`). Parking work mid-stream goes through `/issue-pause`.

## Output

Summarize what was implemented, how it matches the plan, what remains, and any branch / sweep warnings surfaced during the preflight.
