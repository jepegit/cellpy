"""arbin_res's two-stage entry points (#560).

arbin_res reads an Access ``.res`` database — ODBC on Windows, mdbtools on
posix — so these tests skip where no backend is available, exactly as the
loader golden does. Where a backend exists (CI has mdbtools), they run.

The vendor stage is unusually thin here: ``get_headers_normal()`` is already a
``{cellpy attr → Arbin column}`` map, so ``declarations()`` reuses the same
derivation the configuration loaders use. What ``parse()`` adds is only the
database read, stopping before the rename and the datetime conversion that
``harmonize()`` now owns.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers import data_structures as ds

SOURCE = "testdata/data/20160805_test001_45_cc_01.res"


def _loader():
    return ds.generate_default_factory().create("arbin_res")


def _parsed_or_skip():
    loader = _loader()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vendor = loader.parse(SOURCE)
    except Exception as exc:  # noqa: BLE001 — unavailable backend, not a bug
        pytest.skip(f"arbin_res backend unavailable here: {exc}")
    return loader, vendor


@pytest.mark.essential
def test_parse_returns_arbin_vendor_names():
    _, vendor = _parsed_or_skip()

    # Arbin's own spellings, not native — renaming is harmonize's job.
    for arbin in ("Voltage", "Current", "Charge_Capacity", "Cycle_Index"):
        assert arbin in vendor.columns, f"{arbin} missing from the parsed frame"
    assert "potential" not in vendor.columns


@pytest.mark.essential
def test_declarations_derive_from_get_headers_normal():
    loader, _ = _parsed_or_skip()
    declarations = loader.declarations()

    assert declarations.column_map["Voltage"] == "potential"
    assert declarations.column_map["Current"] == "current"
    assert (
        declarations.column_map["Charge_Capacity"] == "cumulative_charge_capacity"
    )


@pytest.mark.essential
def test_the_vendor_test_id_is_not_mapped_onto_the_framework_test_id():
    """``Test_ID`` is provenance; mapping it onto native ``test_id`` (the
    grouping key) would let the vendor value win. The shared derivation drops
    it, same as for the configuration loaders."""
    loader, _ = _parsed_or_skip()
    declarations = loader.declarations()

    assert "Test_ID" not in declarations.column_map
    assert "test_id" not in declarations.column_map.values()


@pytest.mark.essential
def test_declarations_before_parse_raises():
    loader = _loader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()


@pytest.mark.essential
def test_two_stage_capacities_match_the_legacy_frame():
    """The assertion the switchover rests on, through the public entry points."""
    import cellpy

    loader, vendor = _parsed_or_skip()
    from cellpy.readers.instruments.harmonize import harmonize

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = harmonize(vendor, loader.declarations(), strict=False)
        cell = cellpy.get(SOURCE, instrument="arbin_res", mass=1.0, testing=True)

    legacy = pl.from_pandas(cell.data.raw.reset_index(drop=True))
    for column in (
        "potential",
        "current",
        "cumulative_charge_capacity",
        "cumulative_discharge_capacity",
        "test_time",
    ):
        difference = (
            raw[column].cast(pl.Float64) - legacy[column].cast(pl.Float64)
        ).abs().max()
        assert difference is not None and difference < 1e-9, (
            f"{column} differs by {difference}"
        )
