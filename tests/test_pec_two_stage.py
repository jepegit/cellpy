"""pec_csv's own two-stage entry points (#560).

pec_csv is not configuration-driven — it identifies columns by alias set and
carries a different unit per column in the header — so its ``parse()`` and
``declarations()`` are hand-written rather than derived (plan §2.6a). These
tests pin the decisions that shape is built on: units normalised in ``parse()``,
a static canonical→native map, and the file's other columns preserved as
passthroughs.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers import data_structures as ds

SOURCE = "testdata/data/pec.csv"


def _loader():
    return ds.generate_default_factory().create("pec_csv")


def _parsed():
    loader = _loader()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse(SOURCE)
    return loader, vendor


@pytest.mark.essential
def test_parse_renames_matched_columns_to_canonical_names():
    _, vendor = _parsed()

    for canonical in ("voltage", "current", "cycle", "charge_capacity"):
        assert canonical in vendor.columns, f"{canonical} not produced by parse()"
    # Not the native names yet — renaming to native is harmonize's job.
    assert "potential" not in vendor.columns
    assert "cumulative_charge_capacity" not in vendor.columns


@pytest.mark.essential
def test_parse_normalises_units_to_canonical():
    """The header carries the unit; parse() scales to V/A/Ah regardless.

    pec.csv exports voltage in volts, so the values must sit in a plausible
    cell-voltage band — if a mV column were left unscaled it would read in the
    thousands, which is exactly the mutation the parity oracle catches.
    """
    _, vendor = _parsed()

    voltage = vendor["voltage"].drop_nulls()
    assert voltage.min() >= 0.0
    assert voltage.max() < 10.0, "voltage looks unscaled (mV left as V?)"


@pytest.mark.essential
def test_declarations_map_canonical_to_native():
    loader, _ = _parsed()
    declarations = loader.declarations()

    assert declarations.column_map["voltage"] == "potential"
    assert declarations.column_map["current"] == "current"
    assert (
        declarations.column_map["charge_capacity"] == "cumulative_charge_capacity"
    )


@pytest.mark.essential
def test_the_vendor_test_id_is_not_mapped_onto_the_framework_test_id():
    """Same provenance rule the configuration loaders get, reused here.

    ``test`` is the vendor's own test number — provenance, not a measurement.
    Mapping it onto the native ``test_id`` (the framework's grouping key) would
    let the vendor value quietly win. The derivation drops it because it reuses
    ``derive_column_maps``.
    """
    loader, _ = _parsed()
    declarations = loader.declarations()

    assert "test" not in declarations.column_map
    assert "test_id" not in declarations.column_map.values()


@pytest.mark.essential
def test_declarations_preserve_the_files_other_columns_as_passthrough():
    """A pec export carries temperatures, OCV, peak power. loader() keeps them
    under sanitised names; the two-stage path must not silently drop them."""
    loader, vendor = _parsed()
    declarations = loader.declarations()

    # A representative non-canonical column present in the fixture.
    assert "ambient_temperature_degc" in vendor.columns
    assert "ambient_temperature_degc" in declarations.passthrough


@pytest.mark.essential
def test_declarations_before_parse_raises():
    loader = _loader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()


@pytest.mark.essential
def test_zero_based_cycles_are_shifted_in_parse():
    """pec shifts 0-based cycles to start at 1, via the shared hook."""
    _, vendor = _parsed()
    assert vendor["cycle"].min() >= 1
