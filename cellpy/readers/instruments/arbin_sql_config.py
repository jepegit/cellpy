"""Shared Arbin SQL credential resolution for instrument loaders."""

from __future__ import annotations

import os

import cellpy.config as config

_DEFAULTS = {
    "SQL_server": r"localhost\SQLEXPRESS",
    "SQL_UID": "sa",
    "SQL_PWD": "ChangeMe123",
    "SQL_Driver": "SQL Server",
}

_SECRET_MAP = {
    "SQL_server": "host",
    "SQL_UID": "user",
    "SQL_PWD": "password",
}


def arbin_sql_value(key: str) -> str:
    """Resolve a legacy Arbin SQL setting from secrets, extras, or defaults."""

    secret_field = _SECRET_MAP.get(key)
    if secret_field is not None:
        secret_val = getattr(config.secrets, secret_field, None)
        if secret_val:
            return secret_val
        env_key = {
            "host": "CELLPY_HOST",
            "user": "CELLPY_USER",
            "password": "CELLPY_PASSWORD",
        }[secret_field]
        env_val = os.getenv(env_key)
        if env_val:
            return env_val

    arbin = config.instruments.Arbin
    if hasattr(arbin, key):
        value = getattr(arbin, key)
        if value is not None:
            return value
    extras = arbin.model_extra or {}
    if key in extras and extras[key] is not None:
        return extras[key]
    return _DEFAULTS[key]


def set_arbin_sql_value(key: str, value: str) -> None:
    """Write a legacy Arbin SQL setting (secrets for auth fields)."""

    secret_field = _SECRET_MAP.get(key)
    if secret_field is not None:
        setattr(config.secrets, secret_field, value)
        return
    setattr(config.instruments.Arbin, key, value)
