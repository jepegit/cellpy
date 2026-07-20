"""Declarations derived from the existing configurations (#560).

Deriving vendor→native from what the configurations already say — rather than
retyping sixteen column maps — is the mechanical half of the loader port. These
tests check the derivation against reality: the shipped configurations, and the
frames the legacy path actually produces for the in-tree test files.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
import warnings

import pytest
from cellpycore.config import default_schema
from cellpycore.units import validate_units

from cellpy import log
from cellpy.exceptions import LoaderError
from cellpy.readers.instruments import configurations
from cellpy.readers.instruments.config_declarations import (
    declarations_from_configuration,
    derive_column_maps,
)

log.setup_logging(default_level=logging.DEBUG, testing=True)

SCHEMA = default_schema().raw

#: Configurations that carry a vendor→legacy renaming dict.
TIER_ONE_CONFIGS = (
    "maccor_txt_one",
    "maccor_txt_two",
    "maccor_txt_three",
    "neware_txt_zero",
    "neware_txt_one",
    "neware_txt_two",
)


def _config(name: str):
    return importlib.import_module(
        f"cellpy.readers.instruments.configurations.{name}"
    )


def _all_configuration_modules():
    for info in pkgutil.iter_modules(configurations.__path__):
        if info.name.startswith("_"):
            continue
        yield info.name, importlib.import_module(
            f"cellpy.readers.instruments.configurations.{info.name}"
        )


# -- every shipped configuration must declare valid units ----------------------


@pytest.mark.essential
@pytest.mark.parametrize("name", [n for n, _ in _all_configuration_modules()])
def test_every_shipped_configuration_has_parsable_units(name):
    """Loader plan §5: every shipped configuration passes validate_units.

    This is the test that caught `resistance: "mOhm"` in the three neware
    configurations — pint parses `mohm`, not `mOhm`, so the label had been
    unusable since it was written.
    """
    config = _config(name)
    raw_units = getattr(config, "raw_units", None)
    if not raw_units:
        pytest.skip(f"{name} declares no raw_units")

    from cellpycore.units import CellpyUnits

    known = {
        key: value
        for key, value in raw_units.items()
        if hasattr(CellpyUnits(), key) and isinstance(value, str)
    }
    validate_units(CellpyUnits(**known))


# -- the derivation ------------------------------------------------------------


@pytest.mark.essential
@pytest.mark.parametrize("name", TIER_ONE_CONFIGS)
def test_tier_one_configurations_derive(name):
    """A configuration that cannot be expressed as declarations blocks the port."""
    declarations = declarations_from_configuration(_config(name))
    assert declarations.column_map, f"{name} produced an empty column map"


@pytest.mark.essential
@pytest.mark.parametrize("name", TIER_ONE_CONFIGS)
def test_derived_targets_are_real_native_columns(name):
    declarations = declarations_from_configuration(_config(name))
    native = set(SCHEMA.ordered_names())
    assert set(declarations.column_map.values()) <= native


@pytest.mark.essential
@pytest.mark.parametrize("name", TIER_ONE_CONFIGS)
def test_passthrough_never_shadows_a_native_column(name):
    """A passthrough column must not squat on a name the schema owns."""
    declarations = declarations_from_configuration(_config(name))
    native = set(SCHEMA.ordered_names())
    assert not (set(declarations.passthrough.values()) & native)


@pytest.mark.essential
def test_vendor_test_id_is_not_carried_into_raw():
    """The vendor's Test_ID is provenance, and would collide with test_id.

    Native ``test_id`` is the framework-assigned grouping key for merged tests.
    The vendor's identifier means something else entirely and belongs on
    TestMeta (#508) — letting it through would give one name two meanings, with
    the vendor's value quietly winning.
    """
    config = _config("maccor_txt_one")
    assert "test_id_txt" in config.normal_headers_renaming_dict
    declarations = declarations_from_configuration(config)
    assert SCHEMA.test_id not in declarations.column_map.values()
    assert SCHEMA.test_id not in declarations.passthrough.values()


@pytest.mark.essential
def test_energies_map_natively_since_cellpycore_0_2_3():
    """cellpy-core#139 landed; the energies are real native columns now.

    This test used to assert the opposite — that energy data survived only as a
    passthrough — and was written to fail the moment core added the mapping.
    It did, on the 0.2.3 re-pin, which is what a tripwire is for. No loader or
    configuration changed: the derivation picked the new entries up on its own.
    """
    declarations = declarations_from_configuration(_config("neware_txt_one"))
    assert SCHEMA.cumulative_charge_energy in declarations.column_map.values()
    assert SCHEMA.cumulative_discharge_energy in declarations.column_map.values()
    assert "charge_energy" not in declarations.passthrough.values()


@pytest.mark.essential
def test_date_time_is_still_a_passthrough():
    """The mechanism is still needed: not every legacy column has a native home.

    ``date_time`` has no native counterpart (the native schema carries
    ``epoch_time_utc`` instead, which is not a rename), so it is still carried
    through under its legacy name.
    """
    declarations = declarations_from_configuration(_config("neware_txt_one"))
    assert "date_time" in declarations.passthrough.values()


@pytest.mark.essential
def test_passthrough_shrinks_when_the_mapping_gains_an_entry(monkeypatch):
    """The self-updating property: no loader edit when core#139 lands.

    Simulate the core mapping gaining the energy entry and assert the column
    moves from passthrough into column_map on its own.
    """
    from cellpycore.legacy import mapping

    patched = dict(mapping.LEGACY_ATTR_TO_SCHEMA["raw"])
    patched["charge_energy_txt"] = SCHEMA.cumulative_charge_energy
    monkeypatch.setitem(mapping.LEGACY_ATTR_TO_SCHEMA, "raw", patched)

    renaming = _config("neware_txt_one").normal_headers_renaming_dict
    column_map, passthrough, _ = derive_column_maps(renaming)

    assert SCHEMA.cumulative_charge_energy in column_map.values()
    assert "charge_energy" not in passthrough.values()


# -- parity against the frames the legacy path actually produces ---------------

PARITY_CASES = (
    ("maccor_txt", "maccor_txt_one", "testdata/data/maccor_001.txt",
     {"model": "one", "sep": "\t"}),
    ("neware_txt", "neware_txt_one", "testdata/data/neware_uio.csv",
     {"model": "one"}),
)


def _vendor_header(source: str, config) -> set[str]:
    """The vendor column names actually present in the file.

    Reads the header line directly rather than via a CSV parser: we only want
    the names, and asking a parser for them means it also infers dtypes from
    the data, which then fails on values the inference sample did not cover
    (it did, on Linux, for neware's ``Capacity(Ah)``).
    """
    formatters = getattr(config, "formatters", {}) or {}
    separator = formatters.get("sep") or ","
    skiprows = formatters.get("skiprows", 0) or 0

    with open(source, "r", encoding="utf-8", errors="replace") as handle:
        for _ in range(skiprows):
            handle.readline()
        header = handle.readline()

    return {name.strip() for name in header.rstrip("\n").split(separator)}


@pytest.mark.essential
@pytest.mark.parametrize("instrument, config_name, source, kwargs", PARITY_CASES)
def test_declared_columns_present_in_the_file_reach_the_legacy_frame(
    instrument, config_name, source, kwargs
):
    """Parity of the derivation against what the legacy path really produces.

    Only columns the vendor file *actually contains* are checked: the
    configurations legitimately declare columns for other variants of the same
    format (maccor_txt_one has a whole block commented "not observed yet"), and
    ``harmonize()`` tolerates declared-but-absent columns by design.

    What must hold is the other direction — if the file has a declared vendor
    column, the derivation's target name must be what the legacy path ends up
    calling it. A mismatch here means the port would rename something to the
    wrong place, which produces plausible numbers rather than an error.
    """
    import cellpy

    config = _config(config_name)
    declarations = declarations_from_configuration(config)
    present_vendor = _vendor_header(source, config)

    expected = {
        target
        for vendor, target in {
            **declarations.column_map,
            **declarations.passthrough,
        }.items()
        if vendor in present_vendor
    }
    assert expected, f"no declared column of {config_name} is present in {source}"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cell = cellpy.get(source, instrument=instrument, mass=1.0, testing=True, **kwargs)

    actual = set(cell.data.raw.columns)
    missing = sorted(expected - actual)
    assert not missing, (
        f"{config_name}: columns present in {source} but absent from the legacy "
        f"frame under their derived names: {missing}"
    )


@pytest.mark.essential
def test_derivation_rejects_an_invalid_configuration():
    """A configuration that cannot be expressed must fail at derivation time."""

    class BogusConfig:
        __name__ = "bogus"
        normal_headers_renaming_dict = {"voltage_txt": "V"}
        raw_units = {"voltage": "not_a_unit"}

    with pytest.raises(LoaderError, match="not a valid unit spec"):
        declarations_from_configuration(BogusConfig)


@pytest.mark.essential
def test_ambiguous_vendor_column_is_detected_and_resolved_deterministically():
    """One vendor column claimed by two legacy attributes loses one of them.

    The derivation keeps the first declaration and logs the collision instead
    of picking silently. Synthetic fixture: the real case this was written
    against (`maccor_txt_one` mapping `Watt-hr` to both `power_txt` and
    `charge_energy_txt`) was resolved by decision #560 (2026-07-20) — the
    power mapping was a config slip — so the repo no longer carries a live
    ambiguity to point at.
    """
    renaming = {
        "power_txt": "Watt-hr",
        "charge_energy_txt": "Watt-hr",
        "voltage_txt": "Volts",
    }
    column_map, passthrough, _ = derive_column_maps(renaming)
    targets = {**column_map, **passthrough}
    # power_txt is declared first, so power wins (first-wins, logged).
    assert targets["Watt-hr"] == "power"


@pytest.mark.essential
def test_maccor_txt_one_watt_hr_is_energy():
    """Decision #560 (2026-07-20): a Watt-hr column is dimensionally energy.

    maccor_txt_one used to map it to power_txt *and* charge_energy_txt, and
    first-wins fed it to power. The power mapping is gone; the vendor column
    now lands on charge_energy, and there is no double-claim left in the
    configuration.
    """
    renaming = _config("maccor_txt_one").normal_headers_renaming_dict
    claimed_twice = [
        vendor
        for vendor in set(renaming.values())
        if list(renaming.values()).count(vendor) > 1
    ]
    assert not claimed_twice, f"double-claimed vendor columns: {claimed_twice}"

    column_map, passthrough, _ = derive_column_maps(renaming)
    # Lands on the *native* energy column (cellpycore 0.2.3 gained them via
    # cellpy-core#139), so it is a real mapping, not a passthrough.
    assert column_map["Watt-hr"] == "cumulative_charge_energy"
    assert "Watt-hr" not in passthrough
