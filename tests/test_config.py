"""Tests for the parallel pydantic config stack (issue #452)."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib
from cellpycore.units import CellpyUnits

from cellpy.config import LoadOptions, override, reload, reset_session, set_load_options, sources
from cellpy.config.loader import load_config, write_toml
from cellpy.config.migrate import convert_yaml_to_toml_dict
from cellpy.config.models import UnitsConfig
from cellpy.config.sources import SourceLayer
from tests.config_support import assert_config_inventory_parity, collect_config_inventory
from tests.prms_support import INVENTORY_ROOT


@pytest.fixture(autouse=True)
def _reset_config_session():
    reset_session()
    yield
    reset_session()


@pytest.fixture
def isolated_config():
    """Leak-free scoped config for tests."""

    with override():
        from cellpy.config import get_config

        yield get_config()


@pytest.mark.essential
def test_config_inventory_parity():
    actual = collect_config_inventory()
    assert_config_inventory_parity(actual)


@pytest.mark.essential
def test_units_defaults_match_cellpycore():
    expected = {key: getattr(CellpyUnits(), key) for key in CellpyUnits().keys()}
    actual = UnitsConfig().model_dump()
    assert actual == expected


@pytest.mark.essential
def test_config_override_fixture(isolated_config):
    assert isolated_config.reader.cycle_mode == "anode"
    with override(reader={"cycle_mode": "cathode"}):
        from cellpy.config import reader

        assert reader.cycle_mode == "cathode"
    assert isolated_config.reader.cycle_mode == "anode"


def test_config_override_nested_stack():
    with override(reader={"cycle_mode": "cathode"}):
        from cellpy.config import reader as reader_outer

        assert reader_outer.cycle_mode == "cathode"
        with override(reader={"cycle_mode": "lithium"}):
            from cellpy.config import reader as reader_inner

            assert reader_inner.cycle_mode == "lithium"
        assert reader_outer.cycle_mode == "cathode"


def test_loader_user_file_overrides_default(tmp_path, monkeypatch):
    user_file = tmp_path / "cellpy.toml"
    write_toml(user_file, {"reader": {"cycle_mode": "cathode"}})
    result = load_config(
        options=LoadOptions(user_config_file=user_file, cwd=tmp_path, skip_env=True)
    )
    assert result.config.reader.cycle_mode == "cathode"
    assert result.provenance.get("reader.cycle_mode") == SourceLayer.USER_FILE


def test_loader_project_file_overrides_user(tmp_path):
    user_file = tmp_path / "user.toml"
    project_file = tmp_path / "project.toml"
    write_toml(user_file, {"reader": {"cycle_mode": "cathode"}})
    write_toml(project_file, {"reader": {"cycle_mode": "lithium"}})
    result = load_config(
        options=LoadOptions(
            user_config_file=user_file,
            project_config_file=project_file,
            cwd=tmp_path,
            skip_env=True,
        )
    )
    assert result.config.reader.cycle_mode == "lithium"
    assert result.provenance.get("reader.cycle_mode") == SourceLayer.PROJECT_FILE


def test_loader_env_overrides_file(tmp_path, monkeypatch):
    user_file = tmp_path / "cellpy.toml"
    write_toml(user_file, {"reader": {"cycle_mode": "cathode"}})
    monkeypatch.setenv("CELLPY_READER__CYCLE_MODE", "lithium")
    result = load_config(
        options=LoadOptions(
            user_config_file=user_file,
            cwd=tmp_path,
            env_file=tmp_path / "missing.env",
            skip_env=False,
        )
    )
    assert result.config.reader.cycle_mode == "lithium"
    assert result.provenance.get("reader.cycle_mode") == SourceLayer.ENV


def test_sources_reports_layers(tmp_path, monkeypatch):
    user_file = tmp_path / "cellpy.toml"
    write_toml(user_file, {"batch": {"backend": "bokeh"}})
    monkeypatch.setenv("CELLPY_READER__CYCLE_MODE", "cathode")
    set_load_options(
        LoadOptions(
            user_config_file=user_file,
            cwd=tmp_path,
            env_file=tmp_path / "x.env",
            skip_env=False,
        )
    )
    reload()
    provenance = sources()
    assert provenance.get("reader.cycle_mode") == SourceLayer.ENV.value
    assert provenance.get("batch.backend") == SourceLayer.USER_FILE.value
    assert provenance.get("paths.outdatadir") == SourceLayer.DEFAULT.value


@pytest.mark.essential
def test_secrets_read_legacy_env(monkeypatch):
    monkeypatch.setenv("CELLPY_PASSWORD", "secret-pass")
    monkeypatch.setenv("CELLPY_USER", "alice")
    result = load_config(options=LoadOptions(skip_files=True, skip_env=False))
    # password is a SecretStr as of #565 — the value only comes out on request
    assert result.config.secrets.get_password() == "secret-pass"
    assert "secret-pass" not in repr(result.config.secrets)
    assert result.config.secrets.user == "alice"


def test_toml_roundtrip_smoke(tmp_path):
    path = tmp_path / "cellpy.toml"
    write_toml(path, {"reader": {"cycle_mode": "cathode", "auto_dirs": False}})
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert data["reader"]["cycle_mode"] == "cathode"
    assert data["reader"]["auto_dirs"] is False


def test_yaml_to_toml_converter_minimal():
    yaml_text = """
Paths:
  outdatadir: /tmp/out
Reader:
  cycle_mode: cathode
CellInfo:
  comment: hello
Materials:
  default_material: graphite
"""
    data = convert_yaml_to_toml_dict(yaml_text)
    assert data["paths"]["outdatadir"] == "/tmp/out"
    assert data["reader"]["cycle_mode"] == "cathode"
    assert data["defaults"]["cell_info"]["comment"] == "hello"
    assert data["defaults"]["materials"]["default_material"] == "graphite"
