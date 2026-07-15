# Issue #458 — Stage 1.15: translate.py — dormant native⇄legacy frame translation in cellpy_file/

GitHub: https://github.com/jepegit/cellpy/issues/458
Labels: cellpy2-stage1

## Goal

Native-headers plan Phase 1: build `to_native(data)` / `to_legacy(data)` in
`cellpy/readers/cellpy_file/translate.py` over `cellpycore.legacy.mapping`
(dormant on v1.x — the Phase-3 flip wires it into `cellpy_file.load`), with the
v8 → native → v8 round-trip and totality tests as the guards, and the #434
value-parity comparator green against the translated frames.

Depends on core#116 (mapping extensions; shipped in cellpycore 0.2.0).

## Acceptance

- v8 golden → to_native → to_legacy round-trip green; every column in the
  golden file classified (mapped / legacy-only) — unknown fails; #434
  comparator green.
