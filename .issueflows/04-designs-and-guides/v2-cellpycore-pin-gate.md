# v2 cellpycore pin gate (#510 Milestone C)

**Status:** satisfied for the 2.0 line (as of 2026-07-24 / issue #574).

**Context.** V2-15 wants an exact `cellpycore==` pin in the cellpy release
commit.

**Decision (historical, #510).** Do not cut the v2.0 release pin until
[cellpy/cellpy-core#136](https://github.com/cellpy/cellpy-core/issues/136) ships
in a **new** core release, then re-pin cellpy to that version. #136 fixed
legacy-bridge stripping of `test_id` on steps/summary and the legacy-schema
`merge_data` story; releasing against `0.2.1` would have frozen the #507
workaround.

**Current pin (master).** `cellpycore==0.2.4` in `[project.dependencies]` /
`uv.lock` (EFC summary columns from core #138/#141). Keep an exact
`==` pin on every release commit; bump only via the F9 order (core release →
cellpy re-pin → cellpy release).

**`v1.x` line.** Stays on the conservative `cellpycore==0.2.1` pin unless a
fix demands a patch bump (`cellpy-v2-branching.md`).

**Sequence (still the rule for future bumps).**

```text
core fix → core bump/tag/PyPI → cellpy pin + UV_NO_SOURCES=1 uv lock
  → essential green → cellpy tag
```

**Refs.** cellpy #510 / #507 / #511 / #574; `.issueflows/04-designs-and-guides/release-procedure.md`.
