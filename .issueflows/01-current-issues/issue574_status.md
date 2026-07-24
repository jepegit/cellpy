# Issue #574 status

- [ ] Done

## Done so far

- Plan confirmed: ship **`v2.0.0rc1`** first; #655 non-blocking; feedstock with stable; audit `master` first.
- **Phase A audit (master @ #667 / 2026-07-24):**
  - CI run [30084328653](https://github.com/jepegit/cellpy/actions/runs/30084328653): `essential (linux / uv)` ✅ · `full (linux / uv)` ✅
  - Docs run [30084328614](https://github.com/jepegit/cellpy/actions/runs/30084328614): `build (zensical)` ✅
  - Benchmarks run [30084328804](https://github.com/jepegit/cellpy/actions/runs/30084328804): compare job ✅ (fail-band clear)
  - Pin: `cellpycore==0.2.3` in `pyproject.toml` / `uv.lock`; core #136 closed
  - Stage-3 open: only #574 + tracking #575
  - Migration guide + `DEPRECATIONS.md` present (#572)
  - Dependency budget (#570): box/ruamel/dotenv out; `tables` behind `legacy-files`; polars/pyarrow/pydantic-settings/platformdirs in
- **Benchmark warn-band (load paths) — explained for rc1:**
  - Latest master: `single_cell_pipeline` **+25.2%** (0.160s vs 0.128s); `v8_cellpy_file_load` **+22.7%** (0.089s vs 0.073s)
  - Intermittent: same day run [30053511478](https://github.com/jepegit/cellpy/actions/runs/30053511478) had **no** +20% warns; other runs warn at +21–32%
  - Suite uses `benchmark.pedantic(..., iterations=1)` → single-round GHA noise; batch summary / `get_cap` stay in band
  - Fail-band (+100%) never hit; release plan “investigate load/summary” noted — not a silent ignore
- **Phase B doc sync (this branch):**
  - `v2-cellpycore-pin-gate.md` → satisfied / `==0.2.3`
  - `cellpy-v2-branching.md` “At v2.0 release” → rc1 soak + stable + window timing
  - `release-procedure.md` → rc1 example + extra gates
  - `this-project.md` → tag example `v2.0.0rc1`

## Remaining work

- [x] User accepted warn explanation for **rc1** (2026-07-24)
- [x] Readiness PR: https://github.com/jepegit/cellpy/pull/671 (`Refs #574`)
- [ ] `/iflow-close` (owns `HISTORY.md` `[2.0.0rc1]` bullet)
- [ ] Phase C after merge: clean `master` → `gh release create v2.0.0rc1 --target master`
- [ ] Later: soak → re-audit → stable `v2.0.0` + feedstock + start 12-month `v1.x` window

## Gate checklist (issue body)

- [x] Benchmarks vs GHA v1.x baselines: fail-band clear; load/summary warn intermittent — documented
- [x] Value-parity: covered by green `full (linux / uv)` on master (incl. golden/parity suites)
- [x] Full CI: `essential` + `full` green on master
- [x] `DEPRECATIONS.md` + migration guide present
- [x] Dependency budget applied; `cellpycore==0.2.3`
- [x] Docs build green (zensical)
- [x] Every other Stage-3 sub-issue closed (#655 deferred)
- [ ] Tag `v2.0.0rc1` + PyPI (Phase C)
- [ ] Stable `v2.0.0` / feedstock / v1.x window (post-rc)
