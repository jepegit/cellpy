# Issue #434 — Status

- [x] Done

## What's done

- Branch `434-value-parity-comparator` from current `master`.
- `tests/parity.py` — `assert_value_parity(legacy, native, family, *, exceptions=...)`
  with raw/steps/summary mapping pairs, summary `{col}_{mode}` specific columns,
  row-key merge alignment, dtype-tolerant comparison.
- `tests/parity_support.py` — canonical `.res` pipeline + native engine frame builders
  (mirrors bridge nom-cap resolution for C-rate).
- `tests/test_value_parity.py` — 3 `@pytest.mark.essential` trivial-pass tests.
- `tests/README.md` — Stage 0.7 section.
- Archived #433 issue files to `03-solved-issues/`.
- Tests: `tests/test_value_parity.py -m essential` — 3 passed.
