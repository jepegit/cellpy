"""Secrets hardening tests (#565, config plan Step 6 / decision 5).

The contract: credentials come from the environment only, never from a config
file, and the password value does not leak through reprs, dumps or logs.
"""

from __future__ import annotations

import logging

import pytest

from cellpy import log
from cellpy.config import credentials
from cellpy.config.loader import LoadOptions, load_config, write_toml
from cellpy.config.models import CellpyConfig, SecretsConfig
from cellpy.exceptions import ConfigurationError

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def hermetic_session():
    """A session config built from defaults only.

    Without this the result depends on whether the machine running the tests
    happens to have a ``~/.env_cellpy`` or a user ``cellpy.toml`` — a real
    developer machine does, CI does not, so a credential test that reads the
    ambient layers passes or fails by accident.
    """
    from cellpy.config import session

    session.reset_session()
    session.reload(options=LoadOptions(skip_env=True, skip_files=True))
    try:
        yield session
    finally:
        session.reset_session()


# -- the password does not leak ------------------------------------------------


@pytest.mark.essential
def test_password_is_not_in_repr():
    secrets = SecretsConfig(password="hunter2")
    assert "hunter2" not in repr(secrets)
    assert "hunter2" not in str(secrets)


@pytest.mark.essential
def test_password_is_not_in_a_model_dump():
    config = CellpyConfig(secrets=SecretsConfig(password="hunter2"))
    assert "hunter2" not in str(config.model_dump())


@pytest.mark.essential
def test_password_is_not_in_the_file_dump():
    config = CellpyConfig(secrets=SecretsConfig(password="hunter2"))
    dumped = config.model_dump_for_file()
    assert "secrets" not in dumped
    assert "hunter2" not in str(dumped)


@pytest.mark.essential
def test_password_comes_out_on_request():
    secrets = SecretsConfig(password="hunter2")
    assert secrets.get_password() == "hunter2"


@pytest.mark.essential
def test_get_password_is_none_when_unset():
    assert SecretsConfig().get_password() is None


# -- credentials never come from a config file ---------------------------------


@pytest.mark.essential
def test_secrets_in_a_user_toml_are_rejected(tmp_path):
    path = tmp_path / "cellpy.toml"
    write_toml(path, {"secrets": {"password": "in-a-file"}})

    with pytest.raises(ConfigurationError) as excinfo:
        load_config(options=LoadOptions(user_config_file=path, skip_env=True))

    message = str(excinfo.value)
    # The error must also be the instruction: name the env var to use instead.
    assert "CELLPY_PASSWORD" in message
    # ... and must not echo the credential it is refusing.
    assert "in-a-file" not in message


@pytest.mark.essential
def test_secrets_in_a_project_toml_are_rejected(tmp_path):
    user = tmp_path / "user" / "cellpy.toml"
    write_toml(user, {"reader": {"auto_dirs": False}})
    project = tmp_path / "project" / "cellpy.toml"
    write_toml(project, {"secrets": {"host": "in-a-file"}})

    with pytest.raises(ConfigurationError):
        load_config(
            options=LoadOptions(
                user_config_file=user, project_config_file=project, skip_env=True
            )
        )


@pytest.mark.essential
def test_a_clean_toml_still_loads(tmp_path):
    path = tmp_path / "cellpy.toml"
    write_toml(path, {"reader": {"auto_dirs": False}})
    result = load_config(options=LoadOptions(user_config_file=path, skip_env=True))
    assert result.config.reader.auto_dirs is False


# -- resolution order ----------------------------------------------------------


@pytest.mark.essential
def test_environment_is_picked_up_when_the_session_value_is_unset(
    hermetic_session, monkeypatch
):
    # Exporting a variable after import is a normal notebook pattern; the
    # session here was built with skip_env, so this exercises the fallback.
    monkeypatch.setenv("CELLPY_PASSWORD", "from-env")
    assert credentials.get_password() == "from-env"


@pytest.mark.essential
def test_a_runtime_assignment_beats_the_environment(hermetic_session, monkeypatch):
    # The environment must not silently override a value set deliberately.
    monkeypatch.setenv("CELLPY_HOST", "from-env")
    hermetic_session.get_config().secrets.host = "set-at-runtime"
    assert credentials.get_host() == "set-at-runtime"


@pytest.mark.essential
def test_env_var_names_live_in_one_place():
    # The point of the module: four call sites no longer each know these.
    assert credentials.ENV_VARS == {
        "password": "CELLPY_PASSWORD",
        "key_filename": "CELLPY_KEY_FILENAME",
        "host": "CELLPY_HOST",
        "user": "CELLPY_USER",
    }


# -- no shipped default password ------------------------------------------------


@pytest.mark.essential
def test_no_default_arbin_sql_password(hermetic_session, monkeypatch):
    """Shipping "ChangeMe123" made a misconfigured setup look like a bad login."""
    from cellpy.readers.instruments import arbin_sql_config

    monkeypatch.delenv("CELLPY_PASSWORD", raising=False)
    with pytest.raises(ConfigurationError, match="CELLPY_PASSWORD"):
        arbin_sql_config.arbin_sql_value("SQL_PWD")


@pytest.mark.essential
def test_arbin_sql_password_from_env(hermetic_session, monkeypatch):
    from cellpy.readers.instruments import arbin_sql_config

    monkeypatch.setenv("CELLPY_PASSWORD", "from-env")
    assert arbin_sql_config.arbin_sql_value("SQL_PWD") == "from-env"


@pytest.mark.essential
def test_non_secret_arbin_settings_still_resolve(hermetic_session):
    from cellpy.readers.instruments import arbin_sql_config

    # Resolves from the Arbin instrument config; the point is only that
    # dropping the password default did not disturb the non-secret path.
    assert arbin_sql_config.arbin_sql_value("SQL_Driver")
    assert arbin_sql_config.arbin_sql_value("SQL_server")


# -- the generated configuration reference --------------------------------------


@pytest.mark.essential
def test_configuration_reference_matches_the_models():
    """The docs page is generated; if you add a field, regenerate it.

    ```shell
    uv run python -m cellpy.config.reference
    ```
    """
    from pathlib import Path

    from cellpy.config import reference

    repo_root = Path(__file__).resolve().parents[1]
    on_disk = (repo_root / reference.DOC_PATH).read_text(encoding="utf-8")
    assert on_disk == reference.render_reference_md()


@pytest.mark.essential
def test_configuration_reference_has_no_machine_specific_paths():
    """Defaults are computed from cwd/home; they must not reach the page.

    Otherwise the generating machine's directory layout and user name end up
    in published documentation, and the check above can only pass on one
    machine.
    """
    from pathlib import Path

    from cellpy.config import reference

    rendered = reference.render_reference_md()
    assert str(Path.home()) not in rendered
    assert str(Path.cwd()) not in rendered
    assert "<home>" in rendered
    assert "<current directory>" in rendered


@pytest.mark.essential
def test_configuration_reference_documents_secrets_without_values():
    from cellpy.config import reference

    rendered = reference.render_reference_md()
    assert "CELLPY_PASSWORD" in rendered
    # The secrets section documents the env var, never a default value.
    assert "ChangeMe123" not in rendered
