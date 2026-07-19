"""Layered config loading and TOML I/O."""

from __future__ import annotations

import logging
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs
from dotenv import dotenv_values

from cellpy.config.models import CellpyConfig
from cellpy.config.sources import ProvenanceRegistry, SourceLayer
from cellpy.exceptions import ConfigurationError

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
    legacy_yaml_file: Path | None = None


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
        if value is None:
            continue
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _strip_none_values(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` entries (legacy YAML often omits or nulls optional fields)."""

    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, dict):
            nested = _strip_none_values(value)
            if nested:
                cleaned[key] = nested
        else:
            cleaned[key] = value
    return cleaned


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


def _reject_secrets_from_file(data: dict[str, Any], path: Path) -> None:
    """Refuse a ``[secrets]`` section in a config file (config plan decision 5).

    Secrets are env-only. Silently ignoring the section would be worse than
    failing: the user would believe the credential was configured. Name the
    env vars so the error is also the instruction.
    """
    secrets = data.get("secrets")
    if not secrets:
        return
    fields = ", ".join(sorted(secrets)) if isinstance(secrets, dict) else "secrets"
    env_vars = ", ".join(
        _LEGACY_SECRET_ENV[f] for f in sorted(secrets) if f in _LEGACY_SECRET_ENV
    ) or ", ".join(sorted(_LEGACY_SECRET_ENV.values()))
    raise ConfigurationError(
        f"{path} contains a [secrets] section ({fields}). Credentials are read "
        f"from the environment only — set {env_vars} in your environment or "
        f"your .env file instead, and remove the section from the file."
    )


def _drop_legacy_secrets(data: dict[str, Any], path: Path) -> None:
    """Strip credentials from a *legacy YAML* layer, in place, with a warning.

    Unlike a hand-written ``cellpy.toml``, a legacy YAML is a file the user is
    migrating *from* — it may carry the old plain-text ``SQL_PWD``. Refusing to
    load it would strand them, so drop the section and say so.
    """
    secrets = data.pop("secrets", None)
    if secrets:
        logging.warning(
            "%s carries credentials (%s); these are ignored — cellpy 2 reads "
            "them from the environment only (%s). See the configuration docs.",
            path,
            ", ".join(sorted(secrets)) if isinstance(secrets, dict) else "secrets",
            ", ".join(sorted(_LEGACY_SECRET_ENV.values())),
        )


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
        from cellpy.config.legacy import find_legacy_yaml_file, load_legacy_yaml_dict

        user_file = opts.user_config_file or user_config_path()
        user_toml_loaded = False
        if user_file.is_file():
            user_file_path = user_file
            user_toml_loaded = True
            user_data = _read_toml(user_file)
            _reject_secrets_from_file(user_data, user_file)
            merged = _deep_merge(merged, user_data)
            _record_layer(registry, SourceLayer.USER_FILE, user_data)

        if not user_toml_loaded:
            legacy_path = opts.legacy_yaml_file or find_legacy_yaml_file()
            if legacy_path is not None and legacy_path.is_file():
                legacy_data = load_legacy_yaml_dict(legacy_path)
                # A legacy YAML may legitimately carry the old plain-text
                # SQL_PWD; drop it with a warning rather than refusing to load
                # a file the user did not write in this format.
                _drop_legacy_secrets(legacy_data, legacy_path)
                merged = _deep_merge(merged, legacy_data)
                _record_layer(registry, SourceLayer.USER_FILE, legacy_data)

        project_file = opts.project_config_file
        if project_file is None and not opts.skip_files:
            project_file = find_project_config_file(opts.cwd)
        if (
            project_file
            and project_file.is_file()
            and project_file != user_file_path
        ):
            project_data = _read_toml(project_file)
            _reject_secrets_from_file(project_data, project_file)
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
        merged = _deep_merge(merged, _strip_none_values(overrides))
        _record_layer(registry, SourceLayer.RUNTIME, overrides)

    config = CellpyConfig.model_validate(_strip_none_values(merged))
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
