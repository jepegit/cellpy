# Issue #1051 plan — connect Cursor / other IDEs to the cellpy MCP server

## Goal

Give cellpy’s own docs an end-to-end recipe for wiring Cursor (and other stdio
MCP clients) to `cellpy-mcp`, and make `cellpy mcp install --list-clients` work
through the shim the README already advertises.

## Constraints

- Docs live on `master` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)). Same PR as the shim flag.
- Do **not** duplicate the cellpy-mcp tool/prompt catalog. Link
  [cellpy-mcp](https://github.com/cellpy/cellpy-mcp) for that.
- Do **not** dump the recipe into root `AGENTS.md` (managed issue-flow block
  stays untouched). One pointer line in the **Using cellpy (for agents)**
  section is allowed — that matches
  [this-project.md](../04-designs-and-guides/this-project.md) when the CLI
  surface changes.
- Do **not** add new `install --client` backends (Windsurf, Cline, …).
- Do **not** extend the hard `cellpy_mcp` contract (`__version__`, `serve`,
  `install`, `describe`). `--list-clients` is implemented only in
  `cellpy_mcp.__main__` today; listing must not call `install()`.
- Installer names stay `claude-desktop` / `cursor` / `vscode` as in
  cellpy-mcp `clients.py`.
- Keep `agents.md` as the **library-import** guide; MCP is a sibling page.

### Prior art

- Shim + absence/contract tests: [`cellpy/cli_api.py`](../../cellpy/cli_api.py)
  (`mcp_serve` / `mcp_install` / `mcp_status`), [`cellpy/cli.py`](../../cellpy/cli.py)
  (`mcp` typer group), [`tests/test_cli_mcp.py`](../../tests/test_cli_mcp.py)
  (essential). **Extend** these; do not add a new command group.
- cellpy-mcp registration copy (source of client paths / JSON / Claude Code
  refusal): [cellpy-mcp README](https://github.com/cellpy/cellpy-mcp) and
  `cellpy_mcp.clients` (`CLIENTS`, `MANUAL`, `config_path`, `command_for`).
  cellpy-mcp#1 already added Cursor/VS Code installers. **Mirror** that
  content into a walkthrough; do not fork path tables that will drift —
  tell the reader `cellpy mcp install --list-clients` is authoritative for
  *this machine*.
- Agent library recipes: [`docs/getting_started/agents.md`](../../docs/getting_started/agents.md).
  **Coexist** — one-line fork at the top, no merge.
- CLI stub: [`docs/reference/cli.md`](../../docs/reference/cli.md) `cellpy mcp`.
  **Replace** the stub with a short pointer + flags.
- CLI surface snapshot: [`tests/data/cli_surface.json`](../../tests/data/cli_surface.json)
  records `mcp` as a group (`install`/`serve`/`status`) with empty `params`.
  Nested `install` flags are **not** in the snapshot today — adding
  `--list-clients` should not require a snapshot regen. Confirm when editing.
- Toolbox (`00-tools/`): none applicable.
- Graphify: no `graphify-out/GRAPH_REPORT.md` in this worktree.

## Approach

### 1. Recipe page (main deliverable)

Add [`docs/getting_started/mcp.md`](../../docs/getting_started/mcp.md) in the
same tone as `agents.md` (researcher-first, copy-paste first, then traps).
Order matches the issue:

1. **What this is** — local stdio; the client spawns `python -m cellpy_mcp`;
   nothing hosted; files stay on disk except what is pasted into chat.
2. **Prerequisites** — `pip install cellpy cellpy-mcp` (also `uv` / conda);
   `cellpy setup`; `cellpy mcp status` must show server + cellpy versions +
   roots.
3. **Fast path** — `install --client cursor --dry-run` then without
   `--dry-run`; restart; one first prompt (example cell → capacity vs cycle).
4. **Cursor** — global `~/.cursor/mcp.json` vs project `.cursor/mcp.json`
   (project wins; installer writes **global**); exact JSON; `sys.executable`
   from the env that has `cellpy-mcp`; Settings → MCP (verify current Cursor
   UI wording, do not invent); how to see a failed spawn; how to confirm
   `load_cell` / `search_api` appear.
5. **WSL / Windows split** (the failure this workspace hits) — three cases,
   each naming **which file** the client reads:
   - *Cursor opened on the WSL folder / remote* → Linux `~/.cursor/mcp.json`
     (what `cellpy mcp install --client cursor` writes inside WSL).
   - *Windows Cursor editing `\\wsl$\…` or a synced tree* → Windows
     `%USERPROFILE%\.cursor\mcp.json`. WSL install does **not** update that
     file. Fix: write the Windows file by hand, or put a **project**
     `.cursor/mcp.json` in the workspace, or use a `wsl.exe -e <linux-python>
     -m cellpy_mcp` command from Windows (Linux paths in `CELLPY_MCP_ROOT`).
   - Optional: Cursor Cloud / SSH — same rule: the `command` path must exist
     **on the machine that spawns the server**.
6. **Other harnesses** — table from the issue (Claude Desktop default,
   Cursor, VS Code `servers` key, Claude Code via `claude mcp add`, generic
   stdio). Named extras (Windsurf, Cline, Continue, Codex, Gemini CLI, Zed)
   are “same JSON, different file” — **no** fake `--client` values.
7. **Roots** — configured local dirs; `CELLPY_MCP_ROOT` (PATH-separated);
   remote URIs dropped; fallback `~/cellpy_mcp`; never the whole filesystem.
8. **Verify / troubleshoot** — `status`; wrong interpreter; WSL home
   mismatch; VS Code wrong key; do not hand-run `serve` except to see it
   start; `serve` must print nothing on stdout; restart required.
9. **See also** — cellpy-mcp README (tools/limits); `agents.md` (import, not
   chat).

Client file paths in prose stay aligned with current cellpy-mcp `clients.py`.
If README and `clients.py` disagree, **trust `clients.py`**.

### 2. Findability

| File | Change |
| --- | --- |
| `zensical.toml` | Nav entry after “Using cellpy from an agent”. |
| `docs/getting_started/index.md` | Bullet. |
| `docs/how_do_i.md` | Under Get started: “…connect Cursor / Copilot / Claude to my cells?” → `mcp.md`. |
| `docs/reference/cli.md` | Short pointer to `mcp.md`; keep the three verbs; document `--client`, `--root`, `--dry-run`, `--list-clients`. |
| `docs/getting_started/agents.md` | One-line fork at the top (MCP vs import). |
| `docs/getting_started/checkup.md` | `mcp` row already exists — point it at `mcp.md`. |
| `AGENTS.md` | One line in **Using cellpy (for agents)** only. Not the managed issue-flow block. |
| GitHub `README.md` | **Skip** (optional in the issue; RTD already linked). |

### 3. Shim: `--list-clients`

Add the flag on `cellpy mcp install` (typer) and `cli_api.mcp_install(..., list_clients=False)`.

When `list_clients` is true, **never** call `module.install()`:

1. If `getattr(module, "list_clients", None)` is callable, use it (future-proof).
2. Else import `cellpy_mcp.clients` (`CLIENTS`, `MANUAL`, `config_path`,
   `command_for`) and print the same lines `cellpy_mcp.__main__` prints
   (name, path, note; Claude Code as `run: …`).
3. Else `ui.fail` with `python -m cellpy_mcp install --list-clients` — do not
   invent a hardcoded path table in cellpy.

Missing package still goes through `_import_mcp()` (stderr + hint). Exit
non-zero only on that failure / the fail path, not on a successful list.

Do not add `list_clients` to the documented four-name contract comment
except a one-line note that listing is optional and falls back to
`cellpy_mcp.clients`.

### 4. HISTORY

One Unreleased bullet: recipe page + `cellpy mcp install --list-clients`. (#1051)

## Files to touch

- `docs/getting_started/mcp.md` — **new** recipe.
- `zensical.toml` — nav.
- `docs/getting_started/index.md`, `agents.md`, `checkup.md` — pointers.
- `docs/how_do_i.md` — Get-started question.
- `docs/reference/cli.md` — expand `cellpy mcp`.
- `AGENTS.md` — one pointer line (unmanaged section).
- `cellpy/cli.py` — `--list-clients` on `mcp install`.
- `cellpy/cli_api.py` — `mcp_install(list_clients=…)`.
- `tests/test_cli_mcp.py` — essential tests (below).
- `HISTORY.md` — Unreleased note.
- `tests/data/cli_surface.json` — only if the snapshot actually sees the new
  flag (unexpected; confirm).

## Test strategy

Toolchain: `uv run pytest -m essential` (and `uv run pytest tests/test_cli_mcp.py`).

Add to `tests/test_cli_mcp.py` (keep `essential`):

- `cellpy mcp install --help` lists `--list-clients`.
- Stub with `list_clients()` callable: listing calls it, **`install` is not
  called**, stdout has its output, no “restart” hint.
- Stub **without** `list_clients` / `clients`: fail path, `install` not called.
- Absent package: same install hint as `serve`, non-zero via CLI.

No live `cellpy-mcp` install in CI. No docs build required for the merge gate
(docs.yml is separate); keep markup consistent with sibling pages.

## Open questions

- **README one-liner?** Default **no** (this plan). Say yes if you want it
  on the GitHub front page anyway.
- Everything else in the issue spec is treated as decided (Cursor-first
  walkthrough, WSL split, no new client backends, shim fallback via
  `cellpy_mcp.clients`, AGENTS.md pointer only).
