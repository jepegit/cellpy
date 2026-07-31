"""Essential tests for ``instrument_meta_schema`` (issue #800)."""

from __future__ import annotations

import pytest

import cellpy
from cellpy.readers.data_structures import instrument_meta_schema


@pytest.mark.essential
def test_instrument_meta_schema_shape():
    schema = instrument_meta_schema("maccor_txt")
    assert schema["instrument"] == "maccor_txt"
    assert "fields" in schema and "units" in schema
    names = [f["name"] for f in schema["fields"]]
    assert "mass" in names
    assert "area" in names
    assert "nominal_capacity" in names
    mass = next(f for f in schema["fields"] if f["name"] == "mass")
    assert mass["required"] is True
    assert mass["maps_to"] == "mass"
    assert "mass" in schema["units"]


@pytest.mark.essential
def test_instrument_meta_schema_top_level_export():
    schema = cellpy.instrument_meta_schema()
    assert schema["instrument"] is None
    assert any(f["name"] == "cycle_mode" for f in schema["fields"])
