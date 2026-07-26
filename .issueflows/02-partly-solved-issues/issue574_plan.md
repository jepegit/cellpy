# Issue #574 plan — Stage 3.17: cellpy 2.0.0 release checklist

**Status:** draft 2026-07-26 (supersedes 2026-07-24 confirmed rc1 plan — Phases A–C done)

## Goal

Re-run the **2.0.0 release gates** on current `master`, fold release notes, then
**tag/publish stable `v2.0.0`** from a clean `master`, bump **conda-forge
feedstock**, and **start the 12-month `v1.x` bugfix-only window** (#438-6).
Close #574 / update #575 when done.

## Constraints

- **Operational issue, not a feature.** Evidence + tiny fixes only. No new
  release framework.
- **Tag only from clean `master`** — never from `574-release-checklist`. Follow
  [`release-procedure.md`](../04-designs-and-guides/release-procedure.md)
  (hygiene: no untracked `.issueflows/` on the tagged commit).
- **Branching:** `master` = v2; `v1.x` = 1.x maintenance
  ([`cellpy-v2-branching.md`](../04-designs-and-guides/cellpy-v2-branching.md)
  “At v2.0 release”).
- **Acceptance bar** (release plan §4): no metric slower than 1.x; load/summary
  expected to win. CI harness: warn +20% / fail +100%. Fail-band = hard blocker;
  unexplained load/summary warn-band = block (same as rc1 decision).
- **`cellpycore` pin:** currently `cellpycore==0.2.4` — confirm still intended
  for stable (do not silently bump during this cut unless a gate forces it).
- **Already shipped (do not redo):** `v2.0.0rc1` (2026-07-24), `v2.0.0rc2`
  (2026-07-25; publish workflow green). Note: GitHub marks `v2.0.0rc2` as
  *not* prerelease — fix that flag if still wrong, or leave a status note.
- **#655** still non-blocking (rc1 decision stands).
- **Out of scope unless decided in Open questions:** implementing #687 / #691
  as part of this issue (open separate issues or park stable until they land).

### Prior art

| Hit | Role |
| --- | --- |
| [`benchmarks/`](../../benchmarks/) + [`check_baseline.py`](../../benchmarks/check_baseline.py) + [`.github/workflows/benchmarks.yml`](../../.github/workflows/benchmarks.yml) | GHA baseline compare |
| [`tests/parity.py`](../../tests/parity.py) + golden suites | Value-parity oracle |
| [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) `essential` / `full` | Named CI gates |
| [`.github/workflows/docs.yml`](../../.github/workflows/docs.yml) + RTD | Docs signal |
| [`DEPRECATIONS.md`](../../DEPRECATIONS.md), [`docs/getting_started/migration_v1_to_v2.md`](../../docs/getting_started/migration_v1_to_v2.md) | Verify complete |
| [`release-procedure.md`](../04-designs-and-guides/release-procedure.md) §B | Tag → release.yml → PyPI |
| Sibling [`cellpy-feedstock`](../../../cellpy-feedstock/) | conda-forge after PyPI stable |
| `00-tools/` | None for release ops |

## Approach

**Phases A–C (rc soak path) — DONE** (see `issue574_status.md`). This plan is
**Phase D only**.

### Phase D — Stable `v2.0.0`

Two git moments again: optional readiness PR (HISTORY / docs / tiny gate fixes),
then tag from clean `master`.

#### D1 — Re-audit gates on current `master`

Record in `issue574_status.md`. Do not tag until green.

| Gate | How |
| --- | --- |
| CI | Wait for in-flight / latest `master` CI after #692; require green `essential (linux / uv)` **and** `full (linux / uv)`. |
| Benchmarks | Latest **Benchmarks** on `master` (post-#692 already ran success once — confirm fail-band still clean; note load/summary warn vs rc1). |
| Value-parity | Covered by full suite; call out any intentional `exceptions=` — no silent widen. |
| Docs / deprecations | Migration guide + `DEPRECATIONS.md` still current; Docs/RTD ok for tip. |
| Pin / lock | Confirm `cellpycore==0.2.4` + lock; no surprise editable sources. |
| Stage-3 close-out | Only open `cellpy2-stage3`: **#574**, **#575**. After stable, close #574 and tick #575. |
| Guiding docs | Tick [`cellpy-v2-branching.md`](../04-designs-and-guides/cellpy-v2-branching.md) “At v2.0 release”; refresh `release-procedure.md` dates/examples if stale (`rc1` → stable wording). |

#### D2 — Release notes + readiness PR (if needed)

- `HISTORY.md`: fold `[Unreleased]` into **`## [2.0.0] - <date>`** (migration
  headlines, support matrix, **v1.x 12-month window from this date**, pin).
  Optionally backfill short `[2.0.0rc1]` / `[2.0.0rc2]` stubs if we want the
  soak trail in HISTORY (nice-to-have, not a gate).
- Only minimal patches if D1 finds blockers.
- PR → `master`. Keep `.issueflows/01-current-issues/*` **off** the merge /
  tagged tree.

#### D3 — Tag stable + feedstock + window

On clean `master` after D2 merges (or immediately if D1 green and no HISTORY PR
required — prefer HISTORY PR first):

1. `git switch master && git pull --ff-only`
2. `git status` empty (no untracked)
3. `uv run pytest` (full) locally if any last-minute commit; else rely on green CI
4. `gh release create v2.0.0 --target master` (curated or `--generate-notes`;
   ensure **not** marked prerelease)
5. Watch `release.yml` → PyPI **stable** channel
6. Bump sibling **cellpy-feedstock** to `2.0.0` (stable only — prior decision)
7. Confirm `v1.x` tip healthy; **announce 12-month bugfix-only window from
   today's date** (#438-6) in release notes + tick branching checklist
8. Close #574; update tracking #575

**Split:** keep Phase D on this one checklist issue. If D1 surfaces multi-day
blockers (#687-sized), **pause** and open/fix that issue — do not inflate the
release PR.

## Files to touch

| Path | Change |
| --- | --- |
| `.issueflows/01-current-issues/issue574_status.md` | D1 evidence, ship log |
| `HISTORY.md` | `[2.0.0]` section from Unreleased |
| `.issueflows/04-designs-and-guides/release-procedure.md` (+ branching checklist ticks) | Align with stable ship |
| `pyproject.toml` / `uv.lock` | Only if pin forced |
| `DEPRECATIONS.md` / migration guide | Only if audit finds gaps |
| `cellpy-feedstock/` (sibling) | Phase D3 version bump |
| `architecture-plan/*` (sibling) | Optional status-row refresh |

## Test strategy

- Before tag: green GHA `essential` + `full` on `master`; Benchmarks fail-band clean.
- Local optional: `uv run pytest -m essential` then `uv run pytest`.
- Release: `release.yml` essential + publish after `v2.0.0` tag.
- No new unit tests unless a gap-fix introduces behaviour.

## Decisions carried forward (from 2026-07-24)

1. **#655** does not block 2.0.
2. Warn-band: block ship on unexplained **load/summary** warns; other metrics may proceed if documented.
3. Feedstock with **stable** only (not rc).

## Open questions

1. **Ship now?** Treat soak as done after rc1+rc2 (~2 days) and cut `v2.0.0` this session, or wait longer?
2. **#687 (`scp://` SSH Host aliases)** — block stable, or ship with documented workaround (full HostName + `CELLPY_KEY_FILENAME`) and fix in a fast follow-up?
3. **#691 (project-scoped filefinder)** — confirm non-blocking (enhancement).
