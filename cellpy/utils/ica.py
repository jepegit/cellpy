"""Compatibility re-export of [`cellpy.ica`][].

Incremental capacity analysis moved from ``cellpy.utils.ica`` to ``cellpy.ica``
in 2.0 (#566): it is a first-class analysis, not a utility, and it now has a
sibling in ``dvdq`` (differential voltage analysis).

```python
from cellpy import ica          # preferred
from cellpy.utils import ica    # still works
```

Both names refer to the same objects, so nothing breaks. This module carries no
logic of its own — see [`cellpy.ica`][] for the API, and ``DEPRECATIONS.md``
for what goes away in 2.1.
"""

from __future__ import annotations

from cellpy.ica import (  # noqa: F401
    CHARGE,
    DISCHARGE,
    BOTH,
    DVA_DEFAULTS,
    Converter,
    GaussianOptions,
    HalfCycleResult,
    IcaCols,
    IcaOptions,
    ICA_COLS,
    dqdv,
    dqdv_cycle,
    dqdv_cycles,
    dqdv_np,
    dvdq,
    index_bounds,
    to_wide,
    transform_half_cycle,
    value_bounds,
)

__all__ = [
    "BOTH",
    "CHARGE",
    "Converter",
    "DISCHARGE",
    "DVA_DEFAULTS",
    "GaussianOptions",
    "HalfCycleResult",
    "ICA_COLS",
    "IcaCols",
    "IcaOptions",
    "dqdv",
    "dqdv_cycle",
    "dqdv_cycles",
    "dqdv_np",
    "dvdq",
    "index_bounds",
    "to_wide",
    "transform_half_cycle",
    "value_bounds",
]
