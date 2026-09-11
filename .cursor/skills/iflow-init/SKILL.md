---
name: iflow-init
description: >-
  Cold-start or check the issue-flow harness: guide issue-flow init when the
  scaffold is missing; point at update / doctor / iflow-capture when it exists.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — harness init (`/iflow-init`)

Follow this skill to **cold-start or check the issue-flow harness** in a project — the editor-facing counterpart of the CLI's `issue-flow init`.

This is **not** the step that pulls a GitHub issue into `.issueflows/`. That is **`/iflow-capture`** (chat: `iflow capture`). `/iflow-init` is **off-path**: `/iflow` never auto-dispatches here.


**Invoke:** type `iflow init` in chat, or `/iflow-init` from the slash menu (`iflow-init` also works).




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


## Instructions

1. **Detect harness state** under `<project_root>`:
   - `.issueflows/` present?
   - Agent skills present? Prefer the marker `.cursor/skills/iflow-init/SKILL.md` (or any `iflow-*` skill under `.cursor/skills/`).
   - Optional: `issue-flow agent resolve -C <project_root> --json` / `issue-flow doctor -C <project_root> --json` when the CLI is on `PATH`.

2. **Scaffold missing** (no `.issueflows/` and/or no issue-flow skills):
   - Tell the user the harness is not initialised.
   - Show the exact cold-start command from the project root, e.g. `issue-flow init .` or `uvx issue-flow init .` (add `--editor <id>` when they named an editor).
   - If `issue-flow` is on `PATH`, **offer** to run it after a yes; never run without confirm. Do **not** re-implement scaffolding in this skill.
   - After a successful init, remind them to pick an issue with `/iflow-pick` or capture one with `/iflow-capture <N>`.

3. **Harness already present**:
   - Say so briefly.
   - Point at:
     - `issue-flow update .` — refresh templates after upgrading the CLI.
     - `issue-flow update --editor <id>` / `/iflow-doctor` — add a missing editor scaffold (`missing_editor_scaffold`).
     - **`/iflow-capture <N>`** — pull a GitHub issue into `.issueflows/01-current-issues/`.
     - `/iflow-pick` — front door when no issue is chosen yet.
   - Do not run `init --force` unless the user explicitly asks to re-scaffold.

4. **Report** — missing vs present, commands shown or run, and the next suggested lifecycle step (usually `/iflow-pick` or `/iflow-capture`).

## Constraints

- Off-path: never auto-dispatched by `/iflow`.
- Never capture a GitHub issue, write `issue<N>_*.md`, or create an issue branch from this skill — that is `/iflow-capture` / `/iflow-pick`.
- Never invent a second scaffolder; only guide or confirm-run `issue-flow init` / `update`.
- Never `init --force` or delete scaffold files without an explicit user request.
