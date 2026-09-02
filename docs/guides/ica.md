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

Smoothing and interpolation live on [`IcaOptions`][cellpy.ica.IcaOptions] —
pass an instance as `options=`, or override one field:

```python
ica.dqdv(c, cycles=3, voltage_resolution=0.005)
ica.dvdq(c, cycles=3, capacity_resolution=5.0)
```

Wide (cycle-per-column) layout is an explicit conversion:

```python
wide = ica.to_wide(ica_frame)
```

## Plot

```python
from cellpy.utils.plotutils import ica_plot, dva_plot

fig = ica_plot(c, cycles=[2, 3], voltage_resolution=0.005)
fig = dva_plot(c, cycles=2, direction="charge")
```

Both accept `backend="plotly"` (default) or `"matplotlib"`. Set
`return_data=True` to also get the long frame.

## Many cells

```python
from cellpy.collect import collect_ica, collect_dva

ica_coll = collect_ica(batch, cycles=(2, 3), voltage_resolution=0.005)
dva_coll = collect_dva(batch, cycles=(2, 3), capacity_resolution=5.0)
```

`cellpy.collect.IcaOptions` is **not** `cellpy.ica.IcaOptions`. The collect
variant only has `cycles`, `voltage_resolution`, `capacity_resolution`, and
`transforms`.

## See also

- [Tutorial notebook](../examples/04_incremental_capacity_analysis.md)
- [ICA / DVA API](../api/ica.md)
- [Collect](../api/collect.md) — `collect_ica` / `collect_dva`
- [2.0 → 2.1 migration](../getting_started/migration_v2.0_to_2.1.md) — removed 1.x helpers
