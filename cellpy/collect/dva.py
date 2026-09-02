"""dV/dQ (DVA) collection.

Per-cell dV/dQ curves via `dvdq`, concatenated into one tidy
frame with ``cell`` / ``group`` / ``sub_group`` keys. Mirrors
`collect_ica` -- including the per-cell cycle
isolation that fixes the legacy cross-cell narrowing bug (collectors.py:1691)
-- but emits the specced DVA frame: ``cycle, direction, capacity, voltage,
dvdq`` (#863).
"""

from __future__ import annotations

from typing import Any

from cellpy.collect.collection import Collection
from cellpy.collect.ica import _collect_derivative


def collect_dva(batch: Any, options: Any = None, **overrides) -> Collection:
    """Collect dV/dQ (differential voltage) curves per cell into one Collection.

    ``options`` is a [`cellpy.ica.IcaOptions`][cellpy.ica.IcaOptions] recipe,
    forwarded whole to [`dvdq`][cellpy.ica.dvdq]. When omitted, ``dvdq``'s
    ``DVA_DEFAULTS`` (``normalize=False``) are used. ``cycles`` and
    ``transforms`` are collect-level knobs (keyword arguments, not recipe
    fields).

    Cycle selection is derived per cell from the *originally requested* cycles
    every iteration, so a cell missing a cycle never narrows the request for
    the cells after it (mirrors `collect_ica`).

    Example:
        >>> from cellpy import ica
        >>> from cellpy.collect import collect_dva
        >>> opts = ica.DVA_DEFAULTS.replace(capacity_resolution=5.0)
        >>> collect_dva(batch, options=opts, cycles=(2, 3))
    """
    from cellpy.ica import DVA_DEFAULTS

    return _collect_derivative(
        batch,
        options,
        overrides,
        kind="dva",
        verb="dvdq",
        default_recipe=DVA_DEFAULTS,
        resolution_key="capacity_resolution",
    )
