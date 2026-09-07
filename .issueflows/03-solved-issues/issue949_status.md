# Issue #949 status

- [x] Done

## What's done

- `batch_summary.py`: `_pick_optional_summary` / `_select_ir_column`.
  `direction="discharge"` prefers `ir_discharge`, falls back to `ir_charge`
  with a `UserWarning`, warns and skips when neither column exists.
  Matplotlib uses the same pick.
- Essential tests in `tests/test_batch_summary_ir.py` (8 passed with plotly;
  4 skip on essential `uv sync` without `--extra batch`).
- Design doc, test-registry, `agents.md`, `AGENTS.md`, `HISTORY.md`.
- Essential suite: 817 passed, 64 skipped.

## Remaining work

None.
