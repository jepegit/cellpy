"""YAML → TOML migration helper (CLI wiring is issue #454)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cellpy.config.loader import write_toml



def _yaml_section_to_config_key(section: str) -> str | None:
    mapping = {
        "Paths": "paths",
        "FileNames": "file_names",
        "Reader": "reader",
        "Db": "db",
        "DbCols": "db_cols",
        "Batch": "batch",
        "Instruments": "instruments",
        "CellInfo": "defaults",
        "Materials": "defaults",
    }
    return mapping.get(section)


def _camel_to_snake(name: str) -> str:
    if name in {"Arbin", "Maccor", "Neware", "Batmo"}:
        return name
    return "".join(
        [f"_{ch.lower()}" if ch.isupper() else ch for ch in name]
    ).lstrip("_")


def convert_yaml_to_toml_dict(yaml_text: str) -> dict[str, Any]:
    """Convert legacy ``.cellpy_prms_*.conf`` YAML into new-stack TOML-shaped dict."""

    raw = yaml.safe_load(yaml_text) or {}
    out: dict[str, Any] = {}
    cell_info: dict[str, Any] = {}
    materials: dict[str, Any] = {}

    for section, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        key = _yaml_section_to_config_key(section)
        if key is None:
            continue
        if section == "CellInfo":
            cell_info.update(payload)
            continue
        if section == "Materials":
            materials.update(payload)
            continue
        if section == "Paths":
            paths = {}
            for field, value in payload.items():
                paths[_camel_to_snake(field)] = value
            out["paths"] = paths
            continue
        if section == "Instruments":
            instruments: dict[str, Any] = {}
            for field, value in payload.items():
                if isinstance(value, dict):
                    instruments[field] = value
                else:
                    instruments[_camel_to_snake(field)] = value
            out["instruments"] = instruments
            continue
        converted = {}
        for field, value in payload.items():
            converted[_camel_to_snake(field)] = value
        out[key] = converted

    if cell_info or materials:
        defaults: dict[str, Any] = {}
        if cell_info:
            defaults["cell_info"] = cell_info
        if materials:
            defaults["materials"] = materials
        out["defaults"] = defaults
    return out


def convert_yaml_file_to_toml(yaml_path: Path, toml_path: Path) -> None:
    """Write ``cellpy.toml`` from a legacy YAML config file."""

    yaml_text = yaml_path.read_text(encoding="utf-8")
    data = convert_yaml_to_toml_dict(yaml_text)
    write_toml(toml_path, data)
