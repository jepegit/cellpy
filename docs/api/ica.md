# ICA and DVA

Incremental capacity analysis (dQ/dV) and differential voltage analysis
(dV/dQ).

```python
from cellpy import ica

frame = ica.dqdv(c)                      # cycle, direction, voltage, capacity, dqdv
frame = ica.dvdq(c, direction="charge")  # cycle, direction, capacity, voltage, dvdq
```

Both verbs accept the same three kinds of source — a `CellpyCell`, a curve
frame from `get_cap`, or a bare `(voltage, capacity)` pair — and the same
[`IcaOptions`](#cellpy.ica.IcaOptions) recipe.

::: cellpy.ica
