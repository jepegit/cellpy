"""Shared Arbin SQL credential resolution for instrument loaders."""

from __future__ import annotations

import cellpy.config as config
from cellpy.config import credentials
from cellpy.exceptions import ConfigurationError

# No password default: shipping "ChangeMe123" meant a misconfigured setup
# silently attempted a login with a known credential instead of telling the
# user what was missing (config plan decision 5 — removed, not migrated).
_DEFAULTS = {
    "SQL_server": r"localhost\SQLEXPRESS",
    "SQL_UID": "sa",
    "SQL_Driver": "SQL Server",
}

_SECRET_MAP = {
    "SQL_server": "host",
    "SQL_UID": "user",
    "SQL_PWD": "password",
}

_SECRET_ENV = {
    "host": "CELLPY_HOST",
    "user": "CELLPY_USER",
    "password": "CELLPY_PASSWORD",
}


def arbin_sql_value(key: str) -> str:
    """Resolve a legacy Arbin SQL setting from secrets, extras, or defaults."""

    secret_field = _SECRET_MAP.get(key)
    if secret_field is not None:
        # One resolution path for every consumer: session config first, live
        # environment as fallback (cellpy.config.credentials).
        secret_val = getattr(credentials, f"get_{secret_field}")()
        if secret_val:
            return secret_val
        if secret_field == "password":
            raise ConfigurationError(
                f"No Arbin SQL password configured. Set {_SECRET_ENV['password']} "
                f"in your environment or .env file — cellpy 2 does not ship a "
                f"default password."
            )

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
        # SecretsConfig validates on assignment, so a plain string is coerced
        # into the SecretStr for the password field.
        setattr(config.secrets, secret_field, value)
        return
    setattr(config.instruments.Arbin, key, value)
