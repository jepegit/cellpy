# Issue #561 — status

- [x] Done

## What's done

- Plan accepted (2026-07-22): close-out + essential `check_loader` for
  `biologics_mpr` / `batmo_bdf`; matrix stays on #572; do not close #560 here.
- Fast-forwarded `561-tier3-loader-decisions` onto `origin/master`.
- Verified on master: ports (#619 / #623), park (#600), architecture-plan §2.6,
  `local_instrument` confirmed (no code).
- Added `tests/test_tier3_check_loader.py` — essential adapters that drive the
  real `parse` → `declarations` → `harmonize` path through `check_loader`.
  - Adapters needed: `AtomicLoad.name` collides with InstrumentLoader `name`;
    `harmonize` keeps intentional passthrough (`date_time` shim + unmapped
    legacy headers), so the adapter projects to the native schema before the
    kit's `check_raw_frame`.
- Tiny biologics init: set `_parsed = False` so declarations-before-parse is
  deterministic on a fresh instance.
- Essential suite green (`uv run pytest -m essential`).
- `HISTORY.md` Unreleased bullet; close via `/iflow-close`.

## Remaining work

- None for #561. Matrix / release notes stay on #572. Optional follow-ups:
  drop passthrough when cellpy-core maps those headers / `date_time` window
  ends; rename AtomicLoad path property so loaders can declare InstrumentLoader
  metadata directly.
