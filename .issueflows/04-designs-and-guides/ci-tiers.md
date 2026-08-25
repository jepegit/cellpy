# CI tiers

cellpy CI is split into two Linux merge gates and a slower scheduled matrix.

## Tier 1 — essential merge gate (`ci.yml` → job `essential`)

**When:** pull requests and pushes to `master` (not feature-branch pushes).

**What:** Linux, `uv sync` with `UV_NO_SOURCES=1`, `pytest -m essential`, `cellpy info --check`.

**Branch protection:** require this job before merge.

**Contract:** anything that must block a merge belongs on the `essential` marker (or add it
when you discover a gap). See [`tests/README.md`](../../tests/README.md).

## Tier 2 — full Linux merge gate (`ci.yml` → job `full`)

**When:** pull requests and pushes to `master` (not feature-branch pushes).

**What:** Linux, `uv sync --extra batch` with `UV_NO_SOURCES=1`, full `pytest`.

**Branch protection:** require this job before merge.

## Tier 3 — platform matrix (`ci-scheduled.yml`)

**When:** Mondays 03:00 UTC, or **Actions → CI (scheduled) → Run workflow**.

**What:** full conda pytest matrix (Linux / macOS-14 / Windows with ACE), pip-install
matrix, nbmake notebook (Linux, `continue-on-error`), conda-forge install check.
Local day-to-day work stays on **uv**; do not run this conda matrix unless the
issue is specifically about conda install / those env files.

**Env constraints (issue #885):**
- `sqlalchemy-access` is Windows-only on conda-forge (`__win`). Keep it out of
  shared `github_actions_environment.yml` / `environment*.yml`; install on
  Windows runners (or local Windows) only.
- Scheduled `pip-install` uses `pip install -e ".[legacy-files]"` so Linux has
  PyTables for v4–v8 HDF5 fixtures; the batch plotting extra stays optional.

Failures are informational — fix on the next cycle; they do **not** block merges.

Run manually before a release if the weekly schedule is too stale.

## Release (`release.yml`)

**When:** GitHub release published.

**What:** tag validation → essential tests → PyPI publish (unchanged).

## Manual only

- `draft-pdf.yml` — JOSS paper PDF

## Paths

`ci.yml` runs its real checks for every PR targeting `master` and every push to
`master`, including doc-only changes. This keeps each required check name
unambiguous.

## When to mark a test `essential`

Add `@pytest.mark.essential` when the test guards behaviour that every PR must preserve:

- read → step table → summary pipeline smoke,
- cellpy / cellpy-core parity contract,
- golden-fixture oracles under `tests/data/goldens/`,
- other regressions you cannot afford to discover only on Monday's scheduled run.

Keep the set small (~20 tests today) so Tier 1 stays fast. Platform-specific paths
(Windows ODBC, macOS-only skips) stay in the full suite unless you add a targeted
essential on that platform — which would require a separate job.
