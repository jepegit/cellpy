"""2.0 file-format compatibility matrix (issue #573 / release plan §1).

One essential suite covering every promised cell: read v8/v9, write v9/v8,
reject v<8 by default (naming convert on 1.x), convert escape, and v8→v9
value parity. Deeper characterization stays in ``test_cellpy_file_*.py``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from cellpy import cellreader
from cellpy.exceptions import WrongFileVersion
from cellpy.readers.cellpy_file import CELLPY_FILE_VERSION, v9 as cellpy_file_v9
from tests.cellpy_file_support import (
    assert_data_frames_equal,
    load_cellpy_file,
    snapshot_cell_state,
)

HDF5_DIR = Path(__file__).resolve().parents[1] / "testdata" / "hdf5"
V8_WITH_FIDS = HDF5_DIR / "20160805_test001_45_cc_v8_with_fids.h5"
V5 = HDF5_DIR / "20160805_test001_45_cc_v5.h5"
V7 = HDF5_DIR / "20160805_test001_45_cc_v7.h5"

_FREEZE_MESSAGE = r"Use cellpy 1\.x `cellpy convert`"


def _require(path: Path) -> Path:
    if not path.is_file():
        pytest.skip(f"missing fixture: {path}")
    return path


@pytest.mark.essential
def test_matrix_read_v8():
    cell = load_cellpy_file(_require(V8_WITH_FIDS))
    assert len(cell.data.raw) > 0
    assert len(cell.data.steps) > 0
    assert len(cell.data.summary) > 0
    assert cell.data.meta_common.cellpy_file_version == 8


@pytest.mark.essential
def test_matrix_write_v9_default_and_read(tmp_path):
    original = load_cellpy_file(_require(V8_WITH_FIDS))
    outfile = tmp_path / "out.cellpy"
    original.save(outfile)

    assert cellpy_file_v9.is_zip_cellpy(outfile)
    reloaded = load_cellpy_file(outfile)
    assert reloaded.data.meta_common.cellpy_file_version == CELLPY_FILE_VERSION
    assert len(reloaded.data.raw) > 0


@pytest.mark.essential
def test_matrix_write_v8_via_h5_suffix(tmp_path):
    cell = load_cellpy_file(_require(V8_WITH_FIDS))
    outfile = tmp_path / "legacy.h5"
    cell.save(outfile)

    assert not cellpy_file_v9.is_zip_cellpy(outfile)
    with pd.HDFStore(outfile) as store:
        assert "/CellpyData/raw" in store.keys()
    reloaded = load_cellpy_file(outfile)
    assert reloaded.data.meta_common.cellpy_file_version == 8


@pytest.mark.essential
def test_matrix_write_v8_via_format_kwarg(tmp_path):
    cell = load_cellpy_file(_require(V8_WITH_FIDS))
    outfile = tmp_path / "explicit.cellpy"
    cell.save(outfile, cellpy_file_format="v8")

    assert not cellpy_file_v9.is_zip_cellpy(outfile)
    reloaded = load_cellpy_file(outfile)
    assert reloaded.data.meta_common.cellpy_file_version == 8


@pytest.mark.essential
@pytest.mark.parametrize(
    "legacy, version",
    [(V5, 5), (V7, 7)],
)
def test_matrix_read_pre_v8_raises_naming_convert(legacy, version):
    path = _require(legacy)
    cell = cellreader.CellpyCell()
    with pytest.raises(WrongFileVersion, match=_FREEZE_MESSAGE) as exc_info:
        cell.load(path)
    assert f"v{version}" in str(exc_info.value)


@pytest.mark.essential
def test_matrix_read_pre_v8_accept_old_escape():
    cell = load_cellpy_file(_require(V5), accept_old=True)
    assert cell.data.meta_common.cellpy_file_version == 5
    assert len(cell.data.raw) > 0


@pytest.mark.essential
@pytest.mark.parametrize("target", ["v9", "v8"])
def test_matrix_convert_rewrites_pre_v8(tmp_path, target):
    from cellpy import cli_api

    source = _require(V5)
    work = tmp_path / source.name
    shutil.copy(source, work)

    written = cli_api.convert(work, to=target)
    assert written.is_file()
    reloaded = cellreader.CellpyCell().load(written)
    assert len(reloaded.get_cycle_numbers()) > 0
    assert len(reloaded.data.raw) > 0
    if target == "v9":
        assert cellpy_file_v9.is_zip_cellpy(written)
        assert reloaded.data.meta_common.cellpy_file_version == CELLPY_FILE_VERSION
    else:
        assert written.suffix == ".h5"
        assert reloaded.data.meta_common.cellpy_file_version == 8


@pytest.mark.essential
def test_matrix_v8_to_v9_value_parity(tmp_path):
    original = load_cellpy_file(_require(V8_WITH_FIDS))
    expected = snapshot_cell_state(original)

    outfile = tmp_path / "parity.cellpy"
    original.save(outfile)
    reloaded = load_cellpy_file(outfile)

    assert_data_frames_equal(reloaded.data.raw, expected["raw"])
    assert_data_frames_equal(reloaded.data.steps, expected["steps"])
    assert_data_frames_equal(reloaded.data.summary, expected["summary"])
