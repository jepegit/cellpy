# Issue #646: Port cycles_plot to prepare→spec→render

Source: https://github.com/jepegit/cellpy/issues/646

## Original issue text

## Context

Part of epic #567 (Stage 2 — Other plot families on the same skeleton). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`.

## Scope

Add `prepare/curves.py` (voltage–capacity; prefer `cellpycore.curves` output, with fallback to `c.get_cap` if needed — same trick as the validation notebooks). Route `cycles_plot` through registry/spec/backends. Collapse `x_range`/`y_range` vs `xlim`/`ylim` to one spelling; keep the other as `warn_once` aliases in `DEPRECATIONS.md`.

## Acceptance

- `cycles_plot` oracle cases green both backends.
- Deprecated range kwargs warn and behave identically.
- No private layout fork left inside `cycles_plot`.

## Depends on

#639

Part of epic #567.
