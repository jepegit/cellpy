# Issue #648: Add ica_plot / dva_plot families on the new pipeline

Source: https://github.com/jepegit/cellpy/issues/648

## Original issue text

## Context

Part of epic #567 (Stage 2 â€” Other plot families on the same skeleton). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. ICA redesign: #566 / migration notes.

## Scope

Register ICA/DVA figure families that consume the specced long frames from `cellpy.ica` (`dqdv` / `dvdq`). Implement prepare modules that do not re-invent the math. Public entry points `ica_plot` / `dva_plot` (names may live as `cellpy.plotting` exports and re-exports). Add corresponding cases to the figure-spec snapshot.

## Acceptance

- New oracle cases committed and green.
- Plots honour cell-centric `direction`.
- No dependency on deleted `Converter` / wide-frame helpers.

## Depends on

#647

Part of epic #567.
