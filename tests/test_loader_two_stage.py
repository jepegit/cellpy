"""The two-stage entry points on the shipped loaders (#560).

``parse()`` exposes the vendor stage and ``declarations()`` the declared stage,
so ``harmonize(parse(source), declarations())`` can be driven directly rather
than reconstructed by wrapping ``query_file``. Nothing here changes how
``loader()`` behaves — the legacy path is still what ingestion runs.

The case worth the most attention is ``declarations()`` being **per file**:
neware writes its units into its column names, and which units those are comes
from the file, not the configuration.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers import data_structures as ds
from cellpy.readers.instruments.harmonize import harmonize

#: instrument, source, loader kwargs — the parity cases, driven the new way.
CASES = (
    ("maccor_txt", "testdata/data/maccor_001.txt", {"model": "one", "sep": "\t"}),
    ("neware_txt", "testdata/data/neware_uio.csv", {"model": "one"}),
    ("maccor_txt", "testdata/data/maccor_002.txt", {"model": "two"}),
)


def _loader(instrument, **kwargs):
    return ds.generate_default_factory().create(instrument, **kwargs)


@pytest.mark.essential
@pytest.mark.parametrize("instrument, source, kwargs", CASES)
def test_parse_then_harmonize_produces_a_native_frame(instrument, source, kwargs):
    """The two stages compose into the harmonized-raw schema."""
    model = kwargs.get("model")
    loader = _loader(instrument, model=model) if model else _loader(instrument)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse(source, **kwargs)
        raw = harmonize(vendor, loader.declarations(), strict=False)

    assert raw.height == len(vendor)
    for column in ("cycle_num", "step_num", "current", "potential"):
        assert column in raw.columns, f"{column} missing from the harmonized frame"


@pytest.mark.essential
@pytest.mark.parametrize("instrument, source, kwargs", CASES)
def test_parse_returns_vendor_names_not_native_ones(instrument, source, kwargs):
    """``parse()`` is the *vendor* stage — renaming belongs to harmonize."""
    model = kwargs.get("model")
    loader = _loader(instrument, model=model) if model else _loader(instrument)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse(source, **kwargs)

    assert "potential" not in vendor.columns
    assert "cumulative_charge_capacity" not in vendor.columns


@pytest.mark.essential
def test_declarations_reflect_the_units_in_the_file_not_the_config_default():
    """The reason ``declarations()`` cannot be a class attribute.

    ``neware_txt_one`` defaults to ``mA``/``mAh`` and spells its columns
    ``Current({{ current }})``. ``neware_uio.csv`` is in ``A``/``Ah``, and the
    loader corrects the units while parsing. So the vendor column names — the
    keys of ``column_map`` — depend on the file, and declarations read before
    the parse would name columns the file does not contain.
    """
    loader = _loader("neware_txt", model="one")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse("testdata/data/neware_uio.csv", model="one")
        declarations = loader.declarations()

    assert "Current(A)" in declarations.column_map, (
        f"expected the file's own units in the vendor names, got "
        f"{sorted(declarations.column_map)}"
    )
    assert "Current(mA)" not in declarations.column_map, "used the config default"
    # And the names really are the file's.
    assert "Current(A)" in vendor.columns


@pytest.mark.essential
def test_declarations_before_parse_raises_instead_of_guessing():
    """Silence here would mean silently unmapped columns, not an error."""
    loader = _loader("neware_txt", model="one")

    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()


@pytest.mark.essential
def test_the_two_stages_agree_with_the_legacy_frame():
    """Same value parity as the oracle, reached through the public entry points.

    ``test_loader_port_parity`` gets its vendor frame by wrapping
    ``query_file``. If ``parse()`` did anything different, that oracle would be
    testing a path nothing uses.
    """
    import cellpy

    loader = _loader("neware_txt", model="one")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse("testdata/data/neware_uio.csv", model="one")
        raw = harmonize(vendor, loader.declarations(), strict=False)
        cell = cellpy.get(
            "testdata/data/neware_uio.csv",
            instrument="neware_txt",
            model="one",
            mass=1.0,
            testing=True,
        )

    legacy = pl.from_pandas(cell.data.raw.reset_index(drop=True))
    for column in ("cumulative_charge_capacity", "cumulative_discharge_capacity"):
        difference = (
            raw[column].cast(pl.Float64) - legacy[column].cast(pl.Float64)
        ).abs().max()
        assert difference is not None and difference < 1e-9, (
            f"{column} differs by {difference} between the two-stage path and "
            f"the legacy path"
        )


@pytest.mark.essential
def test_unit_labels_override_lands_in_unit_labels_not_raw_limits():
    """A ``unit_labels=`` override must reach ``config_params.unit_labels``.

    Regression for a copy-paste slip where the ``unit_labels`` branch of
    ``parse_loader_parameters`` updated ``raw_limits`` instead. The symptom was
    that vendor column-name templates (neware spells its columns
    ``Current({{ current }})``) could not be overridden this way, while the
    unit-label strings silently polluted ``raw_limits``.
    """
    loader = _loader("neware_txt", model="one")
    raw_limits_before = dict(loader.config_params.raw_limits)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # sep is given so the branch runs without touching the auto-formatter.
        loader.parse_loader_parameters(sep="\t", unit_labels={"current": "A"})

    assert loader.config_params.unit_labels["current"] == "A", (
        "unit_labels override did not reach config_params.unit_labels"
    )
    assert dict(loader.config_params.raw_limits) == raw_limits_before, (
        "unit_labels override leaked into config_params.raw_limits"
    )
