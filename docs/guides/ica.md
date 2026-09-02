# Compute incremental capacity and differential voltage

dQ/dV (ICA) and dV/dQ (DVA) both live on [`cellpy.ica`](../api/ica.md). Prefer
`from cellpy import ica` — `cellpy.utils.ica` is the same module.

## One cell

```python
from cellpy import ica
from cellpy.utils import example_data

c = example_data.cellpy_file()

ica_frame = ica.dqdv(c, cycles=[2, 3])           # cycle, direction, voltage, capacity, dqdv
dva_frame = ica.dvdq(c, cycles=2, direction="charge")  # cycle, direction, capacity, voltage, dvdq

charge = ica_frame[ica_frame.direction == "charge"]
```

`direction` is cell-centric (`"charge"` = the cell is charging). Pass
`direction=` to keep one half-cycle, or filter the long frame.

## `IcaOptions` — the transform recipe

Smoothing, interpolation, and normalization live on a frozen
[`IcaOptions`][cellpy.ica.IcaOptions]. Three equivalent ways to use it:

```python
from cellpy import ica

# 1. One-off: override a single field (no dataclass needed)
frame = ica.dqdv(c, cycles=3, voltage_resolution=0.005)

# 2. Build a reusable recipe and pass it as options=
opts = ica.IcaOptions(
    voltage_resolution=0.005,
    voltage_fwhm=0.015,
    post_smoothing=True,
    normalize="area",
)
frame = ica.dqdv(c, cycles=3, options=opts)

# 3. Tweak a copy — IcaOptions is frozen, so use replace()
#    Keyword overrides also stack on an existing options object
frame = ica.dqdv(c, cycles=3, options=opts.replace(pre_smoothing=True))
frame = ica.dqdv(c, cycles=3, options=opts, voltage_fwhm=0.02)
```

`dvdq` uses the same class. Its default recipe is `ica.DVA_DEFAULTS`
(`normalize=False` — peak *positions* on the capacity axis are the signal):

```python
dva_opts = ica.DVA_DEFAULTS.replace(capacity_resolution=5.0)
dva = ica.dvdq(c, cycles=3, options=dva_opts)
```

The returned frame's `.attrs["options"]` is the recipe that was actually
used. `strict=True` raises instead of warning when a half-cycle fails.

Common fields (defaults in brackets): `voltage_resolution` / `capacity_resolution`
[`None`], `max_points` [`None`], `interpolation_method` [`"linear"`],
`pre_smoothing` / `diff_smoothing` / `post_smoothing` [`False` / `False` / `True`],
`voltage_fwhm` [`0.01`], `capacity_fwhm` [`None` = 1% of the half-cycle span],
`normalize` [`"area"` for ICA, `False` for DVA]. Full list:
[`IcaOptions`][cellpy.ica.IcaOptions].

Wide (cycle-per-column) layout is an explicit conversion:

```python
wide = ica.to_wide(ica_frame)
```

## Plot

```python
from cellpy.utils.plotutils import ica_plot, dva_plot

fig = ica_plot(c, cycles=[2, 3], voltage_resolution=0.005)
fig = ica_plot(c, cycles=[2, 3], options=opts)  # same IcaOptions as dqdv
fig = dva_plot(c, cycles=2, direction="charge")
```

Both accept `backend="plotly"` (default) or `"matplotlib"`. Set
`return_data=True` to also get the long frame.

## Many cells

```python
from cellpy.collect import IcaOptions as CollectIcaOptions
from cellpy.collect import collect_ica, collect_dva

# keyword overrides (same as one-cell)
ica_coll = collect_ica(batch, cycles=(2, 3), voltage_resolution=0.005)
dva_coll = collect_dva(batch, cycles=(2, 3), capacity_resolution=5.0)

# or a collect-side options object
coll_opts = CollectIcaOptions(cycles=(2, 3), voltage_resolution=0.005)
ica_coll = collect_ica(batch, options=coll_opts)
dva_coll = collect_dva(
    batch, options=coll_opts.replace(capacity_resolution=5.0)
)
```

`cellpy.collect.IcaOptions` is **not** `cellpy.ica.IcaOptions`. The collect
variant only has `cycles`, `voltage_resolution`, `capacity_resolution`, and
`transforms`. Do not pass one where the other is expected.

## See also

- [Tutorial notebook](../examples/04_incremental_capacity_analysis.md)
- [ICA / DVA API](../api/ica.md)
- [Collect](../api/collect.md) — `collect_ica` / `collect_dva`
- [2.0 → 2.1 migration](../getting_started/migration_v2.0_to_2.1.md) — removed 1.x helpers
