# Issue #594 — plan

## Goal

Stop excluding `tests/test_plotutils_summary_plot.py` from the scheduled Tier-3
matrix, and run those jobs with `MPLBACKEND=Agg` so nightly catches platform
plotting regressions the same way Tier-1 / release already do (#593 / #567 Phase 0).

## Constraints

- Match the pattern already used in [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml)
  and [`.github/workflows/release.yml`](../../../.github/workflows/release.yml):
  no file `--ignore`, `MPLBACKEND: Agg` on the pytest step/job.
- Do **not** add a blanket file exclusion again. If a platform fails after the
  first observed run, use a targeted `skipif` (or fix the bug) — not matrix
  `pytest-args` ignore.
- Tier-3 may lack the `batch` extra: plotly/seaborn cases already
  `skipif` when missing; that is acceptable (issue text).
- Scheduled failures do not block merges ([`ci-tiers.md`](../04-designs-and-guides/ci-tiers.md));
  still prefer a green first run if cheap to fix.
- Scope: workflow + stale CI docs only. No plotting redesign (#567).

### Prior art

- [`ci.yml`](../../../.github/workflows/ci.yml) essential + full jobs — comments
  document why the ignore was removed; `MPLBACKEND: Agg` env. **Mirror.**
- [`release.yml`](../../../.github/workflows/release.yml) — same Agg env. **Mirror.**
- [`tests/test_plotutils_summary_plot.py`](../../../tests/test_plotutils_summary_plot.py)
  — sets `matplotlib.use("Agg")` at import; `skipif` on missing plotly/seaborn.
  **Coexist** (workflow Agg is belt-and-suspenders for other matplotlib imports).
- [`ci-tiers.md`](../04-designs-and-guides/ci-tiers.md) — Tier-2 = `ci-scheduled.yml`.
  **Update** only if wording still implies the old ignore.
- [`testing-and-coverage.md`](../04-designs-and-guides/testing-and-coverage.md) —
  still says "CI additionally `--ignore=…summary_plot`". **Update** (stale).
- Toolbox (`00-tools/`): nothing CI-related. Graphify: absent.
- `github_actions_environment.yml`: has `matplotlib` + `plotly`, **no** `seaborn`
  → seaborn classes skip on conda-pytest; plotly runs. Leave as-is unless we
  decide otherwise in Open questions.

## Approach

1. **Edit [`ci-scheduled.yml`](../../../.github/workflows/ci-scheduled.yml)**
   - `conda-pytest` matrix (3 rows): drop
     `--ignore=tests/test_plotutils_summary_plot.py` from every `pytest-args`.
     Keep the macOS `-m "not slowtest and …"` filter as the sole macos args.
     Linux/Windows can use empty `pytest-args` (or omit the ignore-only value).
   - `pip-install` matrix: drop the ignore from linux + macos-14 rows
     (windows stays `tests/test_maccor.py` only — unchanged).
   - Set `env: MPLBACKEND: Agg` on `conda-pytest` and `pip-install` jobs
     (job-level is enough for all pytest steps).
2. **Docs hygiene (same PR)** — fix the stale ignore claim in
   `testing-and-coverage.md`; skim `ci-tiers.md` / `tests/README.md` for the
   same leftover and correct if present.
3. **Local check** — run
   `MPLBACKEND=Agg uv run pytest tests/test_plotutils_summary_plot.py -q`
   (and essential gate) before close. Full OS matrix is GHA-only.
4. **Post-merge observation** — after merge, dispatch
   `CI (scheduled)` once (`gh workflow run "CI (scheduled)"` or Actions UI),
   watch the matrix, and file/fix any real platform failures with targeted
   skips. That satisfies the issue's "one nightly run observed" acceptance;
   do not block the PR on a full weekly wait.

## Files to touch

| Path | Change |
|------|--------|
| `.github/workflows/ci-scheduled.yml` | Remove 5× `--ignore=…summary_plot`; add `MPLBACKEND: Agg` on `conda-pytest` + `pip-install` |
| `.issueflows/04-designs-and-guides/testing-and-coverage.md` | Drop/replace stale "CI `--ignore=summary_plot`" note |
| `.issueflows/04-designs-and-guides/ci-tiers.md` | Only if it still implies the ignore (likely no edit) |
| `tests/README.md` | Only if it still documents the scheduled ignore |

## Test strategy

- Local: `MPLBACKEND=Agg uv run pytest tests/test_plotutils_summary_plot.py -q`
- Local gate: `uv run pytest -m essential` (ignore known host `pyodbc` collection
  error on `test_arbin_variants_two_stage` if it still appears)
- GHA: PR does not run `ci-scheduled.yml` automatically — rely on post-merge
  `workflow_dispatch` for matrix observation

## Open questions

1. **Seaborn on conda Tier-3?** Env has plotly but not seaborn, so seaborn cases
   will `skipif` on `conda-pytest`. **Recommended:** leave out of this issue
   (matches "skip cleanly"); add seaborn in a follow-up if we want those cases
   on the weekly matrix.
2. **Dispatch before merge?** We can `gh workflow run` against this branch only
   if the workflow file on `master` already supports it meaningfully — the
   ignore removal lives on this branch, so observation is **after merge**.
   OK?
