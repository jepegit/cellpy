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

Datetime columns listed in ``tests/golden_support.py`` (currently ``date_time``) are
floored to **microsecond** precision before golden write/compare so parquet oracles stay
stable across platforms.

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

## `essential` marker

Fast smoke tests — read → step table → summary pipeline and cellpy/cellpy-core parity —
are marked `@pytest.mark.essential`. Run them locally with:

```bash
uv run pytest -m essential
```

Tier 1 CI runs the same subset on every PR to `master`. See
[`.issueflows/04-designs-and-guides/ci-tiers.md`](../.issueflows/04-designs-and-guides/ci-tiers.md).

## Running the full suite

See [`.issueflows/04-designs-and-guides/testing-and-coverage.md`](../.issueflows/04-designs-and-guides/testing-and-coverage.md).

```bash
uv run pytest
```

Default `addopts` in `pyproject.toml` deselects slow/local/unfinished markers.
