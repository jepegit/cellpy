# Issue #938 plan

Replaces the yolo-abort stub (same filename, in place).

## Goal

Missing *system* tools must be visible: loading an Arbin `.res` without
`mdb-export` raises a named, installable error; `list_instruments()` still
lists loaders that failed to import (e.g. `arbin_sql*` without `libodbc.so.2`)
with `available=False` and a reason a UI can show.

## Constraints

- Stay quiet: `list_instruments` must not emit WARNING spam (#786). Unavailable
  rows are data, not log noise.
- Additive listing keys only — existing `id` / `label` / `models` / `suffixes`
  stay. Apps that ignore unknown keys keep working.
- Do not change conda env files or add pip extras for mdbtools/unixodbc
  (system packages).
- Windows bundled `mdb-export.exe` path stays as-is; the POSIX `PATH` name
  `"mdb-export"` is the missing-tool case.
- Public listing shape is documented in `docs/getting_started/agents.md` —
  update it in the same PR (AGENTS.md “Using cellpy” pointer if the short
  facts mention the key set).
- **Out of scope unless Open questions say otherwise:** the comment’s
  `examplesdir` default. That is cwd/relative-path config, not a missing
  tool. #960 is a different bug (legacy config file format).

### Prior art

- `OptionalDependencyError` (`cellpy/exceptions.py`) — named missing-dep
  error used for `tables` / matplotlib; reuse for mdbtools (message names
  apt/brew, not a pip extra).
- `arbin_res._loader_posix` already catches `FileNotFoundError`, logs
  “install mdbtools”, then **re-raises the bare** `FileNotFoundError`
  (`cellpy/readers/instruments/arbin_res.py`).
- `cli_api` already probes `command -v mdb-export` on posix (check path
  only; not used at load time).
- `InstrumentFactory.create_all(quiet=True)` swallows create failures —
  that is why `arbin_sql` / `arbin_sql_7` vanish
  (`cellpy/readers/data_structures.py`).
- `list_instruments()` (#786) — app picker; tests pin exact key set in
  `tests/test_instrument_registering.py`.
- Plot `registry.families()` (#868) lists names that exist; it does **not**
  actually return `(available, reason)` — mirror the *intent* (UI can enumerate
  gaps), not the tuple shape.
- `cellpy.readers.instruments.registry` is the entry-point loader path;
  built-ins still go through `InstrumentFactory`. Do not mix the two in this
  issue.
- Toolbox: no helper for this.

## Approach

**1. Named error when `mdb-export` is missing**

- Small helper next to the loader (e.g. `require_mdb_export(path)`): if `path`
  is the bare command `mdb-export` (posix) and `shutil.which` is `None`, raise
  `OptionalDependencyError` naming mdbtools + `apt install mdbtools` /
  `brew install mdbtools`.
- If `path` is an absolute/relative file (Windows bundled exe), keep today’s
  `os.path.isfile` / `FileNotFoundError` behaviour.
- Call the helper in `_loader_posix` **before** `subprocess.call`, replacing
  the re-raise of the raw `FileNotFoundError`.
- Do not lazy-rewrite the whole Arbin loader.

**2. Discovery reports unavailable loaders**

- After `register_builder` for every production loader, iterate **registered
  ids**, not only `create_all` successes.
- Success → existing row plus `available: True`, `reason: None`.
- `create()` / import failure (the `libodbc.so.2` `ImportError`) → still emit
  a row: `available: False`, `reason: <short exception text>`, empty
  `models` / `suffixes` if unknown.
- Expected skips (`local_instrument`, missing `DataLoader`) stay omitted.
- Optional cheap probe: if `arbin_res` created OK but posix `mdb-export` is
  missing, mark that row `available: False` with the same mdbtools reason
  (capability probe the issue asked for). Same helper as part 1.
- Keep `quiet=True` / DEBUG for the underlying create failures.

**3. Docs / tests**

- `list_instruments` docstring + `agents.md` picker bullet: keys become
  `{id, label, models, suffixes, available, reason}`.
- Tests: monkeypatch `shutil.which` → `OptionalDependencyError`; monkeypatch
  factory create for `arbin_sql` → row present with `available is False`;
  existing quiet + shape tests updated for the new keys.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/readers/instruments/arbin_res.py` | `require_mdb_export`; call before subprocess |
| `cellpy/readers/data_structures.py` | `list_instruments` includes failed creates + `available`/`reason` |
| `tests/test_instrument_registering.py` | shape keys; unavailable-row test; keep quiet contract |
| `tests/` (small new or next to arbin tests) | missing `mdb-export` raises named error |
| `docs/getting_started/agents.md` | picker dict keys |
| `.issueflows/04-designs-and-guides/instrument-availability.md` | short decision (listing unavailable vs omit) |

## Test strategy

- `uv run pytest -m essential`
- New/updated tests above; mark essential (public `list_instruments` + load
  error are app-facing).
- Full suite on CI.

## Open questions

1. **`examplesdir` comment (frozen-app cwd trap)** — **Recommend: defer.**
   Different subsystem; #960 is not this bug. Say **include here** if you
   want a third bullet (`PathsConfig` default + resolve relative →
   `Path.home() / "cellpy_data" / "examples"` in `example_data`).
2. **Exception class** — **Recommend: `OptionalDependencyError`.** New
   `CellpyDependencyError` name from the issue is extra surface for one
   caller.
3. **Mark `arbin_res` unavailable when mdbtools is missing?** — **Recommend:
   yes** (same helper). Listing would otherwise claim the loader works on a
   container without mdbtools.
