"""Layered config loading and TOML I/O."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs
from dotenv import dotenv_values

from cellpy.config.models import CellpyConfig
from cellpy.config.sources import ProvenanceRegistry, SourceLayer

CONFIG_FILENAME = "cellpy.toml"

_LEGACY_SECRET_ENV = {
    "password": "CELLPY_PASSWORD",
    "key_filename": "CELLPY_KEY_FILENAME",
    "host": "CELLPY_HOST",
    "user": "CELLPY_USER",
}


@dataclass
class LoadOptions:
    """Hooks for tests and explicit reload paths."""

    user_config_file: Path | None = None
    project_config_file: Path | None = None
    env_file: Path | None = None
    cwd: Path | None = None
    skip_files: bool = False
    skip_env: bool = False


@dataclass
class LoadResult:
    config: CellpyConfig
    provenance: ProvenanceRegistry = field(default_factory=ProvenanceRegistry)


def user_config_path() -> Path:
    return Path(platformdirs.user_config_dir("cellpy")) / CONFIG_FILENAME


def find_project_config_file(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` (default cwd) looking for ``cellpy.toml``."""

    current = (start or Path.cwd()).resolve()
    root = current.anchor
    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        if str(current) == root or current.parent == current:
            return None
        current = current.parent


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _collect_env_overrides(env_file: Path | None) -> dict[str, Any]:
    raw: dict[str, str | None] = {}
    if env_file and env_file.is_file():
        raw.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})
    for key, value in os.environ.items():
        if key.startswith("CELLPY_"):
            raw[key] = value

    config_overlay: dict[str, Any] = {}
    secrets_overlay: dict[str, Any] = {}

    for env_key, value in raw.items():
        if not env_key.startswith("CELLPY_"):
            continue
        if env_key in _LEGACY_SECRET_ENV.values():
            secret_field = next(k for k, v in _LEGACY_SECRET_ENV.items() if v == env_key)
            secrets_overlay[secret_field] = value
            continue
        if env_key == "CELLPY_":
            continue
        body = env_key[len("CELLPY_") :]
        if "__" not in body:
            continue
        section, field_name = body.split("__", 1)
        section_key = section.lower()
        config_overlay.setdefault(section_key, {})
        config_overlay[section_key][_env_field_to_attr(field_name)] = value

    if secrets_overlay:
        config_overlay["secrets"] = secrets_overlay
    return config_overlay


def _env_field_to_attr(name: str) -> str:
    return name.lower()


def _record_layer(registry: ProvenanceRegistry, layer: SourceLayer, payload: dict[str, Any]) -> None:
    if payload:
        registry.record(layer, payload)


def load_config(
    overrides: dict[str, Any] | None = None,
    options: LoadOptions | None = None,
) -> LoadResult:
    """Build ``CellpyConfig`` from layered sources."""

    opts = options or LoadOptions()
    registry = ProvenanceRegistry()
    base = CellpyConfig().model_dump()

    merged = dict(base)
    _record_layer(registry, SourceLayer.DEFAULT, base)

    user_file_path: Path | None = None
    if not opts.skip_files:
        user_file = opts.user_config_file or user_config_path()
        if user_file.is_file():
            user_file_path = user_file
            user_data = _read_toml(user_file)
            merged = _deep_merge(merged, user_data)
            _record_layer(registry, SourceLayer.USER_FILE, user_data)

        project_file = opts.project_config_file
        if project_file is None and not opts.skip_files:
            project_file = find_project_config_file(opts.cwd)
        if (
            project_file
            and project_file.is_file()
            and project_file != user_file_path
        ):
            project_data = _read_toml(project_file)
            merged = _deep_merge(merged, project_data)
            _record_layer(registry, SourceLayer.PROJECT_FILE, project_data)

    if not opts.skip_env:
        env_path = opts.env_file
        if env_path is None:
            env_path = Path(merged.get("paths", {}).get("env_file", Path.home() / ".env_cellpy"))
        env_data = _collect_env_overrides(Path(env_path) if env_path else None)
        if env_data:
            merged = _deep_merge(merged, env_data)
            _record_layer(registry, SourceLayer.ENV, env_data)

    if overrides:
        merged = _deep_merge(merged, overrides)
        _record_layer(registry, SourceLayer.RUNTIME, overrides)

    config = CellpyConfig.model_validate(merged)
    return LoadResult(config=config, provenance=registry)


def write_toml(path: Path, data: dict[str, Any]) -> None:
    """Write a nested dict as TOML (stdlib read; minimal writer)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_toml(data), encoding="utf-8")


def _format_toml(data: dict[str, Any], prefix: str = "") -> str:
    lines: list[str] = []
    tables: list[tuple[str, dict[str, Any]]] = []
    for key, value in data.items():
        if isinstance(value, dict) and value:
            tables.append((key, value))
        else:
            lines.append(f"{key} = {_format_toml_value(value)}")
    body = "\n".join(lines)
    out: list[str] = []
    if body:
        out.append(body)
    for key, table in tables:
        header = f"{prefix}.{key}" if prefix else key
        out.append(f"\n[{header}]\n{_format_toml_table(table)}")
        for sub_key, sub_val in table.items():
            if isinstance(sub_val, dict) and sub_val:
                out.append(
                    f"\n[{header}.{sub_key}]\n{_format_toml_table(sub_val)}"
                )
    return "\n".join(out).strip() + "\n"


def _format_toml_table(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict) or value is None:
            continue
        lines.append(f"{key} = {_format_toml_value(value)}")
    return "\n".join(lines)


def _format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        inner = ", ".join(_format_toml_value(v) for v in value)
        return f"[{inner}]"
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
