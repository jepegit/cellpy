# Plan: #850 thread-safe config.override via ContextVar

## Goal

Make `config.override()` scoped per thread / async task so concurrent jobs
cannot observe each other's overrides.

## Constraints

- Keep nested LIFO stacking and existing tests in `tests/test_config.py`.
- `reload` / `set_load_options` stay process-global (document in docstring).
- Yolo-sized: ContextVar for override stack + active config; do not
  ContextVar-migrate the whole session.

### Prior art

- `cellpy/config/session.py` — `_override_stack` + `reload()` swap global `_session`.
- `tests/test_config.py` — nested override + essential fixture.

## Approach

1. Replace module `_override_stack` with `ContextVar` tuple stack +
   `ContextVar` for the active overridden `CellpyConfig`.
2. `get_config()` returns context config when set, else session config.
3. `override()` pushes stack, builds config via deep-merge on
   `session.config.model_dump()` + `CellpyConfig.model_validate`, yields it;
   no global `_session` swap.
4. `reload()` rebuilds global session **without** applying the override stack;
   if currently inside an override, refresh the context-local config.
5. Threaded regression test matching the issue reproduction.

## Files to touch

- `cellpy/config/session.py`
- `tests/test_config.py`
- HISTORY + issue tracking

## Test strategy

`uv run pytest tests/test_config.py -q` then `uv run pytest -m essential -q`.

## Open questions

None.
