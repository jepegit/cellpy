# Issue #574 plan — Stage 3.17: cellpy 2.0.0 release checklist

**Status:** confirmed 2026-07-24 (Accept; Q2 override → `v2.0.0rc1`)

## Goal

Execute the **2.0.0 release gates** (benchmarks, parity, CI, docs/deps, Stage-3
close-out), align guiding docs, then **tag/publish** `v2.0.0rc1` from a clean
`master`. The stable `v2.0.0` cut and the formal start of the 12-month `v1.x`
bugfix-only window wait until a later follow-up after rc soak (still tracked
under this checklist / Stage 3 until closed).

## Constraints

- **Operational issue, not a feature.** Prefer evidence + tiny fixes over new
  abstractions. No new release framework.
- **Tag only from clean `master`** after the readiness PR merges — never from
  `574-release-checklist`. Follow
  [`.issueflows/04-designs-and-guides/release-procedure.md`](../04-designs-and-guides/release-procedure.md)
  (hygiene: no untracked `.issueflows/` on the tagged commit).
- **Branching:** `master` = v2; `v1.x` = 1.x maintenance
  ([`cellpy-v2-branching.md`](../04-designs-and-guides/cellpy-v2-branching.md)).
- **Acceptance bar** (release plan §4): no metric slower than 1.x; load/summary
  expected to win after bridge removal. CI harness today: warn +20% / fail +100%
  (`benchmarks/check_baseline.py` + `.github/workflows/benchmarks.yml`). Release
  judgment uses the plan bar; CI hard-fail is the floor.
- **`cellpycore` pin:** already `cellpycore==0.2.3` in `pyproject.toml`. Confirm
  it is still the intended release pin (core #136 closed; pin-gate doc
  [`v2-cellpycore-pin-gate.md`](../04-designs-and-guides/v2-cellpycore-pin-gate.md)
  is partly historical — refresh if stale).
- **Comment task:** check/update `.issueflows/04-designs-and-guides` so
  release/branching/pin/docs text matches reality at ship time.
- **Out of scope unless asked:** implementing #655 fixture inventory; cutting
  another `aN`/`rcN` if we choose to delay stable.

### Prior art

| Hit | Role |
| --- | --- |
| [`benchmarks/`](../../benchmarks/) + [`check_baseline.py`](../../benchmarks/check_baseline.py) + [`.github/workflows/benchmarks.yml`](../../.github/workflows/benchmarks.yml) | GHA ubuntu baseline compare (issue #436 / #476 tiered gate) |
| [`tests/parity.py`](../../tests/parity.py) + golden suites | Value-parity oracle; named `exceptions=` only |
| [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) jobs `essential (linux / uv)` / `full (linux / uv)` | Required CI gates named in the issue |
| [`.github/workflows/docs.yml`](../../.github/workflows/docs.yml) + RTD | Docs build signal |
| [`DEPRECATIONS.md`](../../DEPRECATIONS.md), [`docs/getting_started/migration_v1_to_v2.md`](../../docs/getting_started/migration_v1_to_v2.md) | #572 deliverables — verify complete, don't rewrite |
| [`release-procedure.md`](../04-designs-and-guides/release-procedure.md), [`build-and-versioning.md`](../04-designs-and-guides/build-and-versioning.md) | Tag → GitHub release → PyPI trusted publish |
| Sibling [`cellpy-feedstock`](../../../cellpy-feedstock/) | conda-forge follow-up after PyPI |
| `00-tools/` | None for release ops — no new helper unless audit invents a reusable checker |

## Approach

Three phases on this issue. **Phase A+B** = the PR. **Phase C** = post-merge
human release cut (same issue, not a second GitHub issue unless we abort ship).

### Phase A — Readiness audit (evidence first)

Record results in `issue574_status.md` (and tick the GitHub issue checkboxes when
green). Do not tag yet.

| Gate | How |
| --- | --- |
| Benchmarks | Dispatch **Benchmarks** workflow on `master` (or this branch once pushed); download/compare vs `benchmarks/baselines/v1x_ubuntu_py313.json`. Note load/summary deltas. Any warn-band (+20%) → investigate before ship (open Q). Fail-band (+100%) → hard blocker. |
| Value-parity | `uv run pytest` paths that exercise golden / parity oracles (full suite covers them; call out any intentional `exceptions=` list in status — no silent widen). |
| CI | Green `essential (linux / uv)` **and** `full (linux / uv)` on the PR (and on `master` before tag). Optionally kick `ci-scheduled` if weekly is stale. |
| Docs / deprecations | Confirm migration guide + `DEPRECATIONS.md` current; Docs workflow / RTD published for latest `master`. |
| Dependency budget / pin | Confirm #570 budget still true in `uv.lock`; keep or bump exact `cellpycore==…` for the release commit. |
| Stage-3 close-out | Only open `cellpy2-stage3` issues today: **#574** (this) and tracking **#575**. Architecture-plan “open” list is stale — refresh that note if we touch architecture-plan. Decide **#655** (open on `v2.0.0` milestone, not stage-3 label) — see Open questions. |
| Guiding docs | Diff `release-procedure.md`, `cellpy-v2-branching.md` “At v2.0 release”, `v2-cellpycore-pin-gate.md`, `ci-tiers.md` vs current truth; patch drift. |

### Phase B — Gap fixes + release notes prep

Only what audit proves necessary:

- Fix benchmark / parity / CI failures (minimal patches; new issues if large).
- `HISTORY.md`: fold Unreleased into **`## [2.0.0] - <date>`** (migration headlines,
  support matrix, v1.x 12-month window, pin).
- Architecture-plan / issue-flow doc sync as needed (comment task).
- PR → `master`. Keep `.issueflows/01-current-issues/*` **off** the merge if the
  project prefers (or leave on branch only — never pollute the tagged tree).

### Phase C — Ship rc1 (after merge, on clean `master`)

Per `release-procedure.md` §B (pre-release on `master`):

1. `git switch master && git pull --ff-only`
2. `git status` empty (no untracked)
3. `UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync` if pin/lock changed
4. `uv run pytest` (full) + confirm CI green
5. `gh release create v2.0.0rc1 --target master --generate-notes` (or curated notes)
6. Watch `release.yml` → PyPI (`--pre` channel)
7. Update **cellpy-feedstock** only if conda should carry the rc (optional; default
   = PyPI rc first, feedstock with stable later — see decisions)
8. Confirm `v1.x` tip remains healthy; **do not** start the 12-month EOL clock yet
   (clock starts at stable `v2.0.0`)
9. Leave #574 open until stable ship **or** explicitly park after rc1 with remaining
   work = “soak → re-run gates → `v2.0.0` + window announcement”

**Split recommendation:** keep Phases A–C on **one issue** (checklist nature), but
**two git moments** — readiness PR, then tag. If audit finds multi-day blockers,
pause (#655-sized work becomes its own issue; do not inflate this PR).

## Files to touch

| Path | Change |
| --- | --- |
| `.issueflows/01-current-issues/issue574_status.md` | Gate evidence, checkbox progress |
| `.issueflows/04-designs-and-guides/release-procedure.md` (and siblings as needed) | Align with ship reality |
| `HISTORY.md` | `[2.0.0rc1]` section (stable `[2.0.0]` later) |
| `pyproject.toml` / `uv.lock` | Only if pin bump required |
| `DEPRECATIONS.md` / migration guide | Only if audit finds gaps |
| `benchmarks/` or tests | Only if gate fails need a fix |
| `architecture-plan/*` (sibling) | Optional status-row refresh |
| `cellpy-feedstock/` (sibling) | Phase C version bump |

## Test strategy

- Local / PR: `uv run pytest -m essential`, then `uv run pytest` (full) before
  declaring CI gate ready.
- Benchmarks: GHA **Benchmarks** workflow + `check_baseline.py` (not local Windows
  numbers as ruler).
- Release: `release.yml` essential + publish after tag.
- No new unit tests unless a gap-fix introduces behaviour.

## Decisions (confirmed 2026-07-24)

1. **[#655](https://github.com/jepegit/cellpy/issues/655) does not block rc1 / 2.0** — follow-up fixture work; not a Stage-3 sub-issue.
2. **Cut `v2.0.0rc1` first** (user override). Stable `v2.0.0` + 12-month `v1.x` window after soak.
3. **Warn-band (+20%…+100%):** investigate; **block ship on unexplained load/summary warns**; other metrics may proceed if documented in status.
4. **Feedstock:** PyPI rc1 first; feedstock bump with **stable** (or only if we explicitly want conda `--pre`).
5. **Phase A on current `master` first** (benchmarks workflow + latest CI), then PR fixes on this branch.

## Open questions

- None remaining — proceed to `/iflow-build`.
