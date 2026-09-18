# Issue #1055: Discover CLI plugins via the cellpy.cli_plugins entry-point group

Source: https://github.com/jepegit/cellpy/issues/1055

## Original issue text

## Context

Epic #1042 adds a generic CLI plugin hook so third-party packages (cellpy-connectors first) can mount commands under `cellpy` without changing this repo. The live CLI is **Typer** (`cellpy/cli.py`), not a raw Click group — the epic-anchor wording that says “Click Command or Group” is stale. This issue locks the contract and ships discovery only; it does **not** mount anything on the live CLI.

Precedent: `cellpy/readers/instruments/registry.py` and `tests/test_loader_contract.py::_patch_entry_points` (`cellpy.loaders`).

## Scope

Add a small discovery module (suggested home `cellpy/cli_plugins.py` — not inside `cli.py`) that owns:

- `ENTRY_POINT_GROUP = "cellpy.cli_plugins"`
- `_iter_entry_points()` / `discover()` / `clear()` mirroring the loader registry

Rules:

- Scan `importlib.metadata.entry_points(group=...)` on first use of the registry, **not** at `import cellpy` and not at import of this module.
- Each entry’s **name** is the mount name. Do not take the object’s own Click/Typer name for the top-level slot (that is how a connector package declares `connectors = "cellpy_connectors.cli:app"`).
- `load()` the object only when a caller asks for the command object (lazy).
- Accept `typer.Typer`, `click.Group`, and `click.Command`. Anything else is a warning naming the entry and the distribution (`EntryPoint.dist`) and is skipped.
- Import / `load()` exceptions: warning with entry name + distribution + exception, then continue (fail-soft).
- Two plugins claiming the same entry-point name: first wins, later ones warn and skip (loader-registry rule).
- **No mount into the live CLI** in this issue.

Record the contract (group name, accepted types, mount-name rule, fail-soft, first-wins) in a short durable note under `.issueflows/04-designs-and-guides/` so Stage 2 and cellpy/cellpy-connectors#3 share one source.

## Acceptance criteria

Tests monkeypatch `_iter_entry_points` with the same `_FakeEntryPoint` pattern as `tests/test_loader_contract.py::_patch_entry_points`:

1. A valid Typer (or Click) object is returned by name and `load()` is not called until requested.
2. A broken `load()` is skipped and the healthy sibling still appears.
3. A non-command object is skipped.
4. Duplicate names keep the first.
5. `import cellpy` / import of the module does not iterate entry points (spy like `test_discovery_is_lazy`).

**Goal:** `discover()` returns only healthy plugins; a broken plugin cannot raise out of discovery; `load()` is deferred until asked; `import cellpy` does not scan the group.

**Model:** deep

**Depends on:** none

Part of epic #1042.
