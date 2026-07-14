# Plan — issue #451 (Stage 1.6)

1. **Re-pin** `cellpycore==0.2.0` (the Stage-1 additive release carrying
   core#115 `convert_value` / `calculate_scaler` / `validate_units`) +
   `uv lock` / `uv sync`. Rides in this PR per the core-first merge order.
2. **Delegate, delete the bodies** in `cellpy/readers/cellreader.py`:
   - `get_converter_to_specific` → `core_units.get_converter_to_specific`
     (wrapper keeps the `mode is None → 1.0` early-out and the
     `to_units or self.cellpy_units` default).
   - `nominal_capacity_as_absolute` → core original (wrapper pins the legacy
     `nom_cap_specifics or "gravimetric"` default and passes
     `cellpy_units=self.cellpy_units`); the old PerformanceWarning help text
     is condensed into the docstring.
   - `to_cellpy_unit` → `core_units.convert_value` (pint `Quantity` inputs
     handled in the wrapper — core's public API takes plain values; the
     NoDataFound message for cell-less conversion preserved).
   - `unit_scaler_from_raw` → `core_units.calculate_scaler(raw_units[prop],
     unit)`.
   - `_make_summary` current factor →
     `core_units.calculate_current_conversion_factor`.
3. **Known benign deltas:** `value=0` no longer falls back to `data.mass`
   (`is not None` instead of truthiness); unitless strings raise `ValueError`
   with a clear message instead of pint `DimensionalityError`; volumetric mode
   without a volume raises `ValueError` instead of `AttributeError`.
4. **Guards:** converter-parity fixtures (Stage-0 #431) compare cellpy output
   against cellpycore on both sides; full suite green.
