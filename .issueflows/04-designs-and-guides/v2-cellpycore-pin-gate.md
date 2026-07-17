# v2 cellpycore pin gate (#510 Milestone C)

**Context.** V2-15 wants an exact `cellpycore==` pin in the cellpy release
commit. cellpy already pins `cellpycore==0.2.1` (latest core PyPI as of
2026-07-15).

**Decision.** Do not cut the v2.0 release pin (or claim V2-15 done) until
[cellpy/cellpy-core#136](https://github.com/cellpy/cellpy-core/issues/136) ships
in a **new** core release, then re-pin cellpy to that version.

**Why.** #136 fixes legacy-bridge stripping of `test_id` on steps/summary and
the legacy-schema `merge_data` story. cellpy #507 works around the strip today;
releasing v2 against 0.2.1 would freeze the workaround as the supported path.

**Sequence.**

```text
core#136 fix → core bump/tag/PyPI → cellpy pin + UV_NO_SOURCES=1 uv lock
  → essential green → v2.0.0aN / release checklist
```

**Refs.** cellpy #510 / #507 / #511; `.issueflows/04-designs-and-guides/release-procedure.md`.
