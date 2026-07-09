# CI tiers

cellpy CI is split into a fast merge gate and a slower scheduled matrix.

## Tier 1 — merge gate (`ci.yml` → job `essential`)

**When:** pull requests and pushes to `master` (not feature-branch pushes).

**What:** Linux, `uv sync` with `UV_NO_SOURCES=1`, `pytest -m essential`, `cellpy info --check`.

**Branch protection:** require this job before merge.

**Contract:** anything that must block a merge belongs on the `essential` marker (or add it
when you discover a gap). See [`tests/README.md`](../../tests/README.md).

## Tier 2 — platform matrix (`ci-scheduled.yml`)

**When:** Mondays 03:00 UTC, or **Actions → CI (scheduled) → Run workflow**.

**What:** full conda pytest matrix (Linux / macOS-14 / Windows with ACE), pip-install
matrix, nbmake notebook (Linux, `continue-on-error`), conda-forge install check.

Failures are informational — fix on the next cycle; they do **not** block merges.

Run manually before a release if the weekly schedule is too stale.

## Release (`release.yml`)

**When:** GitHub release published.

**What:** tag validation → essential tests → PyPI publish (unchanged).

## Manual only

- `draft-pdf.yml` — JOSS paper PDF

## Skipped paths

Doc-only changes under `docs/`, `paper/`, `.issueflows/`, `graphify-out/`, and `*.md` do not trigger `ci.yml`.

## When to mark a test `essential`

Add `@pytest.mark.essential` when the test guards behaviour that every PR must preserve:

- read → step table → summary pipeline smoke,
- cellpy / cellpy-core parity contract,
- golden-fixture oracles under `tests/data/goldens/`,
- other regressions you cannot afford to discover only on Monday's scheduled run.

Keep the set small (~20 tests today) so Tier 1 stays fast. Platform-specific paths
(Windows ODBC, macOS-only skips) stay in the full suite unless you add a targeted
essential on that platform — which would require a separate job.
