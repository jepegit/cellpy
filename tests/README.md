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
