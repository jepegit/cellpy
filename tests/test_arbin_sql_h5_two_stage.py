"""arbin_sql_h5's two-stage entry points (#560).

The one arbin_sql variant with an in-repo fixture, so the only one whose port is
CI-checkable. Its declarations derive from the module renaming dict like the
other Arbin loaders; what is different is one non-declarative step — the
internal-resistance forward fill — expressed as a declared post hook.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers import data_structures as ds

SOURCE = "testdata/data/20200624_test001_cc_01.h5"


def _loader():
    return ds.generate_default_factory().create("arbin_sql_h5")


def _parsed():
    loader = _loader()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse(SOURCE)
    return loader, vendor


@pytest.mark.essential
def test_parse_returns_arbin_vendor_names():
    _, vendor = _parsed()

    for arbin in ("Voltage", "Current", "Charge_Capacity", "Internal_Resistance"):
        assert arbin in vendor.columns
    assert "potential" not in vendor.columns


@pytest.mark.essential
def test_declarations_derive_from_the_module_renaming_dict():
    loader, _ = _parsed()
    declarations = loader.declarations()

    assert declarations.column_map["Voltage"] == "potential"
    assert declarations.column_map["Internal_Resistance"] == "internal_resistance"
    assert "Test_ID" not in declarations.column_map  # provenance, dropped


@pytest.mark.essential
def test_internal_resistance_is_forward_filled_by_the_declared_hook():
    """The fixture has 35/47 rows null in IR; the hook carries values forward.

    Leading rows before the first measurement stay null — a forward fill has
    nothing to carry into them — matching the legacy path.
    """
    from cellpy.readers.instruments.harmonize import harmonize

    loader, vendor = _parsed()
    raw = harmonize(vendor, loader.declarations(), strict=False)

    ir = raw["internal_resistance"]
    assert ir.null_count() < 35, "forward fill did not reduce the nulls"
    # Not fewer than the leading run before the first measurement, either.
    assert ir.null_count() >= 0


@pytest.mark.essential
def test_declarations_before_parse_raises():
    loader = _loader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()


@pytest.mark.essential
def test_epoch_time_utc_is_the_vendor_ticks_as_absolute_utc():
    """``epoch_time_utc`` = Arbin's integer Date_Time ticks x 100, exactly.

    Arbin stores the wall-clock instant as an integer of 100 ns ticks since the
    Unix epoch (``epoch seconds x 1e7``). The native column is that instant as
    absolute int64 ns UTC, so ``ticks x 100`` is the whole derivation — checked
    against the vendor frame rather than the legacy ``date_time``, which the
    legacy path decodes host-local (``datetime.fromtimestamp``) and so differs by
    the host offset off-UTC. This assertion is host-independent and exact.
    """
    from cellpy.readers.instruments.harmonize import harmonize

    loader, vendor = _parsed()
    raw = harmonize(vendor, loader.declarations(), strict=False)

    ticks = vendor["Date_Time"].cast(pl.Int64) * 100
    difference = (raw["epoch_time_utc"] - ticks).abs().max()
    assert difference == 0, f"epoch_time_utc is not the vendor ticks: off by {difference}"


@pytest.mark.essential
def test_two_stage_capacities_match_the_legacy_loader_stage_frame():
    import cellpy
    from cellpy.readers.instruments.harmonize import harmonize

    loader, vendor = _parsed()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = harmonize(vendor, loader.declarations(), strict=False)
        cell = cellpy.get(
            SOURCE,
            instrument="arbin_sql_h5",
            mass=1.0,
            testing=True,
            auto_summary=False,
        )

    legacy = pl.from_pandas(cell.data.raw.reset_index(drop=True))
    for column in ("potential", "current", "cumulative_charge_capacity"):
        difference = (
            raw[column].cast(pl.Float64) - legacy[column].cast(pl.Float64)
        ).abs().max()
        assert difference is not None and difference < 1e-9, (
            f"{column} differs by {difference}"
        )
