# Status — issue #458 (Stage 1.15)

- [x] Done

## 2026-07-15

- `cellpy_file/translate.py` landed (dormant; Phase 3 wires it into load).
- v8 → native → v8 round-trip exact; totality guard classified two real
  quirks (steps `index` column per D4; legacy-only `shifted_*` specific
  variants); #434 comparator green through the translation for all three
  frame families.
- Full suite: **592 passed, 0 failed**. Stage-1 issue set complete.
