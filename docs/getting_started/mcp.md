# Connect an agent IDE to cellpy

This page wires **Cursor**, VS Code, Claude, or any other stdio MCP client to
cellpy so a chat agent can load cells, plot, and look up the API **without
writing Python**.

To **import cellpy as a library** from an agent (a GUI, a script, a notebook),
use [Using cellpy from an agent](agents.md) instead.

The server itself is the separate
[`cellpy-mcp`](https://github.com/cellpy/cellpy-mcp) package. Cellpy ships the
command you type (`cellpy mcp …`) and does not depend on the MCP SDK.

## What this is

A local [MCP](https://modelcontextprotocol.io/) server over **stdio**. Your
editor or chat client **spawns** `python -m cellpy_mcp` and talks to it on
stdin/stdout. There is nothing to host, no URL to open, and nothing leaves the
machine except what you paste into the chat.

Do not run `cellpy mcp serve` “in the background and connect”. The client
starts the process. Running `serve` by hand is only useful to see that it
starts — and it must print **nothing** on stdout (stdout *is* the protocol).

## Prerequisites

```console
python -m pip install cellpy cellpy-mcp
cellpy setup
cellpy mcp status
```

In this repo, use `uv run` instead of a bare `python` / `cellpy`. Conda is
fine if that is the env that already has cellpy.

`cellpy mcp status` should report:

- the **server** package version (or “not installed” plus the pip hint)
- the **cellpy** version that server would import
- the **roots** it may read and write
- which clients it can already see `cellpy` registered with

If the server line says “not installed”, the rest of this page will not work
until `cellpy-mcp` is in the same environment.

## Fast path (Cursor)

```console
cellpy mcp install --client cursor --dry-run
cellpy mcp install --client cursor
```

Restart Cursor. Then ask:

> Load the bundled example cell and plot charge capacity versus cycle.

`--dry-run` prints the file it *would* write and does not change anything.

## Cursor (detailed)

`cellpy mcp install --client cursor` writes the **global** file
`~/.cursor/mcp.json`. A project file `.cursor/mcp.json` (next to the repo
root) **wins** if both define a server named `cellpy`. The installer writes
global on purpose: “where my cells live” is not a property of whichever
repository happens to be open.

Both files use the top-level key `mcpServers`:

```json
{
  "mcpServers": {
    "cellpy": {
      "command": "/full/path/to/python",
      "args": ["-m", "cellpy_mcp"],
      "env": { "CELLPY_MCP_ROOT": "/path/to/cells" }
    }
  }
}
```

### The interpreter path

A desktop / IDE client **does not activate a virtualenv** and often has a
minimal `PATH`. `command` must be the **full path** to the interpreter that
has `cellpy-mcp` installed — never a bare `python`.

```console
python -c "import sys; print(sys.executable)"
```

In this repo: `uv run python -c "import sys; print(sys.executable)"`.

### See it in Cursor

After a restart, open **Cursor Settings → Tools & MCP** (on some builds this
sits under **Customize → MCPs**). You should see a `cellpy` server. Official
notes: [Cursor MCP](https://cursor.com/docs/mcp).

- Green / connected: expand it and confirm tools such as `load_cell` and
  `search_api`.
- Red / failed: the `command` path is almost always wrong (or that Python
  does not have `cellpy-mcp`). Open the **Output** panel and choose the MCP
  log if you need the spawn error.

Agent chats may still ask before calling a tool; that is Cursor’s approval
setting, not a broken server.

### WSL and Windows (which `mcp.json`?)

`~/.cursor/mcp.json` means *that process’s home directory*. Windows Cursor
and a WSL shell do **not** share one.

| How you opened Cursor | File the client reads | What `cellpy mcp install --client cursor` writes *inside WSL* |
| --- | --- | --- |
| Cursor on the **WSL folder / remote** (Linux home) | Linux `~/.cursor/mcp.json` | This file. Restart and it should appear. |
| **Windows** Cursor on `\\wsl$\…` or a synced Windows tree | `%USERPROFILE%\.cursor\mcp.json` (Windows home) | The **Linux** file. Windows Cursor will not see it. |

Fixes when Windows Cursor cannot see the server:

1. Write the same JSON into the **Windows** `%USERPROFILE%\.cursor\mcp.json`,
   *or*
2. Put a **project** `.cursor/mcp.json` in the workspace Cursor actually
   opened (project wins), *or*
3. Keep the config on Windows and spawn Linux Python via `wsl.exe`:

```json
{
  "mcpServers": {
    "cellpy": {
      "command": "wsl.exe",
      "args": ["-e", "/home/you/.venv/bin/python", "-m", "cellpy_mcp"],
      "env": { "CELLPY_MCP_ROOT": "/home/you/data/cells" }
    }
  }
}
```

`CELLPY_MCP_ROOT` in that last block is a **Linux** path. The `command` path
must exist **on the machine that starts the server**.

Cursor Cloud / SSH: same rule — install `cellpy-mcp` on the remote, and
point `command` at that remote interpreter.

## Other clients

`cellpy mcp install` writes Claude Desktop’s config by default. Pass
`--client` for the two file-based installers; Claude Code is a command, not
a file edit.

```console
cellpy mcp install --list-clients
```

That prints the path (or command) **on this machine**. Trust it over any
table in a README.

| Client | Register | Config |
| --- | --- | --- |
| Claude Desktop | `cellpy mcp install` | `mcpServers` in the Claude desktop config |
| Cursor | `cellpy mcp install --client cursor` | `~/.cursor/mcp.json` or `.cursor/mcp.json` |
| VS Code / Copilot | `cellpy mcp install --client vscode` | user `mcp.json`, key **`servers`** (not `mcpServers`) |
| Claude Code | `claude mcp add …` (the installer refuses to edit `~/.claude.json`) | CLI-managed |
| Anything else that speaks stdio (Windsurf, Cline, Continue, Codex, Gemini CLI, Zed, …) | by-hand JSON, same block, client-specific file | almost always `mcpServers` |

There is **no** `--client windsurf` (or Cline, Codex, …). Use the JSON below.

**VS Code names the key `servers`.** The wrong key parses, saves, and does
nothing — it looks like a broken server rather than an unregistered one.

### Claude Code

```console
claude mcp add cellpy --env CELLPY_MCP_ROOT=/path/to/cells -- python -m cellpy_mcp
```

`cellpy mcp install --list-clients` prints that line filled in with *your*
interpreter. Prefer the full path to Python after `--`, for the same reason
as Cursor.

### By-hand JSON (any stdio client)

```json
{
  "mcpServers": {
    "cellpy": {
      "command": "/full/path/to/python",
      "args": ["-m", "cellpy_mcp"],
      "env": { "CELLPY_MCP_ROOT": "/path/to/cells" }
    }
  }
}
```

For VS Code, the top-level key is `servers` instead of `mcpServers`. Restart
the client afterwards — none of them re-read the file while running.

You can skip cellpy’s shim entirely (`cellpy` 2.1.3.post3+ is what
`cellpy-mcp` requires):

```console
python -m cellpy_mcp serve
python -m cellpy_mcp install --dry-run
python -m cellpy_mcp status
```

## Roots (what it may read and write)

Reads and writes are confined to a set of roots.

By default those are the **local** directories cellpy already knows
(`rawdatadir`, `cellpydatadir`, `outdatadir`, `notebookdir`) from
`cellpy setup`. Override with `CELLPY_MCP_ROOT` — several directories,
separated the way `PATH` is on that OS:

```console
CELLPY_MCP_ROOT=/data/cells:/data/out cellpy mcp serve
```

Remote URIs (`scp://…`, `sftp://…`) are dropped: containment is
`pathlib`-based and cannot express “inside that share”. If cellpy has no
configured local paths, the single root is `~/cellpy_mcp` — never your
whole filesystem.

## Verify and troubleshoot

| Symptom | Likely cause |
| --- | --- |
| `cellpy mcp status` → server “not installed” | `pip install cellpy-mcp` into *this* env |
| Client shows the server as failed | `command` is not the interpreter that has `cellpy-mcp` (bare `python`, wrong venv) |
| Cursor on Windows never lists `cellpy` after a WSL install | Different `~/.cursor/mcp.json` — see [WSL and Windows](#wsl-and-windows-which-mcpjson) |
| VS Code ignores a file that looks correct | Top-level key is `mcpServers` instead of `servers` |
| `cellpy mcp serve` “does nothing” / client parse error | Banner or logs on **stdout**; that channel is the protocol |
| Tools missing after a successful install | Client not restarted |

`cellpy mcp status` is the command you script. It exits 0 even when the
server package is missing — “not installed” is a true answer.

## See also

- [cellpy-mcp](https://github.com/cellpy/cellpy-mcp) — tools, prompts, and
  limits (`load_cell` blocks, no quota, one client per process).
- [Using cellpy from an agent](agents.md) — import the library, do not chat
  to it.
- [Command-line reference — `cellpy mcp`](../reference/cli.md#cellpy-mcp)
- [Setup and configuration](configuration.md) — what `cellpy setup` writes
