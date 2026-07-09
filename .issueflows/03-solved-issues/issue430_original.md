# Issue #430: Stage 0.3: Characterization tests — configuration system (prms)

Source: https://github.com/jepegit/cellpy/issues/430

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/code-reviews/` (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Pin the current prms behavior before the pydantic-settings rework:

- config-file round-trip (extend `test_prms.py`),
- precedence: file values vs runtime mutation,
- OtherPath coercion in `Paths` (+ resolve behavior),
- `.env_cellpy` secret pickup as consumed by `internals/otherpath.py`,
- `cellpy setup` file/folder creation,
- an **inventory test** asserting the exact set of (section, field, default) triples.

## Why

Config plan Step 0. The inventory test becomes the parity contract for the new pydantic
models (plan Step 2 asserts new defaults == old, field by field). Validation will later
*find* type lies (e.g. `Reader.limit_loaded_cycles` declared `Optional[int]` but used as a
`[from, to]` list in `arbin_res.py`) — current behavior must be recorded before it is fixed.

## Links

- `code-reviews/cellpy2-configuration-and-parameters-plan.md` (Step 0, §6 risks)
- `code-reviews/cellpy2-plans-gap-analysis.md` (G7 — OtherPath decision recorded in config plan §5b)

## Acceptance

- Inventory test fails if any prms field/default changes without the test being updated.
- All listed behaviors covered; suite green on master.

