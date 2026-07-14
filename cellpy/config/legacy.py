"""Legacy ``.cellpy_prms_*.conf`` discovery and YAML ingest (issue #453)."""

from __future__ import annotations

import getpass
import glob
import os
import sys
from collections import OrderedDict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cellpy.config.migrate import convert_yaml_to_toml_dict
from cellpy.config.models import CellpyConfig
from cellpy.internals.connections import OtherPath

DEFAULT_FILENAME_START = ".cellpy_prms_"
DEFAULT_FILENAME_END = ".conf"
DEFAULT_FILENAME = DEFAULT_FILENAME_START + "default" + DEFAULT_FILENAME_END
PRM_GLOB = ".cellpy_prms*.conf"
USE_MY_DOCUMENTS = False


def get_user_name() -> str:
    """Return the current username (cross-platform)."""

    return getpass.getuser()


def get_user_dir() -> Path:
    """Return the user home directory (optionally Documents on Windows)."""

    user_dir = Path.home().resolve()
    if os.name == "nt" and USE_MY_DOCUMENTS:
        documents = user_dir / "documents"
        if documents.is_dir():
            return documents
    return user_dir


def find_legacy_yaml_file(
    file_name: str | Path | None = None,
    search_order: Sequence[str] | None = None,
) -> Path | None:
    """Locate a legacy YAML prm file using the historical search order."""

    if file_name is not None:
        candidate = Path(file_name)
        if candidate.is_file():
            return candidate
        return None

    script_dir = Path(__file__).resolve().parents[1] / "parameters"
    search_path = {
        "curdir": Path(os.path.abspath(os.path.dirname(sys.argv[0]))),
        "filedir": script_dir,
        "user_dir": get_user_dir(),
    }
    order = list(search_order or ["user_dir"])

    search_dict: OrderedDict[str, list[str | None]] = OrderedDict()
    for key in order:
        search_dict[key] = [None, None]
        prm_directory = search_path[key]
        default_file = prm_directory / DEFAULT_FILENAME

        if default_file.is_file():
            search_dict[key][0] = str(default_file)

        for match in sorted(glob.glob(str(prm_directory / PRM_GLOB))):
            if Path(match).name != DEFAULT_FILENAME:
                search_dict[key][1] = match
                break

    prm_file: str | None = None
    for file_list in search_dict.values():
        if file_list[1]:
            prm_file = file_list[1]
            break
        if not prm_file and file_list[0]:
            prm_file = file_list[0]

    if prm_file:
        return Path(prm_file)

    fallback = script_dir / DEFAULT_FILENAME
    if fallback.is_file():
        return fallback
    return None


def load_legacy_yaml_dict(path: Path) -> dict:
    """Read a legacy YAML prm file into new-stack-shaped dict."""

    return convert_yaml_to_toml_dict(path.read_text(encoding="utf-8"))


def load_legacy_yaml_overrides(path: Path) -> dict:
    """Alias for :func:`load_legacy_yaml_dict` (explicit reload overrides)."""

    return load_legacy_yaml_dict(path)


def _model_to_legacy_dict(model) -> dict[str, Any]:
    """Export a config section without triggering pydantic serializers."""

    result: dict[str, Any] = {}
    for key in type(model).model_fields:
        value = getattr(model, key)
        if isinstance(value, (Path, OtherPath)):
            result[key] = str(value)
        elif hasattr(value, "model_dump"):
            result[key] = value.model_dump(mode="python")
        else:
            result[key] = value
    return result


def _paths_to_legacy(paths) -> dict:
    return _model_to_legacy_dict(paths)


def export_legacy_yaml_dict(config: CellpyConfig | None = None) -> dict:
    """Build a legacy YAML-shaped dict from the active config stack."""

    from cellpy.config.session import get_config

    cfg = config or get_config()

    instruments = {}
    for key in type(cfg.instruments).model_fields:
        value = getattr(cfg.instruments, key)
        if hasattr(value, "model_dump"):
            instruments[key] = value.model_dump(mode="python")
        else:
            instruments[key] = value

    return {
        "Paths": _paths_to_legacy(cfg.paths),
        "FileNames": _model_to_legacy_dict(cfg.file_names),
        "Db": _model_to_legacy_dict(cfg.db),
        "DbCols": _model_to_legacy_dict(cfg.db_cols),
        "CellInfo": _model_to_legacy_dict(cfg.defaults.cell_info),
        "Reader": _model_to_legacy_dict(cfg.reader),
        "Materials": _model_to_legacy_dict(cfg.defaults.materials),
        "Instruments": instruments,
        "Batch": _model_to_legacy_dict(cfg.batch),
    }
