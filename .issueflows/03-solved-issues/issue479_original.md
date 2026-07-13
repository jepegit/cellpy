# Issue #479: Stage 1.18: Deprecate utils/easyplot on v1.x (decision #438-5)

Source: https://github.com/jepegit/cellpy/issues/479

## Original issue text

> Follow-up mandated by the Stage-0 decision register (#438, decision 5) and the
> Stage-1 tracking issue (#459). Plans: `cellpy-workspace/architecture-plan/`
> ([repo](https://github.com/cellpy/architecture-plan)).

## Goal

Deprecate `cellpy/utils/easyplot.py` on the v1.x line: emit a module-level
`DeprecationWarning` on import via the Stage-0 conventions helper
(`cellpy._deprecation.warn_once`, registered in `DEPRECATIONS.md`), pointing users to
`plotutils`/`collectors` as the replacement. No functional changes to the module.

## Why

Decision (2026-07-10, issue #438): **easyplot is deprecated in v1.x and removed in
2.0** â€” no port, no rewrite (utils-migration plan triage table, updated with the
decision). The warning must ship in the next v1.x minor so users hear it well before
2.0 removes the module. The dead block at `easyplot.py:721â€“739` is deleted separately
by the Stage-1 header-literal cleanup (#455).

Related older issues that this decision supersedes (do not implement them; link them
here for the maintainer to triage): #169, #203, #289.

## Links

- `architecture-plan/cellpy2-utils-migration-plan.md` (triage table + decision note)
- `architecture-plan/cellpy2-conventions-plan.md` (Â§3 deprecation cadence)

## Acceptance

- `import cellpy.utils.easyplot` warns exactly once per session, names the
  replacement and the 2.0 removal; entry present in `DEPRECATIONS.md`.
- Full suite green; existing easyplot tests still pass (with the warning filtered).
