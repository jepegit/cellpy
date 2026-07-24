# Issue #676: Update docs and batch-loader examples for native step/raw headers (cellpy 2.0)

Source: https://github.com/jepegit/cellpy/issues/676

## Original issue text

## Problem / context

On cellpy 2.0.0rc1 (native headers), common batch post-processing notebooks fail because they still hard-code 1.x column names.

Reproducer (standard batch-loader template pattern):

```python
discharge = steps.query("type=='discharge'")
```

raises `UndefinedVariableError: name 'type' is not defined` because the step table column is now `step_type`.

A follow-on attempt using `c.schema` also stumbled on a wrong attribute:

```python
dc_col = c.schema.raw.discharge_capacity  # AttributeError
# correct:
dc_col = c.schema.raw.cumulative_discharge_capacity
```

`docs/fundamentals/data_structure.md` still documents legacy `HeadersStepTable` (`type`, `step`, `cycle`, …). The authoritative rename map is already in `docs/other/header_migration_map.md`, but user-facing fundamentals + batch examples still teach the old names.

Common renames that bite this workflow:

| Old (1.x) | New (2.0 native) | `c.schema` attribute |
|---|---|---|
| `type` | `step_type` | `schema.steps.step_type` |
| `step` | `step_num` | `schema.steps.step_num` |
| `cycle` / `cycle_index` | `cycle_num` | `schema.steps.cycle_num` / `schema.raw.cycle_num` |
| `step_index` | `step_num` | `schema.raw.step_num` |
| `data_point` | `datapoint_num` | `schema.raw.datapoint_num` |
| `discharge_capacity` | `cumulative_discharge_capacity` | `schema.raw.cumulative_discharge_capacity` |

## Spec

1. Update `docs/fundamentals/data_structure.md` step/raw/summary column lists to native names (or clearly mark legacy vs native and point at the migration map).
2. Audit and fix hard-coded 1.x headers in batch docs/examples, especially:
   - `docs/examples/batch_utility/cellpy_batch_processing_docs.ipynb` (+ `.md` if generated)
   - any other shipped templates that query `steps["type"]` / `cycle_index` / `discharge_capacity`
3. Add a short “notebook migration” note (near the migration map or batch docs) showing the recommended `c.schema.*` pattern for this discharge-capacity backfill workflow, including the correct `cumulative_discharge_capacity` attribute.
4. Optionally add a smoke test or doc-test that `c.schema.steps.step_type in c.data.steps.columns` (and the raw capacity column) so docs and runtime cannot drift again.

## Acceptance criteria

- [ ] Fundamentals docs no longer present `type` / `step` / `cycle_index` as the current step/raw headers without calling out the 2.0 rename.
- [ ] Batch-loader example(s) run under native headers without `KeyError` / `UndefinedVariableError` on `type`.
- [ ] Documented schema access uses `schema.raw.cumulative_discharge_capacity` (not `discharge_capacity`).
- [ ] Link to `docs/other/header_migration_map.md` from the updated pages.

## Out of scope

- Restoring legacy on-frame column names (`type`, `cycle_index`, …) as the default runtime.
- Changing cellpy-core `RawCols` / `StepCols` naming.

