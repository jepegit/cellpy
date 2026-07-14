"""Helpers for config stack characterization tests (issue #452)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cellpy.config.models import CellpyConfig, default_inventory_config
from tests.prms_support import (
    EXPECTED_PRMS_INVENTORY,
    INVENTORY_ROOT,
    _flatten_section,
    _normalize_value,
    assert_inventory_equal,
)

# Legacy instrument SQL credentials moved to env-only ``secrets`` (issue #452 plan).
EXCLUDED_INVENTORY_TRIPLES: set[tuple[str, str]] = {
    ("Instruments", "Arbin.SQL_Driver"),
    ("Instruments", "Arbin.SQL_PWD"),
    ("Instruments", "Arbin.SQL_UID"),
    ("Instruments", "Arbin.SQL_server"),
}


def _paths_dict(config: CellpyConfig) -> dict[str, Any]:
    paths = config.paths.model_dump(mode="json")
    return {key: _normalize_value(value) for key, value in paths.items()}


def _instruments_dict(config: CellpyConfig) -> dict[str, Any]:
    data = config.instruments.model_dump(mode="json")
    flat: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                flat[f"{key}.{sub_key}"] = _normalize_value(sub_val)
        else:
            flat[key] = _normalize_value(value)
    return flat


def flatten_config_to_legacy_triples(config: CellpyConfig) -> list[tuple[str, str, Any]]:
    """Map new-stack config back to #430 ``(section, field, default)`` triples."""

    inventory: list[tuple[str, str, Any]] = []
    inventory.extend(_flatten_section("Paths", _paths_dict(config)))
    inventory.extend(
        _flatten_section("FileNames", config.file_names.model_dump(mode="json"))
    )
    inventory.extend(_flatten_section("Db", config.db.model_dump(mode="json")))
    inventory.extend(_flatten_section("DbCols", config.db_cols.model_dump(mode="json")))
    inventory.extend(_flatten_section("Reader", config.reader.model_dump(mode="json")))
    inventory.extend(
        _flatten_section("CellInfo", config.defaults.cell_info.model_dump(mode="json"))
    )
    inventory.extend(
        _flatten_section("Materials", config.defaults.materials.model_dump(mode="json"))
    )
    inventory.extend(_flatten_section("Instruments", _instruments_dict(config)))
    inventory.extend(_flatten_section("Batch", config.batch.model_dump(mode="json")))
    return sorted(inventory, key=lambda t: (t[0], t[1]))


def collect_config_inventory(root: Path | None = None) -> list[tuple[str, str, Any]]:
    config = default_inventory_config(root or INVENTORY_ROOT)
    return flatten_config_to_legacy_triples(config)


def expected_prms_inventory_for_config() -> list[tuple[str, str, object]]:
    return [
        triple
        for triple in EXPECTED_PRMS_INVENTORY
        if (triple[0], triple[1]) not in EXCLUDED_INVENTORY_TRIPLES
    ]


def assert_config_inventory_parity(actual: list[tuple[str, str, Any]]) -> None:
    assert_inventory_equal(actual, expected_prms_inventory_for_config())
