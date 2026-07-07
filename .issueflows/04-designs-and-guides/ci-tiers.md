# CI tiers

cellpy CI is split into fast merge gates and a slower scheduled matrix.

## Tier 1 — merge gate (`ci.yml` → job `essential`)

**When:** pull requests and pushes to `master` (not feature-branch pushes).

**What:** Linux, `uv sync` with `UV_NO_SOURCES=1`, `pytest -m essential`, `cellpy info --check`.

**Branch protection:** require this job before merge.

## Tier 2 — platform smoke (`ci.yml` → conda jobs)

**When:** same triggers as Tier 1; runs only if `essential` passes.

**What:** conda pytest on Linux, macOS-14, and Windows (Access ODBC on Windows).

## Tier 3 — full matrix (`ci-scheduled.yml`)

**When:** Mondays 03:00 UTC, or **Actions → CI (scheduled) → Run workflow**.

**What:** full conda pytest matrix, pip-install matrix, nbmake notebook (Linux, `continue-on-error`), conda-forge install check.

Failures are informational — fix on the next cycle; they do not block merges.

## Release (`release.yml`)

**When:** GitHub release published.

**What:** tag validation → essential tests → PyPI publish (unchanged).

## Manual only

- `draft-pdf.yml` — JOSS paper PDF

## Skipped paths

Doc-only changes under `docs/`, `paper/`, `.issueflows/`, `graphify-out/`, and `*.md` do not trigger `ci.yml`.
