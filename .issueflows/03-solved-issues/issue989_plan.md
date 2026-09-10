# Issue #989 — plan (round 2: doubling is back)

## Goal

Make the documented promise true: after a raw load, every cumulative
capacity/energy column starts at 0 in every cycle, regardless of which loader
produced the frame. A tester that forgot to reset at a cycle boundary must not
double the per-cycle summary capacity.

## Evidence (root cause)

Probed `local/data/20260316_nor108_01_MLP01.cellpy` (cellpy 2.1.5, loaded
2026-09-10 via `arbin_sql_h5`, three merged `.h5` exports):

- `cumulative_charge_capacity`: 405 cycles start non-zero (every even cycle
  from 12 on), e.g. cycle 901 first = 0.951142 = cycle 900 last; cycle 901
  summary `charge_capacity` = 1.901845 (doubled). Same for discharge.
- `normalize_reset_granularity` returns early when
  `declarations.reset_granularity` is empty (`harmonize.py:83`). **No Arbin
  loader declares any granularity** (`arbin_sql_h5.declarations()` and
  siblings), and config-based loaders default to `PER_CYCLE`, which is "left
  untouched". So the rebase only ever runs for `batmo_bdf` (PER_STEP) and
  configs with `cumulate_capacity_within_cycle`.
- Round 1 (2026-09-07) added the `UserWarning` + docs on the assumption that
  the rebase always runs. It does not. The `.cellpy`-file hypothesis in the
  comment is secondary: the file was produced from raw today and already
  carries the un-rebased raw.

## Constraints

- KISS: one behaviour, one place (`harmonize.normalize_reset_granularity`),
  no new module, no new dependency.
- Do not touch `cellpycore` (design doc: rebase is cellpy-only; core must not
  require it). No changes to persisted `.cellpy` raw on read — raw from a
  file is treated as-is; users regenerate from raw.
- Keep existing `PER_TEST` / `PER_STEP` semantics and tests unchanged.
- Parity: `tests/test_loader_port_parity.py` compares harmonized vs legacy
  raw. If a committed fixture has a forgotten reset, the new rebase will
  diverge from 1.x *by design*; excuse those columns with a documented
  reason rather than weaken the fix.
- Warn (project logger / `UserWarning`, as round 1) — never silent
  auto-correction.

### Prior art

- `cellpy/readers/instruments/harmonize.py::normalize_reset_granularity` —
  the existing PER_TEST branch (`col - col.first().over(cycle)`) is exactly
  the transform needed; extend, do not duplicate.
- `cellpycore.summarizers.normalize_capacity_granularity` — core's TEST mode
  (diff + cum_sum) assumes *never* resets; wrong for the mixed case here
  (resets on odd cycles, not on even). Coexist; do not call.
- `cellpy/readers/instruments/testing.py::check_reset_granularity` — kit
  check 7; currently only checks finiteness of per-cycle lasts. Natural place
  to enforce "cycle starts at 0".
- `config_declarations._CUMULATIVE_DEFAULTS` — the four cumulative native
  columns; reuse the same list from the schema.
- Toolbox (`.issueflows/00-tools/`): nothing relevant.

## Approach

1. **Guarded default rebase in `normalize_reset_granularity`.**
   Iterate over the four schema cumulative columns present in the frame (not
   only declared ones). Granularity = declared value, else `PER_CYCLE`.
   - `PER_STEP`, `PER_TEST`: unchanged.
   - `PER_CYCLE` (declared or default): *forgotten-reset guard*. Per cycle,
     `offset = first value in cycle`; apply `col - offset` only where
     `offset > rtol * max(|col|)` over the frame (`rtol = 1e-2`). A legit
     first-sample increment (I·dt, ≤ ~0.3 % of a cycle at realistic
     sampling) stays untouched and silent; a carry-over (≈ 100 % of the
     previous cycle) is rebased. Offsets at or below the threshold are 0.
   - Remove the early `return` on empty declarations (the cycle-column
     requirement stays: if `cycle_num` is absent, skip the default guard
     silently instead of raising — raising there would break loaders that
     never declared anything).
2. **One `UserWarning`** per harmonize call listing the rebased columns and
   the number of cycles affected, e.g.
   `cellpy rebased ... so each cycle starts at 0: cumulative_charge_capacity
   (405 cycles), ... The tester did not reset at those cycle boundaries; 1.x
   showed this as doubled capacity.` Reuse the existing warning text shape.
3. **Kit check 7** (`check_reset_granularity`): add the assertion that each
   cycle's first value is ≤ `rtol * max` for the present cumulative
   capacity columns — the contract now states the spec, not just finiteness.
4. **Docs**: correct `harmonize.py` docstrings, `AGENTS.md` /
   `docs/getting_started/agents.md` (claim now true; add "regenerate
   `.cellpy` files made by ≤ 2.1.5 from raw: `force_raw_file=True`"),
   `docs/getting_started/migration_v1_to_v2.md`,
   `.issueflows/04-designs-and-guides/harmonized-raw-default.md` (record the
   guard + threshold and why not `PER_TEST` for Arbin).
5. **HISTORY.md** entry at close (fix).

Not in scope: rewriting raw when reading an existing `.cellpy` file; changing
`cellpycore`; adding a config knob (behaviour is the already-documented
default; see open question 1).

## Files to touch

- `cellpy/readers/instruments/harmonize.py` — guarded default rebase, warning
  text, docstrings.
- `cellpy/readers/instruments/testing.py` — strengthen `check_reset_granularity`.
- `tests/test_harmonize.py` — new tests: undeclared frame with a forgotten
  reset at one cycle → that cycle rebased, others untouched, one warning
  naming the column + count; legit small first increment → untouched and no
  warning; energies rebased too; `PER_TEST` path unchanged.
- `tests/test_loader_port_parity.py` — only if a fixture has a carry-over:
  excuse the cumulative columns with a reason string pointing at #989.
- `AGENTS.md`, `docs/getting_started/agents.md`,
  `docs/getting_started/migration_v1_to_v2.md`,
  `.issueflows/04-designs-and-guides/harmonized-raw-default.md` — wording.
- `HISTORY.md` — at close.

## Test strategy

- `uv run pytest tests/test_harmonize.py tests/test_loader_port_parity.py
  tests/test_arbin_sql_h5_two_stage.py tests/test_arbin_variants_two_stage.py`
  during build.
- `uv run pytest -m essential` before close; full `uv run pytest` once.
- Manual: reload Inger Emma's raw (`force_raw_file=True`) or run
  `normalize_reset_granularity` on the probed frame from
  `local/data/20260316_nor108_01_MLP01.cellpy` and confirm cycle 901 summary
  ≈ 0.95 and one warning with 405 cycles. Script lives in `/tmp`, not the
  repo.

## Open questions

1. **Threshold** `rtol = 1e-2` of the column's max over the frame. Alternative
   is an exact "first ≈ previous cycle's last" match (more specific, two
   tolerances, ~2× code). Recommend the single relative threshold.
2. **Existing `.cellpy` files**: leave raw untouched on read and document
   re-load from raw (recommended, KISS), or also add a small
   `CellpyCell.rebase_capacity()` helper that runs the same function and then
   requires `make_step_table()` / `make_summary()`? Recommend docs only now;
   helper as follow-up if users ask.
3. Config knob to disable the guard? Recommend no — this restores the
   documented 2.x behaviour and warns whenever it acts.
