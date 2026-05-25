# Plan for issue #365: units when exporting in bdf

## Goal

Let callers of `CellpyCell.to_bdf` (and the underlying `cellpy.exporters.bdf.to_bdf`) pass a `CellpyUnits` object as a keyword argument that controls the **units written into the BDF file** (both column labels and column values). When omitted, current behaviour is unchanged — strict BDF spec units (`A`, `V`, `Ah`, `Wh`, `s`, `W`, `ohm`).

> **Important**: providing this kwarg with anything other than the BDF defaults makes the file *not strictly BDF-compliant* (BDF locks units per column). We accept that explicitly — same trade-off the existing `extras=True` knob already makes — and call it out in the docstring and design doc.

## Constraints

- KISS: one new kwarg, one helper to synthesize column labels from a unit symbol; no new public class.
- Back-compat: existing callers that omit the new kwarg get **byte-for-byte identical** output (same labels, same machine names, same values).
- Layering rule from `.issueflows/04-designs-and-guides/bdf-export.md` stays intact: `cellreader` → `exporters` → `filters` → `internal_settings`; no `cellpy.utils` import.
- Do not mutate the passed-in `CellpyUnits` object and do not mutate `cell.cellpy_units`.
- Fail loud, not silent: if the user's unit symbol is not pint-compatible with the underlying dimension (e.g. `charge="kg"`), raise — do *not* fall back to factor 1.0 (the current pint-failure branch is only safe for *spec defaults* and quietly emits wrong values otherwise).

## Approach

### Column map refactor (small, local)

`_COLUMN_MAP` rows currently embed the BDF default label and machine name as constants:

```python
_BdfColumn("charge_capacity_txt", "Charging Capacity / Ah", "charging_capacity_ah", "optional", "charge", "Ah"),
```

Split the label into a unitless **base** plus the unit symbol so we can rebuild both forms for any unit:

```python
_BdfColumn(
    cellpy_field="charge_capacity_txt",
    base_preferred="Charging Capacity",     # no unit
    base_machine="charging_capacity",       # no unit suffix
    tier="optional",
    unit_kind="charge",
    bdf_unit="Ah",                          # BDF spec default
)
```

Add a tiny helper:

```python
def _resolve_column_names(spec, effective_unit):
    # Byte-for-byte identical to today when effective_unit == bdf_unit.
    if effective_unit is None:
        return f"{spec.base_preferred} / 1", spec.base_machine
    if effective_unit == spec.bdf_unit:
        return _BDF_DEFAULT_LABELS[spec.cellpy_field]   # frozen pairs
    return (
        f"{spec.base_preferred} / {effective_unit}",
        f"{spec.base_machine}_{_slug(effective_unit)}",
    )
```

`_BDF_DEFAULT_LABELS` is a frozen `dict` keyed by `cellpy_field` holding the exact strings we ship today (`"Charging Capacity / Ah"`, `"charging_capacity_ah"`, ...). That guarantees the no-override path is unchanged and pins the existing BDF-spec spellings (which are inconsistent: `volt`, `ampere`, `watt` vs `ah`, `wh`, `ohm` — we keep them, don't try to "fix" them).

`_slug(unit)` lowercases and strips non-alphanumerics: `"mAh" → "mah"`, `"kWh" → "kwh"`, `"min" → "min"`.

### Entry point (`cellpy/exporters/bdf.py:to_bdf`)

- Add `bdf_units: Optional[CellpyUnits] = None` kwarg (name choice — see open questions; `bdf_units` is my recommendation, but I'll change to whatever you pick).
- Build an `effective_unit_map: dict[unit_kind, str]` (e.g. `{"charge": "mAh", "current": "A", ...}`):
  - default: read each `unit_kind` from `_BDF_DEFAULT_TARGET_UNITS` (== the current `bdf_unit` per column);
  - when `bdf_units is not None`: for each unit kind present on `CellpyUnits`, look it up and override the default.
- Pass `effective_unit_map` into `_build_bdf_frame`.
- Re-purpose `_conversion_factor`: factor = ratio from `cell.cellpy_units` to `effective_unit_map[unit_kind]`. The pint call is the same shape as today; only the second argument changes.
- On pint failure with an explicit override, raise `ValueError("to_bdf: cannot convert charge from 'mAh' to 'kg': ...")`. With no override (legacy path), keep today's warn-and-skip-conversion behaviour intact.

### Class layer (`cellpy/readers/cellreader.py:CellpyCell.to_bdf`)

- Add the same `bdf_units=None` kwarg and forward to `_to_bdf(...)`.
- Docstring update — add the `Args:` entry and an Example block:

  ```python
  from cellpy.parameters.internal_settings import CellpyUnits

  custom = CellpyUnits(charge="mAh", current="mA")
  cell.to_bdf("out.bdf.csv", bdf_units=custom)
  # column headers become "Charging Capacity / mAh", "Current / mA"
  # values are scaled to mAh / mA accordingly
  ```

- Mirror the example in `cellpy/exporters/bdf.py:to_bdf`'s docstring as the issue explicitly requested.

### Design doc (`.issueflows/04-designs-and-guides/bdf-export.md`)

- New short subsection under "Unit conversion" titled e.g. **"Overriding target units (`bdf_units=`)"**, explaining: (a) what it does, (b) that it produces a non-strictly-BDF file (parallel to `extras=True`), (c) failure mode on incompatible units. Cross-link to issue #365.
- Add a Q7 row to the **Locked decisions** table: target unit override knob, default = strict BDF spec.

## Files to touch

- `cellpy/exporters/bdf.py` — refactor `_BdfColumn` fields, add `_resolve_column_names` + `_slug` + `_BDF_DEFAULT_LABELS` + `_BDF_DEFAULT_TARGET_UNITS`, add `bdf_units` kwarg, strict-failure on incompatible units, docstring example.
- `cellpy/readers/cellreader.py` — pass-through kwarg on `CellpyCell.to_bdf`, docstring example.
- `tests/test_exporters_bdf.py` — new tests (see below).
- `.issueflows/04-designs-and-guides/bdf-export.md` — Q7 row, target-unit subsection, cross-link to #365.

## Test strategy

Re-run the existing exporters suite first to confirm no regression from the refactor:

```bash
uv run pytest tests/test_exporters_bdf.py -q
```

Add the following targeted tests to `tests/test_exporters_bdf.py`:

- `test_bdf_units_none_matches_default_path` — explicit `bdf_units=None` produces a frame identical to the default-kwarg call (same columns, same values).
- `test_bdf_units_overrides_charge_to_mAh` — pass `CellpyUnits(charge="mAh")`; expect column `Charging Capacity / mAh` (machine: `charging_capacity_mah`) with values 100x the `Ah` values (since the synthetic cell's source charge is mAh, factor 1.0, but the *label* changes to mAh and values stay raw mAh).
- `test_bdf_units_overrides_current_to_mA` — pass `CellpyUnits(current="mA")`, source `cell.cellpy_units.current == "A"`. Expect `Current / mA` column with values 1000× the `A` values. Header machine name = `current_ma`.
- `test_bdf_units_overrides_time_to_minutes` — `CellpyUnits(time="min")`; expect `Test Time / min` and values divided by 60.
- `test_bdf_units_does_not_mutate_inputs` — capture cell + passed-in `CellpyUnits` before and after; assert neither mutated.
- `test_bdf_units_incompatible_unit_raises` — pass `CellpyUnits(charge="kg")`; expect `ValueError` mentioning `charge`, `mAh`, `kg`.
- `test_bdf_units_partial_override_keeps_defaults` — `CellpyUnits(charge="mAh")` only; assert `Voltage / V` and `Current / A` columns are unchanged (still BDF defaults, byte-for-byte against the no-override output).

Wider sweep at close-time:

```bash
uv run pytest tests/test_exporters_bdf.py tests/test_filters_cycles.py -q
```

## Open questions

1. **Kwarg name**: my proposal is `bdf_units` ("what units do I want in the BDF file?"). Alternatives:
   - `output_units` — general but loses the BDF context;
   - `cellpy_units` — matches the type name but collides with `cell.cellpy_units` (which is the *source* unit set);
   - `target_units` — accurate but a bit jargon-y.
   **Pick one.**
2. **Failure on incompatible unit**: I propose hard-fail (`ValueError`) when the user explicitly overrides to a unit pint cannot convert. Today's silent factor-1.0 fallback only fires on weird custom units in the spec-default path. **OK to fail loud?**
3. **Strict-BDF flag in the file?** Should we (optionally) emit a small log warning like `"to_bdf: bdf_units override active — file is not strictly BDF-compliant (Charging Capacity in mAh, expected Ah)"`? Mirrors what `extras=True` logs. **OK to add?**
4. **`CellpyUnits` fields we ignore**: the column map only uses `current`, `voltage`, `time`, `charge`, `energy`, `power`, `resistance`. Other `CellpyUnits` fields (`mass`, `nominal_capacity`, `specific_*`, `temperature`, `pressure`, `frequency`, ...) are silently ignored by `to_bdf` today and stay ignored. **Confirm we don't try to surface temperature / pressure here — that's already listed as out of scope in the design doc.**
