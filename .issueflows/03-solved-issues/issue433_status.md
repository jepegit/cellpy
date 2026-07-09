# Issue #433 — Status

- [x] Done

## What's done

- Branch `433-curve-extraction-goldens` from current `master`.
- `tests/curve_golden_support.py` — case registry, golden cell loader, curve frame
  normalization (drop raw index), NullData capture.
- Nine golden suites under `tests/data/goldens/curve_*` for `get_cap` / `get_ccap` /
  `get_dcap` / `get_ocv` option matrix + two NullData cases.
- `dev/regenerate_goldens.py` — curve suite registration.
- `tests/test_curve_goldens.py` — 18 parametrized `@pytest.mark.essential` tests.
- `tests/data/goldens/README.md` — curve suite row added.
- Archived #432 issue files to `03-solved-issues/`.
- Tests: `tests/test_curve_goldens.py -m essential` — 18 passed.
