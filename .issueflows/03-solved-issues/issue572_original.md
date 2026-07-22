# Issue #572: Stage 3.15: 2.0 migration guide, release notes, complete DEPRECATIONS.md

Source: https://github.com/jepegit/cellpy/issues/572

## Original issue text

## Goal

Write the 2.0 migration guide and release notes — the document that tells a 1.x user
what changed and what to do about it.

## Why

2.0 changes frames (polars), column names (native schema), the file format (v9), the
config format (TOML), plotting entry points, and the instrument set. Every one of those
is survivable with a shim; none of them is survivable without being told.

Plan: `architecture-plan/cellpy2-release-and-branching-plan.md` §1;
`cellpy2-documentation-plan.md`; architecture plan §7.

## Scope

- [ ] Migration guide: pandas→polars frame idioms, `headers_*` → `c.schema`,
      `prms.*` → `cellpy.config`, v8 → v9 (`cellpy convert --to v9`), easyplot removal,
      plotting entry-point changes, ICA output-frame change.
- [ ] Support matrix: reads v8 + v9, writes v9, `save(cellpy_file_format="v8")` compat,
      v<8 via `cellpy convert` on 1.x.
- [ ] The v1.x maintenance window: **bugfix-only for 12 months from the 2.0 release
      date** (decision #438-6).
- [ ] Behavior-delta register (architecture plan §7, Δ1–Δ7) — every delta stated with
      its verdict, the CE inversion (Δ2) as the headline item.
- [ ] `DEPRECATIONS.md` complete and regenerated; every shim in the release registered
      with its 2.1 removal.

## Acceptance

- A 1.x script's failure modes each map to a named section in the guide.
- `DEPRECATIONS.md` regenerates with no diff.

## Comments (curated summary)

- **Additional tasks**:
  - Release notes must include the accumulated items from comments (do not reconstruct only from git log): Maccor/`#580` zero-capacity re-load, ICA redesign (`#566`), Typer/`cellpy convert` v9 default (`#569`), plotting Phase-0 fixes (`#593`/`#567`), dependency budget (`#570`), ICA direction cell-centric + unknown-column warn + Maccor Watt-hr energy (`#591`/`#560` decisions), loader-author `harmonize()` cast-empty raise + `duration_columns`.
  - Also fold in `#560` product bullets already recorded for this issue (harmonized-raw default, Arbin aux naming, datapoint preservation, `arbin_sql_h5` row retention) if not already covered when drafting.
  - Migration guide: pandas→polars, `headers_*` → `c.schema`, config TOML, v9 files, plotting entry points, instrument/dependency changes; convert-once hint for legacy HDF5 via `cellpy convert` + `[legacy-files]`.
  - Complete `DEPRECATIONS.md` for ICA removals listed in the `#566` note (and any other 2.0 removals).
- **Clarifications / constraints**:
  - Maccor txt / 2.0.0a5: saved `.cellpy` files can have **zeros baked in** — upgrade alone does not fix; re-load from raw. Only `maccor_txt` (`split_capacity: True`).
  - Plotting CV-split corruption on 2.0.0a5 was **in-memory only** (re-load cell; disk files OK) — unlike `#580`.
  - Conda keeps pytables; pip users need `cellpy[legacy-files]` for v4–v8 `.h5`.
  - ICA `direction` is **cell-centric** ("charge" = cell charging); anode batch ICA film labels flip once vs old electrode-centric labels.
  - **Do not** write a "re-load your neware data" note — oracle bugs were pre-flag-day only; neware capacities on 2.0.0a5 were correct.
  - Loader-author items (`harmonize` empty-cast raise, `duration_columns`) belong in a loader-authors section, not the end-user migration guide.
- **Superseded / retracted**:
  - Early `#566` note that ICA charge/discharge polarity was still open (`#591`) — resolved later: cell-centric direction landed.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 6, last comment by @jepegit on 2026-07-20._

