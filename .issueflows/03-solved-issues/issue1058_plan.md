# Issue #1058 plan

## Goal

Mount `cellpy.cli_plugins` names on the live Typer CLI so `cellpy --help`
lists a plugin and invoking it runs it, without importing the plugin module
on `--help` / `info --version`, without stealing built-in names, and without
breaking the #569 surface snapshot.

## Constraints

- Honour [cli-plugins.md](../04-designs-and-guides/cli-plugins.md) (#1055):
  mount name = entry-point name; accept Typer / Click; fail-soft; first-wins
  already in `discover()`.
- [cli-light-startup.md](../04-designs-and-guides/cli-light-startup.md): do
  not import `cli_plugins` from `cellpy/__init__.py`. Importing it from
  `cellpy.cli` is OK (that module already imports Typer).
- Do not regenerate `tests/data/cli_surface.json` unless a built-in flag
  changes (it must not).
- Public CLI docs: `docs/getting_started/agents.md` + AGENTS.md agents
  blurb in this PR ([this-project.md](../04-designs-and-guides/this-project.md)).
- No `HISTORY.md` here — `/iflow-close` writes it.
- **`--help` vs broken plugins:** Click/Typer `--help` uses
  `self.commands` (`TyperGroup.list_commands` is a dict walk). Root `--help`
  must not call `load_plugin` (canary test). Therefore a *name* from
  `discover()` is registered as a **stub** and can appear on root `--help`
  even if later `load()` fails. Acceptance (2) is: invoke the broken name
  (or its `--help`) → warning names the distribution, exit 0, no traceback —
  not “name missing from root `--help`”. That last reading would require
  loading every plugin to format help.

### Prior art

- `cellpy.cli_plugins` — `discover` / `load_plugin` / `load_all` / `clear` /
  `_iter_entry_points`. **Use as-is**; add stub attach + lazy Click group
  here.
- `typer.core.TyperGroup` — `list_commands` / `get_command` only read
  `self.commands`. **Subclass** (`cls=` on the existing `typer.Typer(...)`)
  and attach stubs before those lookups.
- `tests/test_cli_plugins.py` `_FakeEntryPoint` / `_patch_entry_points` —
  **reuse** for mount tests.
- `tests/test_cli_light_import.py` — subprocess + `CliRunner`; **extend**.
- `tests/test_cli_surface.py` / `dev/snapshot_cli_surface.py` — walks
  `command.commands`. **Filter or empty-registry** so plugins never fail
  the snapshot.
- `docs/other/writing_a_loader_plugin.md` — **sibling page** for CLI
  plugins, same register-via-entry-point shape.
- Toolbox (`00-tools/`) — nothing for CLI/Click.

## Approach

1. **`cellpy/cli_plugins.py`**
   - `BUILTIN_COMMANDS = frozenset({convert, edit, info, mcp, new, pull,
     run, serve, setup})`.
   - `LazyPluginGroup(click.Group)`: short help like “Third-party CLI
     plugin.”; `load_plugin` only on `invoke` / child `get_command` /
     `list_commands`. Typer object → `typer.main.get_command`. Failed load:
     warning already from `load_plugin`; `invoke` exits 0.
   - `attach_plugin_stubs(group)`: `discover()` (no load); skip + warn if
     name is in `BUILTIN_COMMANDS` or already a non-stub in `group.commands`;
     otherwise `group.commands[name] = LazyPluginGroup(name)`. Idempotent.

2. **`cellpy/cli.py`**
   - `cli = typer.Typer(..., cls=CellpyCLIGroup)` where `CellpyCLIGroup`
     subclasses `typer.core.TyperGroup` and calls `attach_plugin_stubs(self)`
     at the start of `list_commands` and `get_command`. Fail-soft wrap:
     attach exceptions logged, `--help` still exit 0.

3. **Snapshot**
   - In `test_cli_surface.py` (or `build_surface`), `clear()` + patch
     `_iter_entry_points` to `[]` so the live command set is built-ins only.
     Do not rewrite `cli_surface.json`.

4. **Docs**
   - `docs/other/writing_a_cli_plugin.md` + links from `how_do_i.md` /
     guides index (same places as the loader page).
   - One line in `agents.md` and AGENTS.md agents block.
   - Note in `cli-plugins.md` that Stage 2 mount is this issue (stubs +
     lazy load).

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/cli_plugins.py` | `BUILTIN_COMMANDS`, `LazyPluginGroup`, `attach_plugin_stubs` |
| `cellpy/cli.py` | `cls=CellpyCLIGroup` on the root Typer |
| `tests/test_cli_plugin_mount.py` | Help / invoke / collision / broken (new, essential) |
| `tests/test_cli_light_import.py` | Canary: `--help` and `info --version` do not import plugin module |
| `tests/test_cli_surface.py` | Empty plugin registry around snapshot |
| `docs/other/writing_a_cli_plugin.md` | New |
| `docs/how_do_i.md`, `docs/guides/index.md` | Links |
| `docs/getting_started/agents.md`, `AGENTS.md` | One-liner |
| `.issueflows/04-designs-and-guides/cli-plugins.md` | Mount now landed |
| `.issueflows/04-designs-and-guides/test-registry.md` | New/extended essential rows |

## Test strategy

`uv run pytest tests/test_cli_plugin_mount.py tests/test_cli_light_import.py tests/test_cli_surface.py tests/test_cli_plugins.py` then `uv run pytest -m essential`.

Reuse `_FakeEntryPoint` + `_patch_entry_points`:

1. Healthy `typer.Typer` (and one `click.Command`): `--help` contains the
   name; `load()` count still 0; `invoke(["<name>"])` runs it (`loads >= 1`).
2. Broken `load()`: invoke that name → warning includes `dist.name`, exit 0.
3. Entry named `info`: stub not installed; `info --version` still works;
   warning.
4. Light-import subprocess: patch/register a plugin whose `load()` imports
   a canary module; after `["--help"]` and `["info", "--version"]` the canary
   is not in `sys.modules`.
5. Surface snapshot still matches `cli_surface.json` with plugins patched
   empty (and with a fake plugin registered — snapshot must ignore it).

## Open questions

None — `--help`/broken interpretation is in Constraints (only reading that
keeps the canary test possible).
