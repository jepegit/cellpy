"""Deprecated ``prms`` → ``cellpy.config`` forwarding (issue #453)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from cellpy._deprecation import warn_once
from cellpy.config.session import get_config

_SECTION_TO_CONFIG: dict[str, tuple[str, str]] = {
    "Paths": ("paths", "cellpy.config.paths"),
    "FileNames": ("file_names", "cellpy.config.file_names"),
    "Reader": ("reader", "cellpy.config.reader"),
    "Db": ("db", "cellpy.config.db"),
    "DbCols": ("db_cols", "cellpy.config.db_cols"),
    "Batch": ("batch", "cellpy.config.batch"),
    "Instruments": ("instruments", "cellpy.config.instruments"),
    "CellInfo": ("defaults.cell_info", "cellpy.config.defaults.cell_info"),
    "Materials": ("defaults.materials", "cellpy.config.defaults.materials"),
}

_SHIM_SECTIONS = frozenset(_SECTION_TO_CONFIG)

_LEGACY_ARBIN_SQL_KEYS = {
    "SQL_server": ("host", "cellpy.config.secrets.host"),
    "SQL_UID": ("user", "cellpy.config.secrets.user"),
    "SQL_PWD": ("password", "cellpy.config.secrets.password"),
    "SQL_Driver": (None, None),
}


def _resolve_config_path(path: str) -> Any:
    obj: Any = get_config()
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def _warn_section(legacy_name: str, replacement: str) -> None:
    warn_once(f"prms.{legacy_name}", replacement)


class _SectionProxy:
    """Forward attribute access to a pydantic config section."""

    def __init__(self, legacy_name: str, config_path: str, replacement: str) -> None:
        object.__setattr__(self, "_legacy_name", legacy_name)
        object.__setattr__(self, "_config_path", config_path)
        object.__setattr__(self, "_replacement", replacement)

    def _target(self) -> Any:
        return _resolve_config_path(self._config_path)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        _warn_section(self._legacy_name, self._replacement)
        value = getattr(self._target(), name)
        if self._legacy_name == "Instruments" and isinstance(value, BaseModel):
            return _InstrumentConfigProxy(self._legacy_name, name, value)
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        _warn_section(self._legacy_name, self._replacement)
        setattr(self._target(), name, value)

    def __repr__(self) -> str:
        return f"<deprecated prms.{self._legacy_name} shim → {self._replacement}>"


class _InstrumentConfigProxy:
    """Instrument subsection with legacy ``__getitem__`` SQL compat."""

    def __init__(self, section_name: str, instrument_name: str, model: BaseModel) -> None:
        object.__setattr__(self, "_section_name", section_name)
        object.__setattr__(self, "_instrument_name", instrument_name)
        object.__setattr__(self, "_model", model)

    def _warn(self) -> None:
        _warn_section(
            self._section_name,
            _SECTION_TO_CONFIG[self._section_name][1],
        )

    def __getattr__(self, name: str) -> Any:
        self._warn()
        return getattr(self._model, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self._warn()
        setattr(self._model, name, value)

    def __getitem__(self, key: str) -> Any:
        self._warn()
        if self._instrument_name == "Arbin" and key in _LEGACY_ARBIN_SQL_KEYS:
            secret_field, replacement = _LEGACY_ARBIN_SQL_KEYS[key]
            if secret_field is not None and replacement is not None:
                warn_once(f"prms.Instruments.Arbin[{key!r}]", replacement)
                secrets = get_config().secrets
                # The legacy shim promised a plain string; unwrap the SecretStr
                # here rather than leaking the wrapper into 1.x-shaped code.
                if secret_field == "password":
                    return secrets.get_password()
                return getattr(secrets, secret_field)
        if hasattr(self._model, key):
            return getattr(self._model, key)
        extras = getattr(self._model, "model_extra", None) or {}
        if key in extras:
            return extras[key]
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._warn()
        if self._instrument_name == "Arbin" and key in _LEGACY_ARBIN_SQL_KEYS:
            secret_field, replacement = _LEGACY_ARBIN_SQL_KEYS[key]
            if secret_field is not None and replacement is not None:
                warn_once(f"prms.Instruments.Arbin[{key!r}]", replacement)
                setattr(get_config().secrets, secret_field, value)
                return
        if hasattr(self._model, key):
            setattr(self._model, key, value)
            return
        setattr(self._model, key, value)

    def keys(self) -> list[str]:
        self._warn()
        data = self._model.model_dump()
        return list(data.keys())

    def __iter__(self):
        self._warn()
        return iter(self.keys())

    def __contains__(self, key: object) -> bool:
        self._warn()
        try:
            self[key]
        except KeyError:
            return False
        return True

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> dict[str, Any]:
        self._warn()
        return self._model.model_dump()


class _InstrumentsProxy(_SectionProxy):
    """``prms.Instruments`` with instrument-level proxies."""

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        _warn_section(self._legacy_name, self._replacement)
        value = getattr(self._target(), name)
        if isinstance(value, BaseModel):
            return _InstrumentConfigProxy(self._legacy_name, name, value)
        return value


def _get_shim_section(name: str) -> Any:
    config_path, replacement = _SECTION_TO_CONFIG[name]
    if name == "Instruments":
        return _InstrumentsProxy(name, config_path, replacement)
    return _SectionProxy(name, config_path, replacement)
