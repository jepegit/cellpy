"""biologics_mpr's two-stage entry points (#560).

Value parity is covered end-to-end in ``test_loader_port_parity.py`` (the mpr
fixture is in-repo). This module pins the parts specific to the biologics port:
that ``parse()`` runs the mpr *derivations* — not a plain rename — so the vendor
frame already carries cellpy names and a real datetime, and that
``declarations()`` refuses to run before ``parse()``.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers import data_structures as ds

SOURCE = "testdata/data/biol.mpr"


def _loader():
    return ds.generate_default_factory().create("biologics_mpr")


def _parsed():
    loader = _loader()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse(SOURCE)
    return loader, vendor


@pytest.mark.essential
def test_parse_derives_cellpy_columns_the_file_does_not_store():
    """cycle_index, the capacity split and date_time are all *derived* in parse."""
    _, vendor = _parsed()
    for derived in ("cycle_index", "charge_capacity", "discharge_capacity", "date_time"):
        assert derived in vendor.columns
    # date_time is a real datetime, built from the log start plus elapsed seconds.
    assert vendor["date_time"].dtype == pl.Datetime


@pytest.mark.essential
def test_declarations_map_to_native_and_pick_datetime():
    loader, _ = _parsed()
    declarations = loader.declarations()
    assert declarations.column_map["voltage"] == "potential"
    assert declarations.column_map["current"] == "current"
    assert declarations.datetime_kind == "datetime"


@pytest.mark.essential
def test_declarations_before_parse_raises():
    loader = _loader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()
