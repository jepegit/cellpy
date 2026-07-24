# Issue #573: Stage 3.16: lock the file-format compatibility matrix (v8 read/write, v9, convert)

Source: https://github.com/jepegit/cellpy/issues/573

## Original issue text

## Goal

Verify and lock the 2.0 file-format compatibility matrix end to end.

## Why

The support matrix is a promise made in the release notes; it needs a test, not a
sentence. v9 write and v8 write both exist today (`save(cellpy_file_format="v8")`), but
there is no single suite asserting the whole matrix, and `cellpy convert --to v9` does
not exist yet â€” `convert` still only takes `old_h5 new_h5`.

Plan: `architecture-plan/cellpy2-release-and-branching-plan.md` Â§1; architecture plan
Â§2 and Â§6 row 3.1.

## Scope

- [ ] Test matrix: read v8 âœ“, read v9 âœ“, write v9 (default) âœ“,
      write v8 via `save(cellpy_file_format="v8")` âœ“, read v<8 â†’ typed error naming
      `cellpy convert` on 1.x âœ“.
- [ ] `cellpy convert --to v9` (and `--to v8`) implemented and tested.
- [ ] v8 round-trip through 2.0 preserves values (parity oracle, not byte equality).
- [ ] The v<8 freeze message is what the 1.x deprecation warnings promised.
- [ ] Matrix runs on every CI job that touches file IO.

## Acceptance

- One parametrized suite covers every cell of the matrix.
- Converting a v8 golden to v9 and back gives value parity on raw, steps and summary.
