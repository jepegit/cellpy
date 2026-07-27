"""Tests for the removed prms shim (E5, #717) and legacy YAML fallback (#453)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cellpy.config import LoadOptions, reset_session
from cellpy.config.loader import load_config
from cellpy.config.sources import SourceLayer
from cellpy.parameters import prms
from cellpy.parameters import prmreader
from tests.prms_support import write_minimal_prm_file


@pytest.fixture(autouse=True)
def _reset_config_session():
    reset_session()
    yield
    reset_session()


@pytest.mark.essential
@pytest.mark.parametrize(
    "section", ["Paths", "Reader", "Db", "Batch", "Instruments", "Materials"]
)
def test_prms_section_shim_removed(section):
    """The ``prms.<Section>`` global-mutation shim was removed in 2.1 (E5, #717);
    use ``cellpy.config`` (e.g. ``config.reader.cycle_mode = ...``) instead."""
    with pytest.raises(AttributeError):
        getattr(prms, section)


@pytest.mark.essential
def test_config_is_the_replacement():
    """``cellpy.config`` is the sanctioned way to read/mutate settings."""
    from cellpy import config

    prmreader.initialize()
    config.reader.cycle_mode = "cathode"
    assert config.reader.cycle_mode == "cathode"


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


@pytest.mark.essential
def test_import_cellpy_no_file_io():
    """``import cellpy`` must not read config files (issue #453 acceptance)."""

    import subprocess
    import sys

    script = """
import builtins
from pathlib import Path

reads = []
_real_open = builtins.open

def _track_open(path, *args, **kwargs):
    reads.append(str(path))
    return _real_open(path, *args, **kwargs)

builtins.open = _track_open
_real_read_text = Path.read_text

def _track_read_text(self, *args, **kwargs):
    reads.append(str(self))
    return _real_read_text(self, *args, **kwargs)

Path.read_text = _track_read_text

import cellpy  # noqa: F401

config_reads = [
    p
    for p in reads
    if ".cellpy_prms" in p or p.endswith("cellpy.toml") or p.endswith(".env_cellpy")
]
assert not config_reads, config_reads
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
