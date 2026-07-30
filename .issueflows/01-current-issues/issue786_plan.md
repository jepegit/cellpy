# Issue #786 — plan (warnings-only reopen)

## Goal

Make `cellpy.list_instruments()` (and ideally discovery via `instrument_configurations()`) quiet for **expected** loader-probe skips, so apps can call it at startup without bracketing the root logger. Keep the existing `id` / `label` / `models` / `suffixes` API unchanged.

## Constraints

- Warnings-only reopen: do **not** redesign labels/suffixes (already shipped in #796).
- Out of scope: #799 / #800 / #801 / other #791 items.
- Preserve behaviour of real loaders that fail for environmental reasons when used through normal load paths; only discovery noise should change.
- Public surface already documented in `docs/getting_started/agents.md` — update only if the quiet contract needs an explicit note.

### Prior art

- `cellpy.list_instruments()` in [`cellpy/readers/data_structures.py`](cellpy/readers/data_structures.py) — already raises `logging.getLogger("cellpy")` to `ERROR` during the scan; **misses** bare `logging.warning(...)` calls that go to the **root** logger.
- `InstrumentFactory.create_all()` in the same module — on create failure logs `logging.warning(f"Could not create loader for {key}: {e}")` except `local_instrument` (debug). This is the noise source.
- Module already has `logger = logging.getLogger(__name__)` at top of `data_structures.py` — unused by `create_all`.
- Tests: `test_list_instruments_shape_and_known_entry` / `test_list_instruments_is_quiet` in [`tests/test_instrument_registering.py`](tests/test_instrument_registering.py). The quiet test only asserts **Python `warnings`**, not **logging WARNING** — so it currently passes while the bug remains.
- Toolbox / graph: nothing relevant for logging quieting.

## Approach

1. **Classify expected discovery skips in `InstrumentFactory.create_all`**
   - If create fails because the module has no `DataLoader`, or `custom` raises “Missing instrument definition file…”, log at **DEBUG** via the module `logger` (not bare `logging.warning`).
   - Other failures (e.g. missing ODBC for a real SQL loader) stay at **WARNING**, but also via the module logger so they are filterable under `cellpy.readers.data_structures` rather than `root`.

2. **Make `list_instruments()` quiet by contract**
   - Add `create_all(..., quiet=False)`; `list_instruments()` calls `create_all(quiet=True)` so *all* probe failures during that scan are DEBUG (including env-missing real loaders).
   - Drop or shrink the ineffective `getLogger("cellpy").setLevel(ERROR)` wrapper once the above is in place (keep `warnings.catch_warnings` only if something still emits Python warnings).

3. **Harden the test**
   - Replace/extend `test_list_instruments_is_quiet` to use `caplog` at WARNING on the root logger **and** `cellpy.readers.data_structures`, asserting no “Could not create loader” records when calling `list_instruments()`.
   - Keep the shape/label test as-is.
   - Mark the quiet regression `@pytest.mark.essential` if Tier-1 should guard it (small, fast).

4. **Docs / HISTORY** — one Unreleased bullet that #786 warnings reopen is fixed (close step); optional one-liner in agents.md that `list_instruments()` is quiet at WARNING+.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/readers/data_structures.py` | `create_all(quiet=…)`; expected skips → DEBUG; use module logger; `list_instruments` uses `quiet=True` |
| `tests/test_instrument_registering.py` | Caplog-based quiet assertion (and essential marker if agreed) |
| `HISTORY.md` | Unreleased fix bullet (at close) |
| `docs/getting_started/agents.md` | Optional one-line quiet-contract note |

## Test strategy

```bash
uv run pytest tests/test_instrument_registering.py -q
uv run pytest -m essential
```

Manual smoke (matches issue repro):

```python
import logging, cellpy
logging.basicConfig(level=logging.INFO)
cellpy.list_instruments()  # no WARNING:root Could not create loader ...
```

## Open questions

1. **Should `instrument_configurations()` / `print_instruments` also go quiet for expected non-loader skips?**  
   **Recommended: yes** for the “no DataLoader / missing custom def” class (DEBUG), so `print_instruments` stops spam too; keep WARNING for unexpected real-loader failures unless `quiet=True`.
2. **Essential marker on the quiet test?**  
   **Recommended: yes** — tiny, guards the reopen regression that shipped incompletely once already.
