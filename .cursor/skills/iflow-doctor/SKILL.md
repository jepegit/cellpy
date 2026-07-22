---
name: iflow-doctor
description: >-
  Audit .issueflows/ for dirty conditions and optionally apply safe repairs.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — doctor (`.issueflows/` health) (`/iflow-doctor`)

Follow this skill to **detect and optionally fix** inconsistent issue-tracking
folders under `.issueflows/`.

Unlike `/iflow-status` (read-only overview), `/iflow-doctor` can **move issue
groups** when the user confirms repair — using the same safe sweep rules as
`/iflow-init` and `/iflow-start`.

Do **not** auto-dispatch from `/iflow`, `/iflow-start`, or `/iflow-close`.


**Invoke:** type `iflow doctor` in chat, or `/iflow-doctor` from the slash menu (`iflow-doctor` also works).




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


## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`:
> - **Audit:** `issue-flow doctor [--json]` (or `issue-flow agent audit`).
> - **Repair:** `issue-flow doctor --fix [--except N] [--dry-run] [--json]`
>   (or `issue-flow agent repair`).
>
> The CLI is optional: if it is missing or errors, fall back to the manual
> checklist in `.issueflows/04-designs-and-guides/dirty-issueflows.md`.

1. **Resolve project root** — use `issue-flow agent resolve` when available.

2. **Audit** — run `issue-flow doctor` (or manual checks per the design doc).
   Present every finding: code, severity, message, suggested next step.

3. **Repair (only on explicit user confirm)** — run
   `issue-flow doctor --fix` with `--dry-run` first when anything will move;
   pass `--except N` when multiple groups sit in `01-current-issues/`
   and focus is ambiguous. Never repair duplicate-across-folders automatically.

4. **Re-audit** after repair and report what changed.

## Constraints

- **Off-path** — never auto-dispatch from `/iflow` or other lifecycle steps.
- **Safe repairs only** — mkdir missing tree folders; sweep non-focus groups
  from `01-current-issues/` to `02-partly-solved-issues/` or
  `03-solved-issues/` by Done status. No deletes, no duplicate merges.
- **Gated moves** — nothing moves without a consolidated user confirm.
- Degrade gracefully when the CLI is absent (manual checklist + sweep steps).
