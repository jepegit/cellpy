# Status — doctor (`/iflow-status doctor`)

Read this to **detect and optionally fix** inconsistent issue-tracking
folders under `.issueflows/`.

Unlike `/iflow-status` (read-only overview), `/iflow-status doctor` can **move issue
groups** when the user confirms repair — using the same safe sweep rules as
`/iflow-pick` and `/iflow-build`.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`:
> - **Audit:** `issue-flow doctor [--json]` (or `issue-flow agent audit`).
> - **Repair:** `issue-flow doctor --fix [--except N] [--dry-run] [--json]`
>   (or `issue-flow agent repair`).
> - **Workspace audit:** trailing `workspace` / `all`, or cwd is the workspace
>   root → `issue-flow workspace doctor [--json]` (no `--fix`).
>
> The CLI is optional: if it is missing or errors, fall back to the manual
> checks below.

1. **Resolve project root** — use `issue-flow agent resolve` when available.
   If the user passed `workspace` / `all`, or cwd is the workspace root (toml
   present, not a member), run `issue-flow workspace doctor` and present each
   member. Repair stays per-repo: `issue-flow doctor --fix -C <member>` after
   they name members. Do not `--fix` the whole workspace in one shot.

2. **Audit** — run `issue-flow doctor`. Without the CLI, check by hand:
   more than one `issue<N>_*` group in `01-current-issues/` with no `<N>-slug` branch (error);
   a non-focus group in `01-current-issues/` (sweep it); the same number in two
   lifecycle folders (error, manual merge); a focus group marked `- [x] Done`
   (run close); a plan or status file without `issue<N>_original.md`; missing
   `.issueflows/` subfolders (create them).
   Present every finding: code, severity, message, suggested next step.

3. **Repair (only on explicit user confirm)** — run
   `issue-flow doctor --fix` with `--dry-run` first when anything will move;
   pass `--except N` when multiple groups sit in `01-current-issues/`
   and focus is ambiguous. Never repair duplicate-across-folders automatically.

4. **Re-audit** after repair and report what changed.

5. **Housekeeping commit (default when issueflows-only dirty)** — Doctor repair
   is filesystem-only; it never runs `git commit`. After a successful repair,
   check the working tree (`issue-flow agent preflight --json` when available,
   else `git status --porcelain`):
   - If **clean** — done.
   - If dirty and **every** path is under `.issueflows/`
     (`issueflows_only: true` in preflight JSON, or the same rule by hand) —
     list the paths, propose
     `chore: doctor housekeeping — archive/sweep .issueflows groups`,
     and ask for **one confirm** with **yes as the recommended default**.
     On yes: `git add` **only** those paths and commit (no push). If the
     current branch is the **default**, commit on a chore branch (or a tiny
     PR) instead — do not leave housekeeping unpushed on home default
    . On no: leave dirty and note that `/iflow-pick` will
     offer the same commit again.
   - If dirty with any path **outside** `.issueflows/` — report mixed
     dirt; do **not** offer the housekeeping default (user must sort code
     changes separately).

4. **Essential tests audit** (optional; this project has `essential_tests = true`) —
   Only when the user asks for a full-suite essential review (or after folder
   repair if they opt in). Do **not** run this on every doctor call by default.
   - Read `.issueflows/04-designs-and-guides/essential-tests.md` and
     `.issueflows/04-designs-and-guides/test-registry.md`.
   - Scan the pytest suite vs the registry: missing rows, marked-but-not-listed,
     listed-but-unmarked, candidates to demote (suite growing too large), tests
     created outside issue-flow.
   - Present a consolidated proposal (mark / unmark / registry edits). Apply
     only after one confirm. Prefer graphify when available to name code under
     test; never silently rewrite unrelated tests.
   - Marker name: `essential`.

## Constraints

- **Safe repairs only** — mkdir missing tree folders; sweep non-focus groups
  from `01-current-issues/` to `02-partly-solved-issues/` or
  `03-solved-issues/` by Done status. No deletes, no duplicate merges.
- **Gated moves** — nothing moves without a consolidated user confirm.
- **No CLI auto-commit** — `doctor --fix` never commits; the agent commits
  only after the step-5 confirm, and never stages paths outside
  `.issueflows/`.
- Degrade gracefully when the CLI is absent (manual checklist + sweep steps).
