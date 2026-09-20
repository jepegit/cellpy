# Epic #1042: CLI plugin hook

Anchor: https://github.com/jepegit/cellpy/issues/1042
Status: confirmed

## Goal

A third-party package that declares an entry point in `cellpy.cli_plugins` gets
its command mounted under the `cellpy` CLI with no further change to this repo.
Plain `cellpy` (no plugins installed) behaves exactly as today: same command
set, same flags, same light startup.

Done when:

- A monkeypatched fake entry point appears in `cellpy --help` and runs.
- A plugin that raises on import is logged (warning, with the distribution
  name) and skipped; `cellpy --help` still exits 0.
- A plugin whose entry-point name collides with a built-in is skipped and
  warned; the built-in wins.
- `import cellpy` does not scan or import CLI plugins.
- `cellpy info --version` / default `cellpy setup` still pass
  `tests/test_cli_light_import.py` even when a plugin is registered.
- Contributor docs describe `cellpy.cli_plugins` next to `cellpy.loaders`.

## Constraints

- **This repo only.** No BatBase client, no `configure` command, no
  `requests`/`keyring` deps. Command *shape* (`cellpy connectors configure
  batbase` vs a top-level `batbase` group) is owned by
  [cellpy/cellpy-connectors#3](https://github.com/cellpy/cellpy-connectors/issues/3).
- **Not #784.** The `MetadataSource` Protocol / `cellpy.metadata_sources`
  registry stays on #784. This epic is the CLI discovery hook only.
- **CLI is Typer, not Click.** `cellpy/cli.py` is a `typer.Typer` app
  (Click underneath). The anchor text says "Click Command or Group" — that is
  stale. The contract must accept what plugins will actually ship
  (`typer.Typer` and/or `click.Command` / `click.Group`).
- **Light startup is law.** [cli-light-startup.md](../04-designs-and-guides/cli-light-startup.md)
  (#837 / #839): `import cellpy` stays lazy; `cellpy --help` and
  `cellpy info --version` must not import the reader stack. Plugin *metadata*
  may be read eagerly; plugin *modules* load on first use of that command (or
  that command's own `--help`), never at package import.
- **CLI surface snapshot is built-ins only.** `tests/test_cli_surface.py` /
  `tests/data/cli_surface.json` (#569) must keep matching the frozen built-in
  set (`convert`, `edit`, `info`, `mcp`, `new`, `pull`, `run`, `serve`,
  `setup`). Plugin names are extras and must not fail the snapshot when a
  plugin happens to be installed in the test env.
- **No new third-party deps.** `importlib.metadata` + existing Typer/Click.
- **Mirror the loader registry, do not fork a new style.**
  `cellpy/readers/instruments/registry.py` +
  `tests/test_loader_contract.py::_patch_entry_points` are the precedent:
  named group, fail-soft on import, first-wins on duplicate plugin names,
  monkeypatch `_iter_entry_points` in tests.
- **Docs on `master`.** [docs-on-master.md](../04-designs-and-guides/docs-on-master.md).
  Public CLI surface change updates `docs/getting_started/agents.md` and the
  short agents section in root `AGENTS.md` in the same PR
  ([this-project.md](../04-designs-and-guides/this-project.md)).
- **Parent design (context only):**
  [cellpy2-metadata-source-integration.md](../../cellpy-design-and-development/active/cellpy2-metadata-source-integration.md)
  §3.5 (HTTP/auth stay in the adapter package). #784.

## Stage 1 — Contract and discovery

Lock the entry-point contract and ship a testable discovery module that does
not touch `cellpy.cli` yet. This stage retires the Typer-vs-Click mismatch and
the "does `--help` import every plugin?" risk before anything is mounted.

- Goal: a `cellpy.cli_plugins` registry that lists, loads, and fail-softs
  plugins the same way `cellpy.loaders` does, with names only until first use.

### Issue: Discover CLI plugins via the cellpy.cli_plugins entry-point group

- Spec: Add a small discovery module (suggested home
  `cellpy/cli_plugins.py`, next to the loader registry's role — not inside
  `cli.py`) that owns `ENTRY_POINT_GROUP = "cellpy.cli_plugins"` and
  `_iter_entry_points()` / `discover()` / `clear()` mirroring
  `cellpy/readers/instruments/registry.py`. Scan
  `importlib.metadata.entry_points(group=...)` on first use of the registry,
  not at `import cellpy` and not at import of this module. Each entry's
  *name* is the mount name (do not take the object's own Click/Typer name for
  the top-level slot — that is how a connector package declares
  `connectors = "cellpy_connectors.cli:app"`). `load()` the object only when
  a caller asks for the command object (lazy). Accept `typer.Typer`,
  `click.Group`, and `click.Command`; anything else is a warning naming the
  entry and the distribution (`EntryPoint.dist`) and is skipped. Import /
  `load()` exceptions are the same: warning with entry name + distribution +
  exception, then continue. Two plugins claiming the same entry-point name:
  first wins, later ones warn and skip (loader-registry rule). No mount into
  the live CLI in this issue. Tests monkeypatch `_iter_entry_points` with the
  same `_FakeEntryPoint` pattern as
  `tests/test_loader_contract.py::_patch_entry_points`: (1) a valid Typer (or
  Click) object is returned by name and `load()` is not called until
  requested; (2) a broken `load()` is skipped and the healthy sibling still
  appears; (3) a non-command object is skipped; (4) duplicate names keep the
  first; (5) `import cellpy` / import of the module does not iterate entry
  points (spy like `test_discovery_is_lazy`). Record the contract (group
  name, accepted types, mount-name rule, fail-soft, first-wins) in a short
  durable note under `.issueflows/04-designs-and-guides/` so Stage 2 and
  cellpy-connectors#3 share one source.
- Goal: `discover()` returns only healthy plugins; a broken plugin cannot
  raise out of discovery; `load()` is deferred until asked; `import cellpy`
  does not scan the group.
- Model: deep
- Depends on: none
- yolo: no — Typer vs Click, lazy vs eager, and mount-name rule are design
  calls; blast radius is the public plugin contract connectors will pin to.
- Published: #1055

## Stage 2 — Mount on the live CLI

Wire Stage 1 into `cellpy.cli` and prove `--help`, collisions, light startup,
and the frozen CLI snapshot still hold. Docs land in the same PR because this
changes the public CLI surface.

- Goal: installing a plugin adds its command to `cellpy`; a missing or broken
  plugin leaves the built-in CLI unchanged.

### Issue: Mount discovered CLI plugins on cellpy.cli without breaking --help or the surface snapshot

- Spec: In `cellpy/cli.py` (or a helper it calls once the Typer app exists),
  register each Stage 1 plugin under the entry-point name.
  `typer.Typer` → `cli.add_typer(...)`; `click.Group` / `click.Command` → the
  underlying Click group (`typer.main.get_command` / `add_command`). Built-in
  names win: if the entry-point name is one of `convert`, `edit`, `info`,
  `mcp`, `new`, `pull`, `run`, `serve`, `setup`, skip and warn — do not
  replace the built-in. Registration of the *name* may happen when the CLI
  app is first used (`--help` or invoke) so the name appears in
  `cellpy --help`; the plugin module must still not be imported until that
  command (or its own help) is invoked — use a thin lazy Click/Typer wrapper
  if `add_typer` would otherwise force `load()`. Fail-soft: a plugin that
  blows up during mount is logged and skipped; `cellpy --help` exits 0.
  Tests: (1) monkeypatched healthy plugin appears in `CliRunner().invoke(cli,
  ["--help"])` and `invoke(cli, ["<name>"])` runs it; (2) broken plugin is
  absent from help, warning names the distribution, exit 0; (3) a plugin
  named `info` is skipped and built-in `info --version` still works; (4)
  extend `tests/test_cli_light_import.py` so a registered plugin whose
  `load()` would import a canary module is **not** imported by
  `cellpy --help` or `info --version`; (5) `tests/test_cli_surface.py`
  continues to compare **built-in** commands only — either strip plugin
  names before compare, or run the snapshot against an empty registry. Do
  not regenerate `cli_surface.json` unless a built-in flag actually changes
  (it should not). Docs in the same PR: a short sibling page next to
  `docs/other/writing_a_loader_plugin.md` (or a section in it plus
  `docs/how_do_i.md` / guides index link) showing the
  `[project.entry-points."cellpy.cli_plugins"]` stanza, accepted object
  types, fail-soft / collision rules, and "keep the plugin import light".
  One-line note in `docs/getting_started/agents.md` and the AGENTS.md
  "Using cellpy (for agents)" block that third-party CLI commands arrive via
  that group. No `HISTORY.md` in this issue — `/iflow-close` owns that.
- Goal: `cellpy --help` lists a fake plugin and never imports it; invoking
  the plugin runs it; built-ins and the #569 snapshot stay unchanged; docs
  exist beside the loader plugin page.
- Model: default
- Depends on: stage 1 issue 1
- yolo: no — touches the live CLI, #569 surface snapshot, and light-startup
  essential tests; not mechanical.
- Published: #1058

## Later (unstaged)

- Optional: mention installed CLI plugins from `cellpy info` (nice-to-have,
  not required for connectors).
- cellpy-connectors#3 (shared base + `configure` CLI), #1 (`BatBaseClient`),
  #2 (`MetadataSource` adapter) — other repo; consume this hook, do not
  implement it.
- #784 `MetadataSource` / `cellpy.metadata_sources` — separate cellpy epic.
