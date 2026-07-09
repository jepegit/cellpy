# Issue #431 — Plan

## Goal

Land Stage 0.4 unit-handling test groundwork: a strict-xfail registry-interop test and
legacy↔core converter parity fixtures in **cellpy**, plus confirmation that the
**cellpy-core** pint-optional guard from STEP-12 is already covered (add only if a gap
shows up).

## Constraints

- **Tests only** — no production refactors (Phase 1 registry unification is out of scope).
- **Depends on Stage 0.1** — reuse golden/oracle style from `#428`; no new parquet goldens
  required (hand-computed float oracles like core `#40`).
- **Plan doc paths** — issue says `code-reviews/`; read
  [`architecture-plan/unit-handling-cellpy2-plan.md`](../../architecture-plan/unit-handling-cellpy2-plan.md)
  §6 and STEP-12 in
  [`../cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-integration-roadmap.md`](../cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-integration-roadmap.md).
- **cellpy-core migration** — read
  [`../cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-migration.md`](../cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-migration.md)
  before touching the boundary; parity asserts values only, never passes `Quantity` objects
  across the seam in production code.
- **Modes** — parity covers **gravimetric / areal / absolute** only (issue acceptance);
  volumetric stays out until legacy `nominal_capacity_as_absolute` implements it.
- **Fast PR gate** — mark converter parity parametrization `@pytest.mark.essential`; registry
  interop stays unmarked (strict xfail is expected-fail, not a merge blocker).

### Prior art

| Hit | Module / file | Reuse |
|-----|---------------|--------|
| Legacy unit tests (reimplemented math) | `tests/test_units.py` | **Coexist** — keep; new module adds cross-boundary parity + interop xfail. |
| Core converter goldens | `cellpy-core/tests/test_units_converters.py` | **Mirror** — reuse same stub inputs / expected floats (mass=2, area=2, default `CellpyUnits`). |
| Core pint-optional guard | `cellpy-core/tests/test_units_optional.py` (issue #40) | **Confirm** — deliverable #3 likely done; verify in core pytest, document in status. |
| Two registries | `cellpy/readers/data_structures.py` (`_ureg`, `Q`) vs `cellpycore.units` | **Document** — interop xfail targets unit plan Phase 1. |
| Legacy converters | `cellpy/readers/cellreader.py` `get_converter_to_specific`, `nominal_capacity_as_absolute` | **Compare** — parity calls these vs `cellpycore.units.*` on identical inputs. |
| Unit plan §6 | `architecture-plan/unit-handling-cellpy2-plan.md` | **Authoritative** acceptance checklist. |
| Stage 0 pattern | `issue430_plan.md` (solved) | **Mirror** — `*_support.py` + focused test module + `tests/README.md` subsection. |
| Toolbox | `.issueflows/00-tools/` | Empty — no helpers to reuse. |

## Approach

### 0. Preflight (cellpy-core deliverable #3)

Before writing cellpy tests, run in sibling `cellpy-core`:

```bash
uv run pytest tests/test_units_optional.py tests/test_units_converters.py -q
```

If green: record in `issue431_status.md` that STEP-12 pint-optional + core-side converter
parity already exist (`test_units_optional.py`, `test_units_converters.py`); **no core code
changes** for this issue. If a gap appears (e.g. missing `ModuleNotFoundError` message),
add the minimal test/fix in **cellpy-core** as a follow-up commit on the same branch or a
paired PR — see Open questions.

### 1. Shared helpers — `tests/unit_parity_support.py`

Small module:

- `GOLDEN_CONVERTER_CASES` — parametrized `(mode, expected)` aligned with core
  `test_units_converters.py` defaults (gravimetric `500.0`, areal `0.5`, absolute `1.0`).
- `GOLDEN_NOM_CAP_CASES` — gravimetric / areal / absolute tuples matching core
  `test_nominal_capacity_as_absolute_*` (e.g. gravimetric `0.006` with nom_cap=3000,
  mass=2).
- `make_parity_cell(cellpy_data_instance)` — load or construct a `CellpyCell` whose
  `data` exposes `mass`, `active_electrode_area`, `nom_cap`, `nom_cap_specifics`,
  `raw_units`, and `cellpy_units` matching the core `_stub()` defaults (set attrs on a
  minimal `from_raw` cell or mutate `dataset` fixture).
- `make_core_stub()` — thin wrapper returning the same numeric/`CellpyUnits` inputs as
  core's `_stub()` for `cellpycore.units` calls.

### 2. Main test module — `tests/test_unit_handling_stage0.py`

#### A. Registry interop (`xfail(strict=True)`)

```python
@pytest.mark.xfail(
    strict=True,
    reason="Unit plan Phase 1: unify pint registries before cross-boundary Quantity math",
)
def test_cellpy_and_cellpycore_quantities_interoperate():
    ...
```

Multiply `cellpy.readers.data_structures.Q(1, "mAh")` with `cellpycore.units.Q(1, "h")`
(or equivalent). Expect pint registry mismatch today; becomes a hard pass after Phase 1.
Comment in test points at `architecture-plan/unit-handling-cellpy2-plan.md` Phase 1.

#### B. Converter parity (`@pytest.mark.essential`)

For each mode in `GOLDEN_CONVERTER_CASES`:

1. `legacy = cell.get_converter_to_specific(mode=mode)` on parity cell.
2. `core = cellpycore.units.get_converter_to_specific(make_core_stub(), mode=mode)`.
3. `assert legacy == pytest.approx(core)`.

For each case in `GOLDEN_NOM_CAP_CASES`:

1. `legacy = cell.nominal_capacity_as_absolute(...)` with matching kwargs.
2. `core = cellpycore.units.nominal_capacity_as_absolute(...)` with stub/meta.
3. `assert legacy == pytest.approx(core)`.

Optional one case: raw charge unit mismatch (`A*h` vs `mAh`) — mirrors core
`test_get_converter_to_specific_charge_unit_mismatch` if legacy behaves the same.

#### C. Coexistence with `tests/test_units.py`

Leave existing tests untouched. Add one-line pointer at top of `test_units.py` or in
`tests/README.md` → new module.

### 3. Documentation

Add **Unit-handling characterization (Stage 0.4)** subsection to `tests/README.md`:

- Files: `test_unit_handling_stage0.py`, `unit_parity_support.py`
- Interop xfail semantics (flips on Phase 1)
- Core STEP-12 verification pointer (`cellpy-core/tests/test_units_optional.py`)
- How to update golden floats when converter math intentionally changes

## Files to touch

| Path | Repo | Change |
|------|------|--------|
| `tests/unit_parity_support.py` | cellpy | **New** — shared golden cases + stub builders |
| `tests/test_unit_handling_stage0.py` | cellpy | **New** — interop xfail + parity tests |
| `tests/README.md` | cellpy | Stage 0.4 subsection |
| `tests/test_units.py` | cellpy | Optional one-line pointer comment |
| `cellpy-core/tests/*` | cellpy-core | **Only if preflight finds a gap** |

No changes to `cellreader.py`, `data_structures.py`, or `cellpycore.units` for this issue.

## Test strategy

```bash
# cellpy-core preflight (sibling checkout)
cd ../cellpy-core && uv run pytest tests/test_units_optional.py tests/test_units_converters.py -q

# cellpy development
cd ../cellpy
uv run pytest tests/test_unit_handling_stage0.py -v

# PR gate
uv run pytest -m essential

# Before merge
uv run pytest tests/test_unit_handling_stage0.py tests/test_units.py
```

**Essential budget:** ~3–4 parity parametrizations (one per mode + one nom_cap case). Interop
xfail excluded from essential count.

## Open questions

1. **Dual-repo PR vs cellpy-only** — **Recommended:** single **cellpy** PR (#431) for
   deliverables #1–#2; deliverable #3 = verification note in status/README referencing
   existing core tests. Only open a **cellpy-core** PR if preflight fails.
2. **Parity cell setup** — **Recommended:** mutate `dataset` fixture attrs to match core
   `_stub()` rather than new committed golden files (KISS; Stage 0.1 parquet not needed).
3. **Charge-unit mismatch case** — **Recommended:** include if legacy and core agree today;
   skip if legacy path differs (document in status).

## Branch

Switch off stale `430-prms-characterization-tests` (merged). Suggest:

```bash
git switch master && git pull --ff-only
git switch -c 431-unit-handling-stage0
```

**Branch preflight (2026-07-09):** on `430-prms-characterization-tests` (stale); dirty
`graphify-out/`; `issue431_original.md` untracked in `01-current-issues/`.
