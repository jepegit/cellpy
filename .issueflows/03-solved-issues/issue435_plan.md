# Plan: issue #435 — Stage 0.8 consumer scans (filters / exporters / internals)

## Goal

Close gap **G5** by re-running the two Stage-0 inventory scans over `cellpy/filters/`,
`cellpy/exporters/`, and `cellpy/internals/` (Data/CellpyCell consumers only), then
append dated addenda to the existing reports and enrich the utils-migration triage table
for anything found in `exporters/`.

## Constraints

- **Documentation deliverable** — no production-code refactors in this issue; only scan
  tooling (optional but recommended) and report updates in `architecture-plan/`.
- **Match prior methodology** — same AST rules and classification buckets as
  [data-and-cellpycell-usage-in-cellpy-utils.md](../../architecture-plan/data-and-cellpycell-usage-in-cellpy-utils.md)
  and [hardcoded-column-headers-report.md](../../architecture-plan/hardcoded-column-headers-report.md)
  (receiver-aware member matching; header literals vs `internal_settings` canonical values;
  column-access context filtering; false-positive exclusions).
- **`internals/` scope** — issue text says *consumers only*; path/SSH helpers
  (`otherpath.py`, `connections.py`) are out of scope for the usage report unless they
  touch `Data` / `CellpyCell` (spot-check suggests they do not).
- **Plan docs live in** `architecture-plan/` (authoritative); issue tracked in
  `jepegit/cellpy`.
- **Half-day budget** — keep scanners minimal; manual spot-check is acceptable on this
  tiny surface (~6 `.py` files).

### Prior art

- [data-and-cellpycell-usage-in-cellpy-utils.md](../../architecture-plan/data-and-cellpycell-usage-in-cellpy-utils.md) — AST member-usage inventory for `utils/` only (2026-07-08); methodology to mirror.
- [hardcoded-column-headers-report.md](../../architecture-plan/hardcoded-column-headers-report.md) — whole-package AST header scan (2026-07-08); filters/exporters/internals were not broken out.
- [cellpy2-utils-migration-plan.md](../../architecture-plan/cellpy2-utils-migration-plan.md) — wave 0 already describes this scan; `exporters/*` row is **“Inventory then port/park”**; `filters/*` already **Port (wave 1)**.
- [pandas-to-polars-index-usage-report.md](../../architecture-plan/pandas-to-polars-index-usage-report.md) §2.12 — `filters/` mask pattern; §2.14 — `exporters/bdf.py` `reset_index`.
- `cellpy/filters/cycles.py` — generic DataFrame helper; default cycle column via `get_headers_normal()` (clean).
- `cellpy/filters/summary.py` — generic DataFrame helper; default `rate_columns=("charge_c_rate", "discharge_c_rate")` are hard-coded summary header names.
- `cellpy/exporters/bdf.py` — sole real `CellpyCell` consumer: `cell.data.raw`, `cell.data.raw_units`, `cell.headers_normal`, `cell.cell_name`; delegates cycle filter to `filter_cycles`.
- `cellpy/internals/{connections,otherpath}.py` — no `Data` / `CellpyCell` usage (negative finding expected).
- `.issueflows/00-tools/` — empty index; original scans were not committed as scripts.

## Approach

### 1. Add minimal, reproducible scanners (cellpy repo)

Write two small stdlib-AST scripts under `.issueflows/00-tools/` (no new dependencies):

| Script | Purpose |
| --- | --- |
| `scan_member_usage.py` | Extract `Data` / `CellpyCell` public API; walk `.py` trees; classify `.member` access by receiver (same exclusions as utils report: `logging`, `str`, plotly, etc.). |
| `scan_hardcoded_headers.py` | Load canonical header values from `cellpy.parameters.internal_settings`; AST-match string literals in column-access contexts; apply same verdict categories (fix / semi-OK / not a finding). |

CLI shape (keep simple):

```bash
uv run .issueflows/00-tools/scan_member_usage.py cellpy/filters cellpy/exporters cellpy/internals
uv run .issueflows/00-tools/scan_hardcoded_headers.py cellpy/filters cellpy/exporters cellpy/internals
```

Emit markdown fragments to stdout (or `-o` temp files) for paste into addenda. Register both in `00-tools/README.md`.

**Fallback:** if script time runs long, the surface is small enough to complete inventory manually with `rg` + AST spot-checks; still document methodology in the addendum footer.

### 2. Run scans and triage

**Packages scanned:**

| Package | Files | Expected usage-report headline |
| --- | --- | --- |
| `filters/` | `cycles.py`, `summary.py` | **No `CellpyCell` / `Data` access** — operates on caller-supplied DataFrames. Note dependency on canonical header names only via defaults. |
| `exporters/` | `bdf.py` (+ thin `__init__.py`) | **`CellpyCell` consumer** — `data.raw`, `data.raw_units`, `headers_normal`, `cell_name`; thin utils contract slice. |
| `internals/` | `connections.py`, `otherpath.py` | **No consumers** — document explicitly so G5 is closed. |

**Expected hardcoded-headers headline:**

- `filters/cycles.py` — clean (uses `get_headers_normal()`).
- `filters/summary.py` — default `rate_columns` tuple uses summary header literals → map to `HeadersSummary.charge_c_rate` / `.discharge_c_rate`.
- `exporters/bdf.py` — mostly attribute-driven via `headers_normal` + `_COLUMN_MAP` `cellpy_field` suffixes; verify no raw `df["voltage"]`-style literals slipped in; cross-check polars report lines 538/589 (`reset_index`).
- `internals/` — no column-header findings expected.

### 3. Append dated addenda (architecture-plan repo)

Add a section to each report (date **2026-07-10**, scope line naming the three packages):

**`data-and-cellpycell-usage-in-cellpy-utils.md`** — new **§9 Addendum: filters / exporters / internals**:

- Per-package summary table (mirror §4 style where useful).
- `exporters/bdf.py` member table: `cell_name`, `headers_normal`, `data.raw`, `data.raw_units` (and note `cellpy_units` appears only in docs — export converts from `raw_units`).
- Explicit “no usage” statement for `filters/` and `internals/`.
- Cross-link to utils contract §5 observations (filters stay generic; exporters are thin IO on raw).

**`hardcoded-column-headers-report.md`** — new **§9 Addendum** (or renumber if cleaner):

- Findings tables for `filters/summary.py` defaults and any `exporters/bdf.py` hits.
- Verdict + suggested `HeadersSummary` / `HeadersNormal` replacements.
- Note `internals/` clean.

### 4. Update utils-migration triage

In [cellpy2-utils-migration-plan.md](../../architecture-plan/cellpy2-utils-migration-plan.md) §2 table:

- Split or enrich `exporters/*` row → **`exporters/bdf.py` | Port (wave 1)** with notes from scan (depends on `data.raw`, `raw_units`, `headers_normal`, `filter_cycles`; BDF column map already header-attribute-based).
- Confirm `filters/cycles.py` + `filters/summary.py` rows stay **Port (wave 1)**; add one-line note that summary defaults need `HeadersSummary` at call sites or as defaults.

Mark wave 0 (**G5 scan**) as done in a short footnote under §3.

### 5. Verification

- Re-run scanners after writing; compare output to manual `rg` pass.
- Sanity-check addenda against acceptance criteria in `issue435_original.md`.
- No pytest required; optional smoke: scanners exit 0 on the three package paths.

## Files to touch

| Path | Change |
| --- | --- |
| `architecture-plan/data-and-cellpycell-usage-in-cellpy-utils.md` | Dated addendum §9 |
| `architecture-plan/hardcoded-column-headers-report.md` | Dated addendum |
| `architecture-plan/cellpy2-utils-migration-plan.md` | Enrich `exporters/` + `filters/` triage rows; wave-0 done note |
| `cellpy/.issueflows/00-tools/scan_member_usage.py` | New — reusable scanner |
| `cellpy/.issueflows/00-tools/scan_hardcoded_headers.py` | New — reusable scanner |
| `cellpy/.issueflows/00-tools/README.md` | Index entries for both tools |
| `cellpy/.issueflows/01-current-issues/issue435_status.md` | Created during `/iflow-start` (not this step) |

**Repos / PRs:** expect changes in **both** `jepegit/cellpy` (scanners + issue-flow) and `cellpy/architecture-plan` (reports). Can be one PR each or combined — see open question.

## Test strategy

- `uv run .issueflows/00-tools/scan_*.py …` — scanners run clean from `cellpy` root.
- Manual cross-check: `rg 'CellpyCell|\.data\.|get_headers' cellpy/{filters,exporters,internals}` matches usage addendum.
- No library test changes; documentation-only acceptance.

## Open questions

1. **PR split** — one PR per repo (recommended: cellpy scanners + architecture-plan docs) or single cross-repo PR? Issue is on `cellpy` but most user-visible diff is `architecture-plan`.
2. **Branch** — plan on `master` today (only `issue435_original.md` untracked). Create `435-extend-consumer-scans` before `/iflow-start`?
3. **Scanner permanence** — commit scripts to `00-tools` for future re-runs (recommended) vs one-off manual inventory? Plan assumes **commit**.
