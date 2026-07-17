# ADR: dependency-injection restructuring of CellpyCell (#520, V2-09 tail)

**Status:** accepted (2026-07-17) · **Issue:** [#520](https://github.com/jepegit/cellpy/issues/520) · **Epic:** #402 (V2-09)

## Context

`CellpyCell.__init__` historically built everything itself. After the
mechanical extractions (capacity curves #509, exporters #518, split/drop
#519), the class still *constructs* three collaborator kinds inline:

1. **The core seam** — `OldCellpyCellCore` (legacy bridge) or, under the
   `native_schema` flag (#511), `NativeCellpyCellCore`. The core owns the
   `Data` object and runs the step/summary engine.
2. **The instrument factory** — `register_instrument_readers()` builds
   `ds.generate_default_factory()`; `set_instrument()` then creates
   `self.loader_class` from it.
3. **Config-derived options** — reader options are copied from `prms` at
   init (`self.sep`, `self.ensure_step_table`, data dirs, …); units come
   from `get_cellpy_units(cellpy_units)`.

Only (1) and (2) are *behavioural collaborators* worth injecting: tests and
embedders need to substitute them (fake engine, fake loader registry)
without monkeypatching. (3) is plain data already parameterizable.

## Decision

**Own vs receive:**

| Collaborator | `__init__` policy |
|---|---|
| core seam | **receive** via `core=` (default: built from the `native_schema` flag as today). An injected `core` wins; the flag then only documents intent. |
| instrument factory | **receive** via `instrument_factory=` (default: `ds.generate_default_factory()`; built lazily in `register_instrument_readers()` only when none was injected). |
| config snapshot, units, headers | **own** — plain data, already overridable via existing parameters (`cellpy_units=`, prms). Full config inversion is a non-goal here. |

**Wiring of the extracted modules** (capacity_curves / exporters.tabular /
slicing): stays as instance-first functions plus thin delegates. No service
locator, no registry — the delegate methods *are* the wiring, and subclass
dispatch works because cross-calls go through the instance.

**`register_instrument_readers()`** keeps its public name but becomes
idempotent-with-injection: it only builds the default factory when
`self.instrument_factory` is `None`. Calling it after injecting a factory is
a no-op instead of silently discarding the injected one.

## Non-goals

- Splitting `CellpyCell` into multiple classes (that is the Phase-3 /
  native-runtime discussion, not V2-09).
- Inverting `prms` / config access.
- Changing `set_instrument()` semantics or the loader plug-in story (#210).
- Removing the near-dead `_cap_mod_*` pair — decided here: **keep** them as
  moved (#518) until a deprecation sweep; they are test-pinned and harmless.

## Acceptance

- `tests/test_slim.py` (core-seam acceptance) stays green throughout.
- Defaults produce byte-identical behaviour (full suite green).
- New pins: injecting a custom core is used by the pipeline; injecting a
  custom instrument factory is used by `set_instrument`.
