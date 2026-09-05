# Issue #993 — status

- [x] Done

## What's done

- Restored the dotted path on all 24 bare `` See `name` `` references:
  11 → `cellpy.readers.slicing.*`, 8 → `cellpy.exporters.tabular.*`,
  5 → `cellpy.readers.capacity_curves.*` in
  `cellpy/readers/cellreader.py`, and 1 → `cellpy.plotting.registry.families`
  in `cellpy/plotting/registry.py`. No bare form is left in `cellpy/`.
- New `tests/test_doc_cross_references.py` (two essential tests): every
  `` See `X` `` in `cellpy/` must be dotted and resolve (import the longest
  importable prefix, then walk attributes), and `CellpyCell.get_cap` /
  `to_csv` / `to_excel` must point at a delegate that has a docstring.
  Registered in `04-designs-and-guides/test-registry.md`.
- `tests/test_no_sphinx_doc_roles.py` still passes — no roles reintroduced.
- `get_dcap`'s docstring was split over two lines to stay inside the 120-char
  limit.

## Remaining work

None.
