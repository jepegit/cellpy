# cellpy tests

## Golden fixtures

Characterization and parity oracles for cellpy 2 Stage 0 live under
[`data/goldens/`](data/goldens/). Files there are **committed snapshots** — regenerate
them only with:

```bash
uv run python dev/regenerate_goldens.py
uv run python dev/regenerate_goldens.py --verify   # assert byte-identical re-runs
```

Never edit golden files by hand; review diffs intentionally when re-running the script
after an expected behaviour change.

The ``date_time`` column is compared with ``pytest.approx`` (1 µs absolute tolerance in
epoch nanoseconds) because parquet round-trip can differ by 1 ns across platforms; all
other summary columns must match exactly.

### Layout

| Kind | Path pattern | Format |
|------|--------------|--------|
| DataFrame snapshot | `data/goldens/<suite>/<name>.parquet` | parquet (`index=False`, pyarrow) |
| Scalars / metadata | `data/goldens/<suite>/<name>.json` | UTF-8 JSON, sorted keys |

Legacy fixture locations are unchanged: `../testdata/` (raw instrument inputs),
[`fixtures/`](fixtures/) (older JSON helpers).

Philosophy (loader-free core vs loaderful cellpy): see
[`cellpy-core/.issueflows/04-designs-and-guides/test-data-and-fixtures.md`](../../cellpy-core/.issueflows/04-designs-and-guides/test-data-and-fixtures.md).

### Adding a suite

1. Register a function with `@register_golden_suite("my_suite")` in
   [`dev/regenerate_goldens.py`](../dev/regenerate_goldens.py).
2. Add tests that read from `tests/data/goldens/my_suite/` (skip if files missing).
3. Document the suite in [`data/goldens/README.md`](data/goldens/README.md).

## Cellpy-file characterization (Stage 0.2)

HDF5 load/save behavior is locked in [`test_cellpy_file_roundtrip.py`](test_cellpy_file_roundtrip.py)
before the cellpy-file module extraction. The primary v8 oracle is the committed fixture
`../testdata/hdf5/20160805_test001_45_cc_v8_with_fids.h5` (built from the canonical Arbin
`.res` with populated fid table).

Regenerate that file only when v8 **write** semantics change intentionally:

```bash
uv run python -c "
from pathlib import Path
from cellpy import cellreader
res = Path('testdata/data/20160805_test001_45_cc_01.res')
out = Path('testdata/hdf5/20160805_test001_45_cc_v8_with_fids.h5')
c = cellreader.CellpyCell()
c.from_raw(res); c.mass = 1.0; c.make_step_table(); c.make_summary(); c.save(out)
"
```

Three tests are marked `@pytest.mark.essential` (v8 round-trip, limits-prefix trap,
`max_cycle` selector). Legacy version matrix and corrupt-file tests run in the full suite only.

```bash
uv run pytest tests/test_cellpy_file_roundtrip.py -v
```

## Configuration characterization (Stage 0.3)

`prms` / `prmreader` / `cellpy setup` behavior is locked in
[`test_prms.py`](test_prms.py) with helpers in [`prms_support.py`](prms_support.py).
The frozen `EXPECTED_PRMS_INVENTORY` tuple list is the Step 2 pydantic parity contract —
update it intentionally when dataclass defaults change.

Five tests are marked `@pytest.mark.essential` (inventory, full-section round-trip,
precedence, OtherPath coercion smoke, `.env_cellpy` pickup). Non-dry-run `cellpy setup`
dir/file creation lives in [`test_cellpy_cmd.py`](test_cellpy_cmd.py) (full suite only).

Code defaults are authoritative when they differ from
`cellpy/parameters/.cellpy_prms_default.conf` (e.g. `Materials.cell_class` is `Li-Ion` in
code, `LIB` in the template YAML).

```bash
uv run pytest tests/test_prms.py -v
```

## Unit-handling characterization (Stage 0.4)

Legacy↔cellpycore converter parity and registry-interop groundwork live in
[`test_unit_handling_stage0.py`](test_unit_handling_stage0.py) with helpers in
[`unit_parity_support.py`](unit_parity_support.py). Golden floats mirror
`cellpy-core/tests/test_units_converters.py` (hand-computed oracles, not parquet).

Four tests are marked `@pytest.mark.essential` (gravimetric / areal / absolute
`get_converter_to_specific` parity plus gravimetric `nominal_capacity_as_absolute`).
`test_cellpy_and_cellpycore_quantities_interoperate` is a strict `xfail` until unit-plan
Phase 1 unifies pint registries (`architecture-plan/unit-handling-cellpy2-plan.md`).

cellpy-core STEP-12 pint-optional guard is already covered in the sibling checkout:
`cellpy-core/tests/test_units_optional.py` and `test_units_converters.py` (issue #40) —
no core changes required for Stage 0.4 unless that preflight regresses.

Update `GOLDEN_*_CASES` in `unit_parity_support.py` intentionally when converter math
changes on either side.

```bash
uv run pytest tests/test_unit_handling_stage0.py -v
```

## Value-parity oracle (Stage 0.7)

Legacy↔native column comparison through `cellpycore.legacy.mapping` lives in
[`parity.py`](parity.py) (`assert_value_parity`) with pipeline helpers in
[`parity_support.py`](parity_support.py). Trivial-pass bridge tests are in
[`test_value_parity.py`](test_value_parity.py) (raw / steps / summary on the canonical
Arbin `.res`, including `{col}_{mode}` specific summary columns).

Pass explicit exception column names (legacy or native) when a mapped column is
allowed to differ; unlisted mismatches always fail.

```bash
uv run pytest tests/test_value_parity.py -m essential
```

## `essential` marker

Fast smoke tests — read → step table → summary pipeline and cellpy/cellpy-core parity —
are marked `@pytest.mark.essential`. Run them locally with:

```bash
uv run pytest -m essential
```

Tier 1 CI runs the same subset on every PR to `master`. See
[`.issueflows/04-designs-and-guides/ci-tiers.md`](../.issueflows/04-designs-and-guides/ci-tiers.md)
and [`.github/workflows/ci-scheduled.yml`](../../.github/workflows/ci-scheduled.yml) for the
full conda/platform matrix (weekly + manual).

## Running the full suite

See [`.issueflows/04-designs-and-guides/testing-and-coverage.md`](../.issueflows/04-designs-and-guides/testing-and-coverage.md).

```bash
uv run pytest
```

Default `addopts` in `pyproject.toml` deselects slow/local/unfinished markers.
