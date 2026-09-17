# Issue #1051: Document connecting Cursor and other agent IDEs to the cellpy MCP server

Source: https://github.com/jepegit/cellpy/issues/1051

## Original issue text

### Problem / context

The MCP server lives in the separate [`cellpy-mcp`](https://github.com/cellpy/cellpy-mcp) package. Cellpy only ships a shim (`cellpy mcp status|install|serve`). People looking at cellpy docs never get a walkthrough: [`docs/reference/cli.md`](docs/reference/cli.md) lists the three verbs and `pip install cellpy-mcp`. [`docs/getting_started/agents.md`](docs/getting_started/agents.md) is about **importing the library**, not wiring a chat client.

The cellpy-mcp README already has a “Registering with your client” section (Claude Desktop, Cursor, VS Code, Claude Code, by-hand JSON). What is missing is a **recipe a Cursor / other-harness user can follow end-to-end** on the cellpy site: install, pick a client, write the right config, set roots, verify tools appear, and recover when the server shows as failed.

Known traps the current cellpy docs do not mention:

- A desktop / IDE client **does not activate a venv**. The config must use the **full path** to the interpreter that has `cellpy-mcp`, never a bare `python`.
- **WSL vs Windows Cursor** write different `~/.cursor/mcp.json` files. `cellpy mcp install --client cursor` run inside WSL updates the Linux home; Windows Cursor reads the Windows one. That is the most likely failure for this workspace.
- VS Code uses the top-level key `servers`, not `mcpServers`. The wrong key parses, saves, and does nothing.
- `cellpy mcp serve` is stdio. Stdout **is** the protocol. Do not run it “in the background and connect”; the client spawns it.
- The cellpy-mcp README advertises `cellpy mcp install --list-clients`, but the **cellpy shim does not forward `--list-clients`**. Only `python -m cellpy_mcp install --list-clients` works today.

### Spec

Add a getting-started recipe page and point every existing MCP mention at it. Do not duplicate the cellpy-mcp tool catalog; link it.

1. **New page** `docs/getting_started/mcp.md` — “Connect an agent IDE to cellpy”. Cover, in this order:

   - **What this is.** Local stdio MCP. The client starts `python -m cellpy_mcp`. Nothing is hosted; files stay on the machine (except what the user pastes into chat).
   - **Prerequisites.** `pip install cellpy cellpy-mcp` (or `uv` / conda equivalent), then `cellpy setup` so configured dirs exist. `cellpy mcp status` must report the server package, the cellpy version, and the roots.
   - **Fast path.**
     ```console
     cellpy mcp install --client cursor --dry-run
     cellpy mcp install --client cursor
     ```
     Restart the client. Then a first prompt (e.g. load the example cell and plot capacity vs cycle).
   - **Cursor (detailed).**
     - Global `~/.cursor/mcp.json` vs project `.cursor/mcp.json` (project wins; installer writes **global**, because “my cells” is not a property of the open repo).
     - Exact JSON (`mcpServers` → `cellpy` → `command` / `args` / `env.CELLPY_MCP_ROOT`).
     - How to get `command`: `python -c "import sys; print(sys.executable)"` from the env that has `cellpy-mcp` (`uv run python -c …` in this repo).
     - Cursor Settings → MCP: how to see the server and a failed spawn.
     - **WSL / remote:** Windows Cursor + WSL Python; Cursor opened on the WSL folder; optional `wsl.exe -e …` wrapper. State which `mcp.json` each setup reads.
     - How to confirm tools (`load_cell`, `search_api`, …) appear after restart.
   - **Other harnesses (table + copy-paste, not new installer backends).**
     | Client | How to register | Config key / file |
     | --- | --- | --- |
     | Claude Desktop | `cellpy mcp install` (default) | `mcpServers` in the Claude desktop config |
     | Cursor | `--client cursor` | `~/.cursor/mcp.json` or `.cursor/mcp.json` |
     | VS Code / Copilot | `--client vscode` | user `mcp.json`, key **`servers`** |
     | Claude Code | `claude mcp add …` (installer refuses to edit `~/.claude.json`) | CLI-managed |
     | Anything else that speaks stdio (Windsurf, Cline, Continue, Codex, Gemini CLI, Zed, …) | by-hand JSON, same block, client-specific file | almost always `mcpServers` |
   - **Roots.** Default = cellpy’s configured local dirs (`rawdatadir`, `cellpydatadir`, `outdatadir`, `notebookdir`). `CELLPY_MCP_ROOT` (PATH-separated). Remote URIs (`scp://…`) are dropped. Fallback `~/cellpy_mcp` if nothing is configured — never the whole filesystem.
   - **Verify / troubleshoot.** `cellpy mcp status`; failed spawn = wrong interpreter; WSL home mismatch; VS Code wrong key; “do not `cellpy mcp serve` by hand except to see it start”; restart required; `cellpy mcp serve` must print nothing on stdout.
   - **See also.** Link [cellpy-mcp README](https://github.com/cellpy/cellpy-mcp) for tools, prompts, and limits. Link `agents.md` for “I want to import cellpy, not chat to it”.

2. **Findability (this repo only).** Add the page to `zensical.toml` nav, `docs/getting_started/index.md`, `docs/how_do_i.md` (“…connect Cursor / Copilot / Claude to my cells?”), `docs/reference/cli.md` (replace the stub with a short pointer + the three verbs + `--client` / `--root` / `--dry-run`), and a one-line fork at the top of `agents.md`. Do **not** paste the recipe into root `AGENTS.md` (keep that file short). Optional one-liner in the GitHub README.

3. **Shim gap.** Forward `--list-clients` through `cellpy mcp install` so the advertised command works, with an essential test that the flag exists and does not try to write a config. No new client backends in this issue.

4. **`HISTORY.md`** user-facing note.

Keep installer client names and file paths aligned with `cellpy-mcp` (`claude-desktop`, `cursor`, `vscode`). If a path in their README has drifted, match their current `clients.py` and say so in the PR.

### Acceptance criteria

- [ ] `docs/getting_started/mcp.md` exists and can be followed without opening the cellpy-mcp repo first (that repo is linked for tools/limits only).
- [ ] Cursor is a full walkthrough: global vs project file, full interpreter path, WSL/Windows home split, how to confirm tools, one first prompt.
- [ ] Claude Desktop, VS Code, Claude Code, and a generic stdio block are present. Other named harnesses are “same JSON, different file” — not fake `--client` values.
- [ ] Roots / `CELLPY_MCP_ROOT` / remote-path drop / `~/cellpy_mcp` fallback are documented.
- [ ] Nav + `index.md` + `how_do_i.md` + `cli.md` + `agents.md` all point at the new page.
- [ ] `cellpy mcp install --list-clients` works through the cellpy shim and is tested.
- [ ] `HISTORY.md` updated. Docs stay on `master`.

### Out of scope

- New `cellpy mcp install --client …` backends (Windsurf, Cline, Codex, …). Add later if someone files a real config path.
- Changing MCP tools, sandbox, or HTTP/SSE hosting.
- Duplicating the tool/prompt catalog from the cellpy-mcp README.
- Screenshots of every IDE settings panel.
