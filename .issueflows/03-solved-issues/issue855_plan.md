# Plan: #855 gitignore test leftovers

## Goal

Ignore the two local leftovers named in the issue if they are safe to ignore;
document the verification outcome.

## Constraints

- Do **not** ignore tracked fixtures under `testdata/hdf5/*.h5` (used by
  conftest / suite).
- Prefer exact paths over broad globs.

### Prior art / verification

- `.gitignore` already has a commented “testdata that changes when running
  tests” block (including an old `cellpy_batch_test.json` name).
- `tests/test_batch.py::test_load_autoloads_journal_from_journal_dir` writes
  `cellpy_batch_test_batch.json` under **`tmp_path`**, not the repo root — so
  the root file is a **manual / stray** leftover, not every-run essential output.
- `conftest` regenerates `testdata/hdf5/20160805_test001_45_cc.h5` (tracked) when
  missing; a sibling `.cellpy` is not produced by that path (save infers hdf5 from
  `.h5`). The `.cellpy` leftover is still a local artifact that must not be
  committed.

**Verdict:** Agent assumption “suite regenerates them every run” is **not**
accurate for current essential tests, but both paths are still correct
gitignore entries (stray local artifacts).

## Approach

Add explicit ignore rules for:
- `/cellpy_batch_test_batch.json`
- `/testdata/hdf5/20160805_test001_45_cc.cellpy`

## Files to touch

- `.gitignore`
- issue tracking + HISTORY (small chore)

## Test strategy

No code tests; `git check-ignore -v` on the two paths.

## Open questions

None.
