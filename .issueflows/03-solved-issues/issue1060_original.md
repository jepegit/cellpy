# Issue #1060: Exercise the live cellpy-connectors CLI plugin from a GitHub dev dependency

Source: https://github.com/jepegit/cellpy/issues/1060

## Original issue text

## Problem / context

cellpy now mounts third-party commands from `cellpy.cli_plugins` (#1042 / #1055 / #1058). The first real plugin is [cellpy/cellpy-connectors#4](https://github.com/cellpy/cellpy-connectors/issues/4) (`cellpy connectors ping`). That package is **not on PyPI** yet.

Existing tests only monkeypatch fake entry points. They never install a real distribution, so CI cannot catch a broken hook, a bad entry-point name, or a regression in lazy load once a genuine plugin is present.

## Spec

- Add `cellpy-connectors` to the **`dev` dependency group** via a **Git URL** (not PyPI, not a path override):
  ```toml
  "cellpy-connectors @ git+https://github.com/cellpy/cellpy-connectors.git"
  ```
  Regenerating `uv.lock` will pin the resolved commit. Do **not** add `[tool.uv.sources]` path overrides (breaks Dependabot; see `CONTRIBUTING.md`).
- Do **not** add connectors to `[project.dependencies]` — `pip install cellpy` must not pull it.
- Add tests that use the **installed** plugin (no monkeypatch of `_iter_entry_points` for these cases):
  - `cellpy --help` lists `connectors` and does not import `cellpy_connectors` (`EntryPoint.load()` not run).
  - `cellpy connectors ping` exits 0 and prints `cellpy-connectors: ok`.
  - `import cellpy` does not import `cellpy_connectors`.
- Keep the monkeypatched unit tests. `#569` snapshot (`dev/snapshot_cli_surface.py`) already empties the plugin registry — it must still pass with connectors installed. `tests/test_cli_light_import.py` must still pass.
- Short `CONTRIBUTING.md` note: the git pin is temporary; switch to a PyPI version pin when connectors is published.

## Acceptance criteria

- `uv sync` installs `cellpy-connectors` from GitHub into the dev env (CI included).
- New tests fail if the entry point is missing or `ping` breaks; they pass on current connectors `main`.
- Essential / snapshot / light-import suites stay green with the plugin installed.
- Runtime extra/`pip install cellpy` does not require connectors.

## Out of scope

- Publishing cellpy-connectors to PyPI.
- BatBase, `configure`, keyring, `cellpy.metadata_sources` (#784 / connectors #1–#3).
- Making connectors a runtime dependency.

## Related

- Epic #1042; mount #1058 / #1059.
- https://github.com/cellpy/cellpy-connectors/issues/4
- Contract: `.issueflows/04-designs-and-guides/cli-plugins.md`
