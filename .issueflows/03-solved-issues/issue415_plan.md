# Issue #415 plan — Bump pandas to 3.0.3

## Goal

Raise the `pandas` dependency from 2.3.3 to 3.0.3 and fix all test regressions so the suite is green. Primary breakage called out in the issue is BDF export (`cellpy.exporters.bdf`); reproduction shows **42 failures** across four test modules on pandas 3.0.3.

## Constraints

- Keep BDF export behaviour byte-identical for the default path (no change to column map, unit conversion, or header semantics).
- Respect [bdf-export.md](../04-designs-and-guides/bdf-export.md): no new `cellpy.utils` imports in `cellpy.exporters.bdf`.
- Regenerate `uv.lock` with `UV_NO_SOURCES=1 uv lock` after changing `pyproject.toml` (per cellpy-core migration rules when touching deps).
- Minimal diffs — replace removed APIs, don't refactor surrounding code.

### Prior art

- [`cellpy/exporters/bdf.py`](../../cellpy/exporters/bdf.py) — `_datetime_to_unix_seconds` uses `Series.view("int64")` (removed in pandas 3).
- [`cellpy/readers/instruments/processors/post_processors.py`](../../cellpy/readers/instruments/processors/post_processors.py) — same `.view("int64")` pattern on datetime columns (not hit by BDF tests but will break instrument post-processing).
- [`cellpy/utils/batch_tools/batch_journals.py`](../../cellpy/utils/batch_tools/batch_journals.py) — `.values.flatten()` on string columns; pandas 3 returns `ArrowStringArray` which has no `.flatten()` (5 failures in batch/easyplot).
- [bdf-export.md](../04-designs-and-guides/bdf-export.md) — design doc for BDF layer; no code changes needed unless behaviour shifts.
- `00-tools/` — empty index; no reusable helpers.
- Graphify — not consulted (grep + targeted pytest sufficient).

## Approach

### 1. Bump dependency

In `pyproject.toml`, change `"pandas<3"` → `"pandas>=3.0.3,<4"` (or pin `==3.0.3` if that matches project convention for core deps). Run `uv lock` and `uv sync`.

### 2. Fix BDF datetime conversion (30 test failures)

In `_datetime_to_unix_seconds` ([`bdf.py:334`](../../cellpy/exporters/bdf.py)):

```python
# before (pandas 3: AttributeError — Series.view removed)
return ts.view("int64") / 1e9

# after
return ts.astype("int64") / 1e9
```

`astype("int64")` is the documented replacement; Unix-second values stay identical for timezone-aware `datetime64[ns]`.

### 3. Fix post-processor datetime re-interpretation (proactive)

In `post_processors.py` lines 196 and 212, replace `.view("int64")` with `.astype("int64")` on the same datetime64→nanoseconds path. Same root cause as BDF; prevents silent runtime failures on instrument loads.

### 4. Fix batch journal string extraction (5 test failures)

In `batch_journals.py` (~439, 444, 449), replace:

```python
list(col.dropna().values.flatten())
```

with `.dropna().tolist()` (1-D Series; no flatten needed). Applies to `bad_cells`, `starred`, and `notes` columns. Pandas 3 string dtype is backed by PyArrow; `.values` is an `ArrowStringArray` without `.flatten()`.

### 5. Investigate plotutils summary_plot (7 test failures)

`tests/test_plotutils_summary_plot.py::TestSummaryPlotBasic` — figure returned but lacks `get_axes` and `show`. Likely `summary_plot` returns a Plotly figure when seaborn/matplotlib path is expected, or a wrapper type changed under pandas 3. Reproduce after steps 1–4; inspect return type from `cellpy.utils.plotutils.summary_plot` and adjust either the implementation or the test assertion (prefer fixing the implementation if a pandas-3 dtype change broke the seaborn branch).

## Files to touch

| File | Change |
|------|--------|
| `pyproject.toml` | Relax/pin pandas to 3.0.3 |
| `uv.lock` | Regenerate |
| `cellpy/exporters/bdf.py` | `view` → `astype` in `_datetime_to_unix_seconds` |
| `cellpy/readers/instruments/processors/post_processors.py` | `view` → `astype` (2 sites) |
| `cellpy/utils/batch_tools/batch_journals.py` | `.values.flatten()` → `.tolist()` (3 sites) |
| `cellpy/utils/plotutils.py` (TBD) | Only if step 5 investigation finds a real bug |

## Test strategy

Primary command (conda recommended per project rules; `uv run pytest` also valid):

```bash
cd cellpy
uv sync
uv run pytest tests/test_exporters_bdf.py -q          # 33 tests — must all pass
uv run pytest tests/test_batch.py tests/test_easyplot.py -q
uv run pytest tests/test_plotutils_summary_plot.py -q
uv run pytest -q                                       # full suite (~447+ pass, 0 fail)
```

Confirm pandas version: `uv run python -c "import pandas; print(pandas.__version__)"` → `3.0.3`.

No new tests strictly required — existing BDF and batch tests already cover the broken paths. Optional: add a one-liner unit test on `_datetime_to_unix_seconds` if we want isolation from the heavy `CellpyCell` fixture (not required for this fix).

## Open questions

1. **Pin vs range** — Pin `pandas==3.0.3` exactly, or allow `>=3.0.3,<4`? Recommend `>=3.0.3,<4` unless Dependabot/issue author wants exact pin.
2. **Plotutils scope** — If the 7 plotutils failures pre-exist on pandas 2.3.3 (environment flake), treat as out-of-scope for #415. Will verify during `/iflow-start` before editing plot code.
