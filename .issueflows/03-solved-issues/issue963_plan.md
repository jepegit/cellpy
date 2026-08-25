# Issue #963 plan

## Goal

Document batch from the user's object: `b = batch.load(...)`. Stop leading
with "facade". Give `b.plot` and other public methods Shift-Tab docstrings.

## Constraints

- Docs + docstrings only. No API behavior change.
- Keep private `_Legacy*` adapters out of the published API page.

### Prior art

- `docs/api/batch.md` currently has a **Facade** heading → `cellpy.batch.facade`
  (dumps adapters).
- `Batch.plot` has no docstring.
- `tests/test_collect.py::test_collector_help_names_the_common_kwargs` is the
  Shift-Tab contract pattern.

## Approach

1. Rewrite `docs/api/batch.md` around `b = batch.load(...)` and what `b` does.
   Document `Batch` members, filter `^_`.
2. Expand `Batch` / `cellpy.batch` module docs; add Google-style docstrings on
   public methods that lack them (`plot`, properties, aliases).
3. One essential test: public methods have `__doc__`; class doc names `plot`.

## Files to touch

- `docs/api/batch.md`
- `cellpy/batch/__init__.py`, `cellpy/batch/facade.py`
- `docs/getting_started/agents.md` / `AGENTS.md` (one line: `b.plot()`)
- `tests/test_batch_v3_facade.py`, `test-registry.md`

## Test strategy

`uv run pytest -m essential`. New docstring test.

## Open questions

None — yolo-fit, docs only.
