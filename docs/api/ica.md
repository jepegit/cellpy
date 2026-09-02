# ICA and DVA

Incremental capacity analysis (dQ/dV) and differential voltage analysis
(dV/dQ).

```python
from cellpy import ica          # preferred
from cellpy.utils import ica    # same objects; kept as a re-export

frame = ica.dqdv(c)                      # cycle, direction, voltage, capacity, dqdv
frame = ica.dvdq(c, direction="charge")  # cycle, direction, capacity, voltage, dvdq
```

Both verbs accept the same three kinds of source — a `CellpyCell`, a curve
frame from `get_cap`, or a bare `(voltage, capacity)` pair — and the same
[`IcaOptions`][cellpy.ica.IcaOptions] recipe (or individual fields as keyword
overrides).

`direction` is **cell-centric**: `"charge"` means the *cell* is charging
(same sense as `get_ccap` / the summary). Filter the long frame, or pass
`direction="charge"` / `"discharge"` up front.

DVA (`dvdq`) defaults to `normalize=False` — peak *positions* on the capacity
axis are the signal. Wide layout is an explicit conversion, never an implicit
mode of `dqdv` / `dvdq`:

```python
wide = ica.to_wide(frame)
```

## Plot and collect

| Need | Call |
| --- | --- |
| One-cell dQ/dV figure | [`ica_plot`][cellpy.utils.plotutils.ica_plot] |
| One-cell dV/dQ figure | [`dva_plot`][cellpy.utils.plotutils.dva_plot] |
| Many cells, dQ/dV | [`collect_ica`][cellpy.collect.ica.collect_ica] |
| Many cells, dV/dQ | [`collect_dva`][cellpy.collect.dva.collect_dva] |

`cellpy.collect.IcaOptions` is a **different** dataclass from
[`cellpy.ica.IcaOptions`][cellpy.ica.IcaOptions]: it only holds the collection
knobs (`cycles`, `voltage_resolution`, `capacity_resolution`). Do not pass one
where the other is expected.

Worked notebook: [Incremental capacity analysis](../examples/04_incremental_capacity_analysis.md).
Short recipe: [How to compute ICA / DVA](../guides/ica.md).

Coming from 1.x / 2.0: `Converter`, `dqdv_cycle` / `dqdv_cycles` / `dqdv_np`,
and the duplicate `dq` column are gone — see the
[2.0 → 2.1 migration guide](../getting_started/migration_v2.0_to_2.1.md).

::: cellpy.ica
