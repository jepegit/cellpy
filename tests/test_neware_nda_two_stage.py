"""neware_nda's two-stage declarations (#560).

The real fastnda-based Neware loader (the parked zombie is ``ext_nda_reader``).
It needs the ``fastnda`` backend and an ``.nda*`` file, neither of which is an
in-repo fixture, so — like the fixture-less Arbin variants — it is checked at
the declaration level: vendor→native mapping, ``Test_ID`` dropped as provenance,
and ``datetime_kind="epoch_seconds"`` for its ``unix_time_s`` column.
"""

from __future__ import annotations

import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments import neware_nda


def _declarations():
    """declarations() needs only the static renaming dict, not parsed data (which
    would require fastnda), so we set the parsed flag directly."""
    loader = neware_nda.DataLoader()
    loader._parsed = True
    return loader.declarations()


@pytest.mark.essential
def test_declarations_map_fastnda_columns_to_native():
    column_map = _declarations().column_map
    assert column_map["voltage_V"] == "potential"
    assert column_map["current_mA"] == "current"
    assert column_map["charge_capacity_mAh"] == "cumulative_charge_capacity"
    assert column_map["discharge_capacity_mAh"] == "cumulative_discharge_capacity"
    assert column_map["internal_resistance_mOhm"] == "internal_resistance"


@pytest.mark.essential
def test_test_id_is_dropped_as_provenance():
    assert "Test_ID" not in _declarations().column_map


@pytest.mark.essential
def test_unix_time_is_declared_epoch_seconds():
    declarations = _declarations()
    assert declarations.datetime_kind == "epoch_seconds"
    # unix_time_s is kept as the date_time passthrough for harmonize to parse.
    assert declarations.passthrough.get("unix_time_s") == "date_time"


@pytest.mark.essential
def test_declarations_before_parse_raises():
    loader = neware_nda.DataLoader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()
