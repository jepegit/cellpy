"""Reusable, dataframe-level filters for cellpy.

Anything in this package operates on plain pandas DataFrames so it can
be composed by exporters, plotters, and batch tools without coupling to
``CellpyCell``.
"""

from cellpy.filters.cycles import filter_cycles

__all__ = ["filter_cycles"]
