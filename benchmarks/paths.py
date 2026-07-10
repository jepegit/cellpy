"""Shared paths for the cellpy performance benchmark suite."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_ROOT = Path(__file__).resolve().parent
BASELINES_DIR = BENCHMARKS_ROOT / "baselines"
COMMITTED_BASELINE = BASELINES_DIR / "v1x_ubuntu_py313.json"

RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"
V8_FILE = REPO_ROOT / "testdata" / "hdf5" / "20160805_test001_45_cc_v8.h5"

BATCH_CELL_COUNT = 20
