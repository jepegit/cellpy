# Plan for issue #428: Golden-fixture convention and regeneration tooling

## Goal

Establish one shared golden-fixture convention for cellpy 2 Stage 0 work: committed
artifacts under `tests/data/goldens/`, regenerated only via `dev/regenerate_goldens.py`
(with per-suite registration), plus documentation and a toy suite exercised in CI through
the existing `essential` marker gate.

## Constraints

- **Behaviour-preserving infrastructure only** — no refactors, no migration of existing
  `testdata/` or `tests/fixtures/` in this issue. Later Stage 0 issues (#429–#433) register
  their own suites on this scaffold.
- **KISS** — one script file, one toy suite, one new test module; no new dependencies.
- **Deterministic output** — running the regenerator twice must yield byte-identical files
  (acceptance criterion from the issue).
- **CI-friendly tests** — the new golden test compares committed files only; it must not
  require regeneration on CI. Follow the same “committed snapshot” model as cellpy-core
  (`tests/test_golden.py` reads parquet; loaders run only at regen time).
- **Do not duplicate cellpy-core’s script** — `cellpy-core/dev/regenerate_test_data.py`
  stays the core-side exporter. cellpy gets its own `dev/regenerate_goldens.py` for
  cellpy-side characterization goldens (loaders, files, curves, etc.).
- **Branch target** — Stage 0 lands on `master` (per #439 exit criteria and
  [`cellpy-v2-branching.md`](../04-designs-and-guides/cellpy-v2-branching.md): Phase 0 gate
  work may merge to `master`). Work on branch `428-golden-fixture-convention`.

### Prior art

- **`cellpy-core/dev/regenerate_test_data.py`** — two-stage parquet regeneration,
  provenance comments, golden scalar checks. **Mirror** the registration + “never hand-edit”
  philosophy; do not merge the scripts.
- **`cellpy-core/tests/test_golden.py`** + **`cellpy-core/tests/data/README.md`** —
  regression test pattern (`assert_frame_equal`, skip-if-missing fixtures, documented
  regen commands). **Mirror** for cellpy-side tests.
- **`cellpy-core/.issueflows/04-designs-and-guides/test-data-and-fixtures.md`** — design
  rationale (loader-free core vs loaderful cellpy). **Cite** in `tests/README.md`.
- **`tests/fdv.py`** — canonical test paths (`res_file_path`, `cellpy_file_path`, …).
  **Reuse** for the toy suite source path (same file the `essential` tests already use).
- **`tests/test_cell_readers.py`** — existing scalar oracle (103 steps, 18 cycles, cycle-1
  `data_point` 1457). **Coexist**; the toy golden test encodes the same numbers in
  `metrics.json` so future suites have a JSON template.
- **`tests/fixtures/*.json`** — ad-hoc JSON fixtures for batch/plot tests. **Coexist**;
  new work goes under `tests/data/goldens/<suite>/`.
- **`tests/test_plotutils_summary_plot.py::TestGoldenReference*`** — plot-structure
  goldens, not dataframe snapshots. **Coexist**; different layer (visual regression).
- **`essential` marker** — already defined in [`pyproject.toml`](../../pyproject.toml) and
  run in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) Tier 1. **Document**
  relationship in `tests/README.md`; no marker definition change in this issue.
- **Toolbox (`00-tools/`)** — empty index. **None found** beyond the above.

## Approach

### 1. Directory layout

```
tests/data/goldens/
  README.md                         # suite index + regen one-liner (optional short pointer)
  pipeline_smoke/                   # toy suite (issue #428)
    summary.parquet                 # per-cycle summary after from_raw + make_summary
    metrics.json                    # scalar oracle: n_steps, n_cycles, cycle1_data_point
```

**Naming rules** (document in `tests/README.md`):

| Artifact | Path pattern | Format |
|----------|--------------|--------|
| DataFrame snapshot | `tests/data/goldens/<suite>/<name>.parquet` | parquet, `index=False`, pyarrow engine |
| Scalars / dict meta | `tests/data/goldens/<suite>/<name>.json` | UTF-8 JSON, sorted keys, trailing newline |
| Suite | `<suite>` = snake_case topic (`pipeline_smoke`, later `loader_arbin_res`, …) | one dir per suite |

Legacy locations stay untouched: `testdata/` (raw inputs), `tests/fixtures/` (legacy JSON).

### 2. `dev/regenerate_goldens.py`

Single entry point with a **registration decorator**:

```python
GOLDENS_ROOT = REPO_ROOT / "tests" / "data" / "goldens"
_SUITES: dict[str, Callable[[Path], None]] = {}

def register_golden_suite(name: str):
    """Register a regen callable; ``name`` is the subdirectory under goldens/."""
    ...

@register_golden_suite("pipeline_smoke")
def _regen_pipeline_smoke(out_dir: Path) -> None:
    ...
```

**CLI behaviour:**

```bash
uv run python dev/regenerate_goldens.py              # all suites
uv run python dev/regenerate_goldens.py pipeline_smoke
uv run python dev/regenerate_goldens.py --verify     # regen each suite twice to temp dirs, assert byte-identical
```

**Determinism helpers** (shared in the same file, small):

- Parquet: fixed column order (`sorted(df.columns)`), `index=False`,
  `engine="pyarrow"`, stable compression (`snappy`).
- JSON: `json.dumps(..., sort_keys=True, indent=2)` + `\n`.
- Write via temp file + `os.replace` (atomic).

**Toy suite `pipeline_smoke`:**

1. Load canonical cell via `CellpyCell.from_raw(tests/fdv.res_file_path)` (same source as
   `test_from_raw_local` / `test_make_new_step_table`).
2. `make_step_table()` + `make_summary()`.
3. Write `summary.parquet` (`data.summary.reset_index(drop=True)`).
4. Write `metrics.json` with `{n_steps, n_cycles, cycle1_data_point}` matching the known
   oracle (103 / 18 / 1457).
5. Print paths written + scalar check (warn if oracle drifted).

If `res_file_path` is missing (common on fresh clones without testdata), exit non-zero with
an actionable message — same expectation as existing reader tests.

### 3. Test module `tests/test_goldens.py`

- `@pytest.mark.essential`
- Skip gracefully if golden files or source `.res` missing (`pytest.skip` with reason).
- **Test A** — load `metrics.json`, run the same pipeline, assert scalars match.
- **Test B** — `assert_frame_equal` summary against `summary.parquet` (same tolerances as
  elsewhere: default pandas testing; use `check_dtype=False` only if a column dtype quirk
  appears — prefer fixing regen over loosening).
- No regeneration inside pytest.

Picked up automatically by existing CI: `uv run pytest -m essential`.

### 4. Documentation — `tests/README.md` (new)

Short top-level test README with sections:

1. **Golden fixtures** — “committed under `tests/data/goldens/`; regenerate with
   `uv run python dev/regenerate_goldens.py`; never edit by hand; review diffs intentionally.”
2. **`essential` marker** — fast inner loop + Tier 1 CI gate; `-m essential`; pointer to
   [`ci-tiers.md`](../04-designs-and-guides/ci-tiers.md).
3. **Adding a suite** — register with `@register_golden_suite`, add test module or parametrized
   case, link to cellpy-core `test-data-and-fixtures.md` for philosophy.

Cross-link from [`testing-and-coverage.md`](../04-designs-and-guides/testing-and-coverage.md)
(one line under “Running tests”) — optional tiny addendum, not a new design doc (keeps file
budget down).

### 5. What this issue explicitly does *not* do

- Migrate loader snapshots (#432), file round-trip matrix (#429), curve goldens (#433), or
  value-parity oracle (#434) — they only **register new suites** later.
- Change cellpy-core’s fixture paths or scripts.
- Add a separate CI job for `--verify` (local/dev check only unless we later promote it).

## Files to touch

| Path | Change |
|------|--------|
| `dev/regenerate_goldens.py` | **New** — registry, CLI, `--verify`, `pipeline_smoke` suite |
| `tests/data/goldens/pipeline_smoke/summary.parquet` | **New** — generated once during implementation |
| `tests/data/goldens/pipeline_smoke/metrics.json` | **New** — generated once during implementation |
| `tests/data/goldens/README.md` | **New** — one-paragraph pointer to `tests/README.md` |
| `tests/test_goldens.py` | **New** — essential golden regression test |
| `tests/README.md` | **New** — goldens rule + `essential` marker note |
| `.issueflows/04-designs-and-guides/testing-and-coverage.md` | One-line cross-link to `tests/README.md` goldens section |

## Test strategy

Implementation order:

1. Scaffold script + empty suite dir.
2. Run regen locally (requires `testdata/data/20160805_test001_45_cc_01.res` present).
3. Run `uv run python dev/regenerate_goldens.py --verify` twice → byte-identical.
4. `uv run pytest tests/test_goldens.py -v`
5. `uv run pytest -m essential --ignore=tests/test_plotutils_summary_plot.py` (matches CI Tier 1)

If `.res` testdata is absent in the implementer’s checkout, use an already-generated golden
from a machine with testdata, or temporarily copy from a known-good run — document in status.

## Open questions

1. **Toy suite source file** — plan uses the canonical Arbin `.res` (`fdv.res_file_path`) so
   the toy suite aligns with existing `essential` oracle numbers. Alternative: a smaller in-repo
   file (e.g. `maccor_001.txt`) for easier regen on machines without ODBC/mdbtools. **Recommend
   Arbin `.res`** for maximum alignment; regen remains dev-only.
2. **`--verify` in CI later?** — optional follow-up; not required to close #428.
3. **Durable design note** — add `golden-fixtures.md` under `04-designs-and-guides/` now vs
   defer to when #429 adds a second suite. **Recommend defer**; `tests/README.md` is enough for
   F8.

---

**Status**: ready for `/iflow-start` pending user confirmation.
