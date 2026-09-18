# Issue #1060 plan: live cellpy-connectors plugin in dev/CI

## Goal

Install the real `cellpy-connectors` distribution in the uv `dev` group from
GitHub (not PyPI) and add tests that exercise `cellpy connectors ping` without
monkeypatching entry points.

## Constraints

- Git URL only in `[dependency-groups] dev`. No `[project.dependencies]`.
  No `[tool.uv.sources]` path override (`CONTRIBUTING.md` / Dependabot).
- Lock with `UV_NO_SOURCES=1 uv lock` so the lock pins the resolved git
  commit. CI `uv sync` (`UV_NO_SOURCES=1`) already fetches the lock.
- Keep existing fake-entry-point tests
  (`tests/test_cli_plugins.py`, `tests/test_cli_plugin_mount.py`,
  light-import canary). New cases must not patch `_iter_entry_points`.
- `#569` snapshot already empties the plugin registry — do not regenerate
  `cli_surface.json`.
- Docs-on-master: CONTRIBUTING only. No built-in CLI surface change → skip
  `agents.md` / AGENTS agents block.
- No HISTORY here (`/iflow-close`).
- Conda env files / scheduled Tier-3: connectors is not on conda-forge.
  Do not expand this issue into env-yml work.

### Prior art

- Mount contract: [cli-plugins.md](../04-designs-and-guides/cli-plugins.md);
  live stubs in `cellpy/cli_plugins.py` (`CellpyCLIGroup`,
  `attach_plugin_stubs`).
- Fake plugins: `tests/test_cli_plugin_mount.py` (`CliRunner`,
  `_patch_entry_points`). **Coexist** — new file for the real dist.
- Light import subprocess helper: `tests/test_cli_light_import.py`
  (`_run_script`). **Reuse the pattern** (not the canary patch).
- Snapshot isolation: `dev/snapshot_cli_surface.py` clears
  `_iter_entry_points`. **Leave as-is.**
- Dual-repo pin style: `CONTRIBUTING.md` cellpy-core block (no path
  sources; `UV_NO_SOURCES=1 uv lock`). **Mirror** for connectors git pin.
- Toolbox: none that installs or invokes CLI plugins.
- Graph: no `graphify-out/` in this worktree.

## Approach

1. Add to `[dependency-groups] dev`:
   `"cellpy-connectors @ git+https://github.com/cellpy/cellpy-connectors.git"`.
   Run `UV_NO_SOURCES=1 uv lock` then `uv sync` so the env has the dist.
2. New `tests/test_cli_connectors_plugin.py`:
   - If `importlib.metadata.distribution("cellpy-connectors")` is missing,
     **skip** (conda/scheduled without the git pin). After `uv sync` it is
     present — then **fail** if `connectors` is absent or `ping` breaks.
   - `cli_plugins.clear()` then `CliRunner` / subprocess:
     - `--help` lists `connectors`; `cellpy_connectors` not in `sys.modules`.
     - `["connectors", "ping"]` exit 0, output contains `cellpy-connectors: ok`.
     - `import cellpy` does not import `cellpy_connectors` (subprocess).
   - Mark `@pytest.mark.essential` (merge gate; `uv sync` has the package).
3. CONTRIBUTING: one short paragraph under the dual-repo / lock note — git
   pin is temporary; replace with a PyPI version when published.
4. Registry rows in `test-registry.md`.

## Files to touch

| Path | Change |
| --- | --- |
| `pyproject.toml` | Git URL in `dev` group. |
| `uv.lock` | `UV_NO_SOURCES=1 uv lock`. |
| `tests/test_cli_connectors_plugin.py` | **New.** Real-plugin essential tests. |
| `CONTRIBUTING.md` | Temporary git-pin note. |
| `.issueflows/04-designs-and-guides/test-registry.md` | New rows. |

## Test strategy

```bash
UV_NO_SOURCES=1 uv lock
uv sync
uv run pytest tests/test_cli_connectors_plugin.py tests/test_cli_surface.py tests/test_cli_light_import.py tests/test_cli_plugin_mount.py
uv run pytest -m essential
```

Confirm `uv tree` / `importlib.metadata` sees `cellpy-connectors` and that
`[project.dependencies]` is unchanged.

## Open questions

None.
