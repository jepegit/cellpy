# Setup — harness mode (`/iflow-setup harness`)

Read this to **cold-start or check the issue-flow harness** — the editor-facing counterpart of the CLI's `issue-flow init` and `issue-flow workspace bootstrap`.

The `iflow-setup` skill is also written to the editor's **user-global** skill dir on `init` / `update` (placement `both`) so `iflow setup` works in a folder that has no project scaffold yet. The first machine still needs one CLI `init`/`update` or `uvx issue-flow workspace bootstrap` to plant that global copy. A project-local copy still wins inside a repo.

## Start directory (before member resolve)

For this skill, the start dir is `root:` / `-C` if given, else **cwd**. Do **not** run `issue-flow agent resolve` first when cwd looks like a **parent folder of repos** — resolve may pick a workspace default member and hide the parent. The single-project path below still uses the usual resolve order.

## Package vs scaffold (read first)

If the user asked to **upgrade** / **latest version** / **update the tool**,
that is the **package**, not this skill's scaffold path:

1. `uv tool upgrade issue-flow` (or `uv tool install issue-flow` if missing)
2. Then `issue-flow update` (one repo) or `issue-flow workspace update` (parent folder with toml)

`issue-flow update` alone does **not** upgrade the installed CLI. Full map:

https://issue-flow.readthedocs.io/en/latest/how-to/for-agents/

Also: https://issue-flow.readthedocs.io/llms.txt

If they asked to **init globally**, plant user-global `iflow-setup` with one
`issue-flow init` / `update` / `workspace bootstrap --yes` on this machine,
then follow the classify steps below. Do not `init` a parent folder of repos.

## Parent-folder recipe

When the start dir is a **folder of git sibling repos**, follow this public how-to — do **not** invent a different command order:

https://issue-flow.readthedocs.io/en/latest/how-to/workspaces/

| Situation | Command |
| --- | --- |
| First time (scaffold members + write toml) | `issue-flow workspace bootstrap --yes --default <name>` |
| Members already have `.issueflows/`; toml only | `issue-flow workspace init --default <name>` |
| Toml exists; refresh skills | `issue-flow workspace update` |

Show the user those commands (or the how-to URL) when explaining the path. The classify / confirm steps below still gate any `--yes`.

## Instructions

1. **Workspace file already present** at the start dir (or `issue-flow agent resolve --json` reports `workspace_root` equal to the start dir):
   - Say the workspace already exists.
   - Offer `issue-flow workspace update` / per-member `issue-flow update` (same as the how-to).
   - Do **not** re-bootstrap unless the user explicitly asks `--force` / re-init.

2. **Parent-folder / workspace path** — run classify-only:
   `issue-flow workspace bootstrap <start> --json`
   - If **two or more** children have status `scaffolded` or `unscaffolded` (own-git members):
     - Show the classified list (name, status, skip reasons).
     - Propose `--default` (first `scaffolded`, else first `unscaffolded`, or ask).
     - On **yes**, run
       `issue-flow workspace bootstrap <start> --yes --default <name>`
       (add `--skip-dep-check` / `--editor <id>` / `--force` only when the user asked).
     - After success: remind `/iflow-pick` **per repo** (or open the default member). Stop.
   - If fewer than two git members, continue with the single-project path below.
   - Never `git init` children; point non-git folders at `/iflow-setup`.
   - Never write `.issueflows/` on the parent.

3. **Single-project detect** under `<project_root>` (now resolve is fine):
   - `.issueflows/` present?
   - Agent skills present? Prefer the marker `.cursor/skills/iflow-setup/SKILL.md` (or any `iflow-*` skill under `.cursor/skills/`).
   - Optional: `issue-flow agent resolve -C <project_root> --json` / `issue-flow doctor -C <project_root> --json` when the CLI is on `PATH`.

4. **Scaffold missing** (no `.issueflows/` and/or no issue-flow skills):
   - Tell the user the harness is not initialised.
   - Show the exact cold-start command from the project root, e.g. `issue-flow init .` or `uvx issue-flow init .` (add `--editor <id>` when they named an editor).
   - If `issue-flow` is on `PATH`, **offer** to run it after a yes; never run without confirm. Do **not** re-implement scaffolding in this skill.
   - After a successful init, remind them to pick an issue with `/iflow-pick` or capture one with `/iflow-pick <N>`.

5. **Harness already present**:
   - Say so briefly.
   - Point at:
     - `issue-flow update .` — refresh templates after upgrading the CLI.
     - `issue-flow update --editor <id>` / `/iflow-status doctor` — add a missing editor scaffold (`missing_editor_scaffold`).
     - **`/iflow-pick <N>`** — pull a GitHub issue into `.issueflows/01-current-issues/`.
     - `/iflow-pick` — front door when no issue is chosen yet.
   - Do not run `init --force` unless the user explicitly asks to re-scaffold.

6. **Report** — workspace vs single-project path, missing vs present, commands shown or run, and the next suggested lifecycle step (usually `/iflow-pick`).

## Constraints

- Never capture a GitHub issue, write `issue<N>_*.md`, or create an issue branch from this skill — that is `/iflow-pick`.
- Never invent a second scaffolder; only guide or confirm-run `issue-flow init` / `update` / `workspace bootstrap`.
- Never `init --force`, rewrite `issueflow-workspace.toml`, or delete scaffold files without an explicit user request.
- If a scaffold / update commit is needed, do not leave it unpushed on home default — use a chore branch or a tiny PR.
