"""The one place that resolves cellpy credentials.

Before this module four call sites — ``internals/otherpath.py``,
``internals/connections.py``, ``readers/filefinder.py`` and
``readers/instruments/arbin_sql_config.py`` — each knew the ``CELLPY_*``
environment variable names and each read them with a bare ``os.getenv``. That
is the scatter the config plan set out to remove: four places to update when a
variable is renamed, and four different answers when one of them is stale.

Resolution order, per credential:

1. the **session config** (``cellpy.config.secrets``) — this is where the
   config loader has already deposited the environment and ``.env`` layers, and
   where an explicit runtime assignment lands;
2. the **live environment** — consulted only if the session value is unset, so
   that a variable exported *after* cellpy was imported still works (a normal
   notebook pattern) without letting the environment silently override a value
   the user set deliberately at runtime.

Credentials are never read from a config file: the loader refuses a
``[secrets]`` section outright (config plan decision 5).
"""

from __future__ import annotations

import os
from pathlib import Path

from cellpy.config.models import SecretsConfig

# The only place these names are written down.
ENV_VARS = {
    "password": "CELLPY_PASSWORD",
    "key_filename": "CELLPY_KEY_FILENAME",
    "host": "CELLPY_HOST",
    "user": "CELLPY_USER",
}


def _session_secrets() -> SecretsConfig:
    # Imported lazily: cellpy.config builds the session on first attribute
    # access, and this module must not trigger that at import time.
    from cellpy.config.session import get_config

    return get_config().secrets


def _resolve(field: str) -> str | None:
    secrets = _session_secrets()
    value = (
        secrets.get_password() if field == "password" else getattr(secrets, field, None)
    )
    if value:
        return value
    return os.getenv(ENV_VARS[field]) or None


def describe_env_file(env_file: Path | str | None) -> str:
    """Status of a configured env file for error and warning text.

    Empty string when ``env_file`` is unset. Otherwise names the resolved
    path and, if that path is missing, a same-named file under the home
    directory when one exists.
    """
    if env_file is None or env_file == "":
        return ""
    configured = Path(env_file).expanduser()
    resolved = configured.resolve()
    if resolved.is_file():
        return (
            f"Configured env_file {resolved} was found but does not set "
            f"{ENV_VARS['password']} or {ENV_VARS['key_filename']}."
        )
    parts = [f"Configured env_file {configured} resolved to {resolved} and was not found."]
    home_candidate = Path.home() / configured.name
    try:
        home_same = home_candidate.resolve() == resolved
    except OSError:
        home_same = False
    if home_candidate.is_file() and not home_same:
        parts.append(
            f"A file named {configured.name} exists at {home_candidate}; "
            "set paths.env_file to that absolute path."
        )
    else:
        parts.append(
            "Create that file (or run `cellpy setup`) so those variables can be loaded."
        )
    return " ".join(parts)


def missing_remote_credentials_message(env_file: Path | str | None = None) -> str:
    """``UnderDefined`` text when neither password nor key file is set."""
    base = (
        f"You must define either {ENV_VARS['password']} "
        f"or {ENV_VARS['key_filename']} environment variables."
    )
    if env_file is None:
        try:
            from cellpy.config.session import get_config

            env_file = get_config().paths.env_file
        except Exception:
            env_file = None
    hint = describe_env_file(env_file)
    if not hint:
        return base
    return f"{base} {hint}"


def get_password() -> str | None:
    """The ssh/SQL password, or None if unset."""
    return _resolve("password")


def get_key_filename() -> str | None:
    """Path to the ssh key file, or None if unset."""
    return _resolve("key_filename")


def get_host() -> str | None:
    """Remote host, or None if unset."""
    return _resolve("host")


def get_user() -> str | None:
    """Remote user name, or None if unset."""
    return _resolve("user")


def resolve_credentials() -> SecretsConfig:
    """All four credentials as a fresh `SecretsConfig`.

    Convenience for callers that need more than one; the password comes back
    wrapped in a ``SecretStr`` again, so use ``.get_password()`` on the result.
    """
    return SecretsConfig(
        password=get_password(),
        key_filename=get_key_filename(),
        host=get_host(),
        user=get_user(),
    )
