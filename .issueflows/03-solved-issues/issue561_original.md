# Issue #561: Stage 3.4: tier-3 loader decisions (biologics, batmo, ext_nda, local_instrument)

Source: https://github.com/jepegit/cellpy/issues/561

## Original issue text

## Goal

Execute the tier-3 loader decisions before 2.0 so no instrument is left in an undefined
state at release.

## Why

Tier-3 loaders (`biologics_mpr`, `batmo_bdf`, `ext_nda_reader`, `local_instrument`) are
the ones the loader plan flagged as needing a maintainer call rather than a mechanical
port. Shipping 2.0 with them silently half-working is worse than shipping them
documented as parked.

Plan: `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` tier-3 section.

## Decisions needed

- [x] `biologics_mpr` — port to declarations? (plan recommends yes)
- [x] `batmo_bdf` — port? (plan recommends yes)
- [x] `ext_nda_reader` — park with a clear "unsupported in 2.0" error and a pointer, or
      port? (plan recommends park)
- [x] `local_instrument` — confirm it stays one of the two sanctioned warn-only escape
      hatches (conventions plan §4).

## Acceptance

- Each decision recorded in the loader plan in the #438 decision-register style.
- Ported loaders pass `check_loader`; parked loaders raise a typed `LoaderError` naming
  the status and the workaround.
- 2.0 release notes list the supported-instrument matrix.


## Comments (curated summary)

- **Additional tasks**:
  - Close this issue once `biologics_mpr` and `batmo_bdf` ports land with the #560 arc (decisions already recorded).
- **Clarifications / constraints**:
  - `ext_nda_reader` already parked with typed `LoaderError` naming `instrument="neware_nda"` as replacement (#600); do not re-open that work.
  - `local_instrument` confirmed as sanctioned warn-only escape hatch (conventions plan §4); no code change.
  - Decision is *port* for `biologics_mpr` and `batmo_bdf`; execution rides with #560 (declarations + `check_loader` + goldens).
  - Supported-instrument matrix for release notes tracked on #572, not this issue.
  - Decisions recorded in `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` §2.5–2.6.
- **Superseded / retracted**:
  - The open "decisions needed" work in the body is superseded: all four decisions are settled; remaining work is verifying/closing after the two ports land.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-20._
