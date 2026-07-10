# Plan: issue #439 — Stage 0 exit audit (tracking close)

## Goal

Confirm Stage 0 is complete: all linked cellpy issues (#428–#438) done, exit criteria
verified on current `master`, and only **cellpy-core#114** remains — then close #439
(or document the single cross-repo blocker if #114 is not ready).

## Constraints

- **Audit-first** — this issue is verification and tracking, not new Stage 0 feature work.
- **cellpy repo scope** — #114 lives in `cellpy-core`; hand off via separate init/plan there
  unless user wants one umbrella PR comment only.
- **No behavior changes** unless verification finds a regression (fix → separate issue).
- **Plan docs** — update `architecture-plan/stage0-github-issues.md` status when audit completes
  (PR to `cellpy/architecture-plan`).

### Prior art

| Hit | Use |
|-----|-----|
| `.issueflows/01-current-issues/issue439_status.md` | Linked-issue table started in `/iflow-init` |
| `.issueflows/03-solved-issues/issue438_status.md` | Six decisions recorded; PR architecture-plan #1 |
| `architecture-plan/stage0-github-issues.md` | Stage 0 index; status section stale (428–431 only) |
| `dev/regenerate_goldens.py` | Golden verify/regen (`--verify`) |
| `benchmarks/` + `.github/workflows/benchmarks.yml` | Baseline harness (#436) |
| `tests/parity.py` / `tests/test_*parity*` | Value-parity oracle (#434) |
| `gh issue view 428..438` | GitHub closed state (already: all closed) |

## Approach

### 1. Linked issues (GitHub state) — already green

All **jepegit/cellpy#428–#438** are **CLOSED** on GitHub (verified 2026-07-10).

**Open:** [cellpy/cellpy-core#114](https://github.com/cellpy/cellpy-core/issues/114) only.

### 2. Exit-criteria verification pass (on `master`)

Run from `cellpy/` on updated `master` (branch `439-stage0-audit` for any doc-only edits):

| Criterion | Command / check | Expected |
|-----------|-----------------|----------|
| Essential suites green | `conda activate cellpy_dev_313 && pytest -m essential --ignore=tests/test_plotutils_summary_plot.py` | All pass (note any pre-existing flakes, e.g. `loader_pec_csv` datetime) |
| Goldens deterministic | `uv run python dev/regenerate_goldens.py --verify` (or documented subset) | Exit 0 |
| Benchmark baselines committed | `test -f benchmarks/baselines/v1x_ubuntu_py313.json` + CI Benchmarks green on master | Present; GHA success |
| Value-parity trivial pass | `pytest tests/ -k parity -m essential` (or module named in #434) | Green on bridge |
| #438 decisions in plans | Spot-check six decision notes in `architecture-plan/` (per issue438_status) | Present (2026-07-10) |

Record pass/fail in `issue439_status.md` with dates and command output summary.

### 3. Documentation updates

1. **`architecture-plan/stage0-github-issues.md`** — replace stale “428–431 closed” blurb with:
   - `#428–#438` closed
   - `#114` open (Stage 0.12)
   - `#439` ready to close when #114 done (or closed with explicit blocker note — see open question)
2. **`issue439_status.md`** — fill exit-criteria checkboxes from step 2.
3. **GitHub #439** — post audit summary comment; check off child issues in body if desired (`gh issue edit`).

### 4. Close #439

**If #114 still open (expected now):**

- Option A *(recommended)*: Close #439 with comment “cellpy Stage 0 complete; #114 tracked separately” **only if** user accepts umbrella ≠ every linked issue closed.
- Option B *(strict)*: Leave #439 **open**, status `- [ ] Done`, blocker = #114; `/iflow-pause` to `02-partly-solved-issues`.

**If #114 closes first:** `/iflow-close` #439 on cellpy — move files to `03-solved-issues`, close GitHub issue.

## Files to touch

| Path | Change |
|------|--------|
| `.issueflows/01-current-issues/issue439_status.md` | Audit results + Done checkbox when resolved |
| `architecture-plan/stage0-github-issues.md` | Refresh Stage 0 status table/footnote |
| GitHub #439 | Summary comment; optional body checkbox updates |
| `cellpy-core` | **Separate** — `/iflow-init 114` in that repo for doc-sync work |

No application code unless verification fails.

## Test strategy

```bash
conda activate cellpy_dev_313
pytest -m essential --ignore=tests/test_plotutils_summary_plot.py
uv run python dev/regenerate_goldens.py --verify
pytest tests/test_cellpy_file_roundtrip.py tests/test_loader_goldens.py tests/test_goldens.py -q
# parity: pytest tests/ -k "parity" -v
```

CI on `master` already green for **CI** and **Benchmarks** (2026-07-10).

## Open questions

1. **Close #439 with #114 still open?** Strict reading of “all linked issues” → **no** (Option B). Pragmatic “cellpy Stage 0 done” → **yes** with blocker note (Option A). **Recommend Option B** until #114 closes, unless you want the umbrella closed now.
2. **Who owns #114?** Work happens in `cellpy-core` checkout — init there next, not on this branch.

## Recommended next steps after Accept

1. `git switch master && git pull && git switch -c 439-stage0-audit`
2. `/iflow-start` — run verification commands, update status + `stage0-github-issues.md`
3. `/iflow-init 114` in **cellpy-core** (or `/iflow-pick`) for the last linked issue
4. `/iflow-close` #439 when policy in open question #1 is resolved
