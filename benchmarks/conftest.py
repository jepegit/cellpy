"""Pytest configuration for the cellpy performance benchmark suite."""

from __future__ import annotations

import platform
import shutil
import sys

import pytest

from benchmarks.paths import COMMITTED_BASELINE, REPO_ROOT, RES_FILE, V8_FILE

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

pytestmark = pytest.mark.benchmark


def _machine_subdir() -> str:
    return f"{platform.system()}-CPython-{platform.python_version()}-{platform.architecture()[0]}"


def pytest_configure(config: pytest.Config) -> None:
    """Seed pytest-benchmark storage from the committed baseline when comparing."""
    if not config.getoption("benchmark_compare", default=None):
        return
    if not COMMITTED_BASELINE.is_file():
        return

    dest_dir = REPO_ROOT / ".benchmarks" / _machine_subdir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(COMMITTED_BASELINE, dest_dir / "0001_v1x.json")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if RES_FILE.is_file() and V8_FILE.is_file():
        return
    skip = pytest.mark.skip(
        reason=f"missing golden fixtures: res={RES_FILE.is_file()}, v8={V8_FILE.is_file()}"
    )
    for item in items:
        item.add_marker(skip)


def peak_rss_kib() -> int | None:
    """Peak RSS in KiB on Linux; ``None`` elsewhere."""
    if sys.platform != "linux":
        return None
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


@pytest.fixture(scope="module")
def pipeline_cell():
    """CellpyCell with step table and summary built from the canonical Arbin ``.res``."""
    from cellpy.readers import cellreader

    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()
    return cell


@pytest.fixture(scope="module")
def batch_twenty_cells():
    """Batch with 20 cells loaded from the same v8 oracle (unique virtual file names)."""
    import cellpy
    from cellpy import log, prms
    from cellpy.utils.batch import Batch
    from tests import fdv

    log.setup_logging(testing=True)
    prms.Paths.rawdatadir = fdv.raw_data_dir
    prms.Paths.cellpydatadir = fdv.cellpy_data_dir
    prms.Paths.db_path = fdv.db_dir
    prms.Paths.db_filename = fdv.db_file_name
    prms.Paths.outdatadir = fdv.output_dir
    prms.Batch.auto_use_file_list = False

    cells = []
    for i in range(20):
        cell = cellpy.get(str(V8_FILE), testing=True)
        cell.cell_name = f"bench_cell_{i}"
        cell.cellpy_file_name = f"bench_cell_{i}_{V8_FILE.name}"
        cells.append(cell)

    batch = Batch(
        mode="new",
        cells=cells,
        db_reader="off",
        export_raw=False,
        export_cycles=False,
        export_ica=False,
    )
    return batch
