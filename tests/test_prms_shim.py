"""Tests for the deprecated prms shim and legacy YAML fallback (issue #453)."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from cellpy.config import LoadOptions, reset_session
from cellpy.config.loader import load_config
from cellpy.config.sources import SourceLayer
from cellpy import _deprecation
from cellpy.parameters import prms
from cellpy.parameters import prmreader
from tests.prms_support import write_minimal_prm_file


@pytest.fixture(autouse=True)
def _reset_config_session():
    reset_session()
    yield
    reset_session()


@pytest.mark.essential
def test_prms_shim_forwards_and_warns():
    _deprecation._WARNED_SITES.clear()
    prmreader.initialize()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        prms.Reader.cycle_mode = "cathode"
        assert prms.Reader.cycle_mode == "cathode"

    assert any("prms.Reader" in str(item.message) for item in caught)


@pytest.mark.essential
def test_legacy_yaml_fallback_loads(tmp_path):
    root = str(tmp_path).replace("\\", "/")
    yaml_content = f"""---
Paths:
  outdatadir: {root}/out
  rawdatadir: {root}/raw
  cellpydatadir: {root}/cellpy
  db_path: {root}/db
  filelogdir: {root}/logs
  examplesdir: {root}/examples
  notebookdir: {root}/notebooks
  templatedir: {root}/templates
  batchfiledir: {root}/batchfiles
  instrumentdir: {root}/instruments
  db_filename: cellpy_db.xlsx
  env_file: .env_cellpy
Reader:
  cycle_mode: cathode
...
"""
    legacy_file = tmp_path / ".cellpy_prms_testuser.conf"
    write_minimal_prm_file(legacy_file, yaml_content)

    result = load_config(
        options=LoadOptions(
            legacy_yaml_file=legacy_file,
            user_config_file=tmp_path / "missing.toml",
            cwd=tmp_path,
            skip_env=True,
        )
    )
    assert result.config.reader.cycle_mode == "cathode"
    assert result.provenance.get("reader.cycle_mode") == SourceLayer.USER_FILE
