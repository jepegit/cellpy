# Issue #572 — plan

## Goal

Finish the Stage 3.15 docs package so a 1.x (and 2.0 alpha) user can find
every user-visible break, what to do about it, and the deprecation schedule:
expand [`docs/getting_started/migration_v1_to_v2.md`](../../../docs/getting_started/migration_v1_to_v2.md),
land the accumulated release-note bullets (issue comments + `#560` status),
and keep [`DEPRECATIONS.md`](../../../DEPRECATIONS.md) regenerating with no
diff.

## Constraints

- Docs-only for product code. Prefer editing existing pages over new evergreen
  guides (docs plan: migration stays the bridge page).
- Release notes live in [`HISTORY.md`](../../../HISTORY.md) (Keep a Changelog);
  GitHub Release body for the final `v2.0.0` tag is `#574`, not this issue —
  but `#572` must leave HISTORY / migration text that `#574` can paste.
- Comment constraints are binding: **no** "re-load your neware" note; Maccor
  zeros and CV-split plot corruption are distinct (disk vs in-memory); loader-
  author items stay out of the end-user guide.
- `DEPRECATIONS.md` is generated: `uv run python -m cellpy._deprecation`;
  acceptance is `tests/test_deprecation_conventions.py::test_deprecations_md_matches_renderer`.
  Do not hand-edit the table body except via registry code.
- Tell the truth about **current `master`**: many 2.0 seams are in; full polars
  frame flip may still be incomplete — the guide must not claim APIs that are
  not shipped. Prefer "today on 2.0 alphas / master" + forward pointers over
  aspirational prose.
- Scope is large; keep one issue but **phase the PR** (below). Splitting into
  sub-issues remains available (Phase B of #63) if Δ-register sign-off stalls.

### Prior art

- [`docs/getting_started/migration_v1_to_v2.md`](../../../docs/getting_started/migration_v1_to_v2.md)
  — exists (file format, meta, campaign merge, easyplot, `get_cap` rename).
  **Expand in place** (do not fork a second guide).
- [`docs/other/header_migration_map.md`](../../../docs/other/header_migration_map.md)
  — column map; **link** from migration guide, do not duplicate wholesale.
- [`docs/getting_started/configuration.md`](../../../docs/getting_started/configuration.md)
  / [`configuration_reference.md`](../../../docs/getting_started/configuration_reference.md)
  — config/TOML; migration should point here for `prms` → `cellpy.config`.
- [`docs/other/writing_a_loader_plugin.md`](../../../docs/other/writing_a_loader_plugin.md)
  — natural home for loader-author `harmonize` / `duration_columns` notes.
- [`DEPRECATIONS.md`](../../../DEPRECATIONS.md) + `cellpy._deprecation` — ICA
  shims already registered; **regen currently matches** (`match` on 2026-07-22).
- [`HISTORY.md`](../../../HISTORY.md) — changelog; many 2.0a items already under
  `[2.0.0a6]` / Unreleased; fold missing comment bullets without duplicating.
- Architecture [`§7` delta register](../../../repos/architecture-plan/cellpy2-architecture-plan.md)
  (sibling `architecture-plan/`) — Δ1–Δ7; release plan §1 support matrix +
  12-month v1.x window (`#438-6`).
- Issue comments (curated in `issue572_original.md`) +
  [`issue560_status.md`](../03-solved-issues/issue560_status.md) "Release-note
  bullets for #572".
- Toolbox / graphify: nothing documentation-specific. **None found** beyond
  the above.

## Approach

### Phase A — Migration guide skeleton (researcher path)

Expand `migration_v1_to_v2.md` into named sections that map 1.x failure modes
to fixes (acceptance: each common break has a heading):

1. **Support & maintenance** — reads v8+v9, writes v9, `save(…="v8")` /
   `.h5` escape; v<8 via convert-on-1.x; **bugfix-only v1.x for 12 months
   from 2.0 GA** (replace vague "July 2027" with the rule from `#438-6`).
2. **Frames & headers** — link header map; `headers_*` → `c.schema` (shim
   until 2.1); state honestly whether user frames are still pandas on current
   alphas or already polars (verify against code before writing).
3. **Config** — `prms.*` → `cellpy.config` / TOML; link configuration pages;
   note import-time I/O removed.
4. **Files** — keep/strengthen v8↔v9 + `cellpy convert`; pip
   `[legacy-files]` vs conda pytables (`#570`).
5. **Plotting** — easyplot gone; `plotutils` / collectors; `get_cap` column
   rename; Phase-0 alpha fixes (`#593`).
6. **ICA** — new long frame; cell-centric `direction`; deprecations →
   `DEPRECATIONS.md`; anode label flip (`#591`).
7. **If you used 2.0.0a5** — Maccor baked zeros (re-load raw); CV-split
   in-memory corruption (re-load cell); plotting KeyErrors fixed; **explicitly
   exclude neware re-load**.
8. **Behavior deltas (Δ1–Δ7)** — table with verdict + where documented; only
   rows with a known verdict get firm language (see Open questions).

### Phase B — Release-note ledger → HISTORY

Walk issue comments + `#560` bullets; for each item either (a) already in
`HISTORY.md` → skip, or (b) add a crisp Unreleased / upcoming-2.0 bullet.
Keep user-facing vs loader-author separated (loader-author → short subsection
in `writing_a_loader_plugin.md` or a linked "Loader authors" appendix in the
migration guide).

### Phase C — DEPRECATIONS completeness

1. `uv run python -m cellpy._deprecation` and confirm no diff.
2. Grep for shims / `warn_once` / deprecated public names not in the table;
   register any missing **in code** (`cellpy._deprecation` seed), regen, commit
   both.
3. Ensure ICA list from `#566` is present (already looks complete).

### Phase D — Cross-links & smoke

- Nav already has Migration under getting_started (`zensical.toml`) — verify
  links from install/config/history pages.
- No docs build gate required beyond link sanity; optional local zensical
  build if cheap.
- Essential pytest still green (deprecation test covers regen).

## Files to touch

| Path | Change |
|------|--------|
| `docs/getting_started/migration_v1_to_v2.md` | Major expand (Phases A, parts of B) |
| `HISTORY.md` | Missing release-note bullets (Phase B) |
| `docs/other/writing_a_loader_plugin.md` | Loader-author notes (optional short section) |
| `cellpy/_deprecation.py` (or seed site) | Only if a shim is missing from the registry |
| `DEPRECATIONS.md` | Regen only if registry changes |
| `.issueflows/01-current-issues/issue572_status.md` | Living status during `/iflow-start` |

Likely **no** change to `docs/other/header_migration_map.md` beyond inbound
links.

## Test strategy

- `uv run python -c "…"` / `uv run python -m cellpy._deprecation` — no diff
- `uv run pytest tests/test_deprecation_conventions.py -q`
- `uv run pytest -m essential` (ignore known host `pyodbc` collection if needed)
- Manual: every checklist item in the issue Scope maps to a migration heading
  or an explicit "deferred / N/A on current master" note in status

## Open questions

1. **Δ1–Δ7 verdicts** — architecture §7 still reads as "decide". Ship the
   migration table with **TBD / see architecture §7** for unsigned rows, or
   pause Phase A§8 until you sign them off here? **Recommended:** document
   signed facts only; leave unsigned rows as "under review before 2.0 GA"
   pointing at `#574` / architecture §7 so this issue is not blocked.
2. **Polars wording** — verify on start whether user-facing frames are still
   pandas. If yes, migration says "native headers now; polars frame swap is
   the remaining flag-day — follow HISTORY when it lands" rather than teaching
   polars idioms that are not live.
3. **One PR vs stacked** — **Recommended:** one PR with Phase A+B+C; if Δ
   sign-off or polars wording balloons, land A+B+C without a firm Δ table and
   open a tiny follow-up rather than splitting the whole issue preemptively.
