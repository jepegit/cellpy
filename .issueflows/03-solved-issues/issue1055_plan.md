# Issue #1055 plan

## Goal

Ship a lazy, fail-soft `cellpy.cli_plugins` discovery module (no live CLI
mount) so Stage 2 and cellpy-connectors share one contract: entry-point
**name** is the mount name; `typer.Typer` / `click.Group` / `click.Command`
only; `import cellpy` never scans the group.

## Constraints

- No edits to `cellpy/cli.py`, `cli_surface.json`, or contributor/agent docs
  (Stage 2 / later #1042 issue).
- Do not add `cli_plugins` to `cellpy/__init__.py` `__all__` or `_LAZY_*`
  ([cli-light-startup.md](../04-designs-and-guides/cli-light-startup.md)).
- No new third-party deps.
- `discover()` must not call `EntryPoint.load()`. Type checks and import
  failures happen only in `load_plugin` / a load-all helper. A broken plugin
  must not raise out of either function.
- Warnings use the project logger (`logging.getLogger(__name__)`), include
  entry name + distribution (`EntryPoint.dist`) + exception / reason.
- Tests that guard this contract take `@pytest.mark.essential` (same bar as
  `tests/test_loader_contract.py`).

### Prior art

- `cellpy.readers.instruments.registry` — `ENTRY_POINT_GROUP`,
  `_iter_entry_points()`, cached `get_registry()`, `clear_registry()`,
  fail-soft `load()`, first-wins on duplicate keys, warning + continue.
  **Mirror** the shape; do not share the module (different group, objects,
  and lazy-vs-eager split).
- `tests/test_loader_contract.py::_FakeEntryPoint` /
  `_patch_entry_points` — **reuse the pattern** (copy into
  `tests/test_cli_plugins.py`; add a `dist` stub for warning text).
- `tests/test_cli_light_import.py` — Stage 2 only; this issue only asserts
  `import cellpy` / `import cellpy.cli_plugins` do not call
  `_iter_entry_points`.
- Toolbox (`00-tools/`) — no helper for entry-point discovery.

## Approach

New module `cellpy/cli_plugins.py`:

| Symbol | Behaviour |
| --- | --- |
| `ENTRY_POINT_GROUP` | `"cellpy.cli_plugins"` |
| `_iter_entry_points()` | `importlib.metadata.entry_points(group=...)` — the monkeypatch seam |
| `discover(*, refresh=False)` | Cache `dict[str, EntryPoint]`. First name wins; later duplicates warn + skip. **No `load()`.** |
| `load_plugin(name)` | `ep.load()` then accept `typer.Typer`, `click.Group`, `click.Command` (Typer is not a Click subclass — check Typer first). Else warn + return `None`. Exceptions: warn + `None`. Unknown name → `None` (no warning required). |
| `load_all()` | For each `discover()` name, `load_plugin`; return `dict[str, object]` of successes only. Stage 2 will call this (or equivalent) when mounting. |
| `clear()` | Drop the `discover()` cache (and any load cache if we keep one). |

`import cellpy.cli_plugins` defines the functions only — no scan at import.

Durable note `.issueflows/04-designs-and-guides/cli-plugins.md`: group name,
accepted types, mount-name = entry-point name, fail-soft, first-wins, lazy
`load()`, “do not import this from `cellpy/__init__.py`”. Point at #1055 /
epic #1042.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/cli_plugins.py` | New discovery module |
| `tests/test_cli_plugins.py` | Essential tests (list below) |
| `.issueflows/04-designs-and-guides/cli-plugins.md` | Contract note |
| `.issueflows/04-designs-and-guides/test-registry.md` | Row for the new essential file |
| `.issueflows/01-current-issues/issue1055_status.md` | Status during build |

## Test strategy

`uv run pytest tests/test_cli_plugins.py` then `uv run pytest -m essential`.

Monkeypatch `_iter_entry_points` with a `_FakeEntryPoint` that has `name`,
`value`, `load()`, optional `boom`, and `dist` (object with `.name`).

1. Valid `typer.Typer` (and one `click.Command`) returned by `load_plugin`;
   `load()` call count is 0 after `discover()`, ≥1 after `load_plugin`.
2. Broken `load()` → `None` + warning; sibling still in `discover()` and
   `load_all()`.
3. Non-command object → skipped + warning; not in `load_all()`.
4. Duplicate names: first EntryPoint kept; warning names the loser.
5. Spy: `import cellpy` and `importlib.reload(cellpy.cli_plugins)` /
   `clear()` do not iterate; first `discover()` does; second `discover()`
   does not (cache); `refresh=True` does.
6. `_iter_entry_points` asks `entry_points(group="cellpy.cli_plugins")`.

## Open questions

None — contract locked in epic #1042 / the issue body. Build follows the
table above.
