# Issue #1058: Mount discovered CLI plugins on cellpy.cli without breaking --help or the surface snapshot

Source: https://github.com/jepegit/cellpy/issues/1058

## Original issue text

## Context

Epic #1042 Stage 2: wire the discovery module from #1055 (`cellpy.cli_plugins`) into the live Typer app so a third-party entry point appears under `cellpy`. Docs land in the same PR (public CLI surface).

Contract (do not reopen): `.issueflows/04-designs-and-guides/cli-plugins.md` — group `cellpy.cli_plugins`, mount name = entry-point name, accept `typer.Typer` / `click.Group` / `click.Command`, fail-soft, first-wins, lazy `load()`.

## Scope

In `cellpy/cli.py` (or a helper it calls once the Typer app exists), register each discovered plugin under the entry-point name.

- `typer.Typer` → `cli.add_typer(...)`
- `click.Group` / `click.Command` → the underlying Click group (`typer.main.get_command` / `add_command`)
- Built-in names win: if the entry-point name is one of `convert`, `edit`, `info`, `mcp`, `new`, `pull`, `run`, `serve`, `setup`, skip and warn — do not replace the built-in.
- Registration of the *name* may happen when the CLI app is first used (`--help` or invoke) so the name appears in `cellpy --help`; the plugin module must still not be imported until that command (or its own help) is invoked — use a thin lazy Click/Typer wrapper if `add_typer` would otherwise force `load()`.
- Fail-soft: a plugin that blows up during mount is logged and skipped; `cellpy --help` exits 0.

Docs in the same PR: a short sibling page next to `docs/other/writing_a_loader_plugin.md` (or a section in it plus `docs/how_do_i.md` / guides index link) showing the `[project.entry-points."cellpy.cli_plugins"]` stanza, accepted object types, fail-soft / collision rules, and “keep the plugin import light”. One-line note in `docs/getting_started/agents.md` and the AGENTS.md “Using cellpy (for agents)” block that third-party CLI commands arrive via that group.

No `HISTORY.md` in this issue — `/iflow-close` owns that.

## Acceptance criteria

1. A monkeypatched healthy plugin appears in `CliRunner().invoke(cli, ["--help"])` and `invoke(cli, ["<name>"])` runs it.
2. A broken plugin is absent from help; the warning names the distribution; exit 0.
3. A plugin named `info` is skipped and built-in `info --version` still works.
4. Extend `tests/test_cli_light_import.py` so a registered plugin whose `load()` would import a canary module is **not** imported by `cellpy --help` or `info --version`.
5. `tests/test_cli_surface.py` continues to compare **built-in** commands only — strip plugin names before compare, or run the snapshot against an empty registry. Do not regenerate `cli_surface.json` unless a built-in flag actually changes (it should not).

**Goal:** `cellpy --help` lists a fake plugin and never imports it; invoking the plugin runs it; built-ins and the #569 snapshot stay unchanged; docs exist beside the loader plugin page.

**Model:** default

**Depends on:** #1055

Part of epic #1042.
