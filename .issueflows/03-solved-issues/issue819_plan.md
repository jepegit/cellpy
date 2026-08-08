# Plan: #819 — instrument wins over `.h5`/`.hdf5` auto-pick

## Goal

When `cellpy.get(..., instrument=<raw>)` is called on a `.h5`/`.hdf5` path,
route through the instrument loader — never the native cellpy reader — solely
because of the suffix. Uninstrumented native loads stay as today.

## Constraints

- Back-compat: `get(path.h5)` / `get(path.cellpy)` with **no** `instrument=`
  still auto-picks native when `auto_pick_cellpy_format=True`.
- `.cellpy` / `.cpy` remain unambiguous; auto-pick those even if `instrument=`
  is set (only `.h5`/`.hdf5` collide with raw loaders).
- Explicit `auto_pick_cellpy_format=False` stays the hard override.
- No new deps; keep change inside `get()`.

### Prior art

- `cellpy.get` auto-pick gate:
  [`cellpy/readers/cellreader.py`](cellpy/readers/cellreader.py) (~4252–4306) —
  today uses allow-list `instruments_with_colliding_file_suffix = ["arbin_sql_h5"]`
  (instrument **not in** list ⇒ pick native for `.h5`/`.hdf5`/`.cellpy`/`.cpy`).
- Existing raw `.h5` coverage: `tests/test_arbin_sql_h5.py`,
  `tests/test_loader_port_parity.py` (`arbin_sql_h5` fixture).
- Docs mentioning `get` / instruments: `docs/getting_started/basic_usage.md`,
  `docs/getting_started/agents.md`; get docstring in `cellreader.py`.
- Toolbox: nothing relevant (`00-tools/` scanned).
- Graph: skipped for this tiny gate change.

## Approach

1. Replace the colliding-instrument allow-list with a clearer rule:
   - If `auto_pick_cellpy_format` is false → never auto-pick.
   - If suffix is `.cellpy` / `.cpy` → auto-pick (instrument ignored).
   - If suffix is `.h5` / `.hdf5`:
     - auto-pick **only when** `instrument` is unset (`None` / empty);
     - if `instrument` is set (truthy) → raw path (`load_cellpy_file = False`).
2. Drop `instruments_with_colliding_file_suffix` (superseded; `arbin_sql_h5`
   covered by “any set instrument”).
3. Update `get` docstring: instrument wins over `.h5`/`.hdf5` suffix auto-pick.
4. Short note in `docs/getting_started/basic_usage.md` (and one line in
   `agents.md` if it already discusses instrument + get).
5. Regression test: assert routing — with a `.h5` path + non-empty
   `instrument=`, `CellpyCell.load` is **not** entered / `from_raw` **is**
   (monkeypatch), vs no instrument ⇒ `load` path for same suffix. Plus keep
   existing `arbin_sql_h5` load green.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/readers/cellreader.py` | Auto-pick condition + docstring |
| `tests/test_cellpy.py` (or small new focused test module) | Routing regression |
| `docs/getting_started/basic_usage.md` | Document rule |
| `docs/getting_started/agents.md` | One-line note if fits existing get guidance |

## Test strategy

- `uv run pytest tests/test_cellpy.py -q` (or the new test file) +
  `uv run pytest tests/test_arbin_sql_h5.py -q`
- Fast gate later: `uv run pytest -m essential`

## Open questions

1. **Unset instrument:** treat only `None` as unset, or also `""`?
   **Recommend:** truthy check (`if instrument:`) so `""` counts as unset.
2. **`.cellpy`/`.cpy` with instrument set:** still auto-pick native?
   **Recommend:** yes (unambiguous suffixes).
3. **No other open design forks** — issue already chose “instrument wins”
   over “document that callers must pass `auto_pick_cellpy_format=False`”.
