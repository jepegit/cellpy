#!/usr/bin/env python
"""Regenerate committed golden fixtures under ``tests/data/goldens/``.

Golden files are regression oracles for cellpy 2 Stage 0 characterization work.
They must be updated only through this script — never edited by hand. See
``tests/README.md`` for the convention and ``tests/data/goldens/README.md`` for
the suite index.

Usage::

    uv run python dev/regenerate_goldens.py                  # all suites
    uv run python dev/regenerate_goldens.py pipeline_smoke   # one suite
    uv run python dev/regenerate_goldens.py --verify         # byte-identical check
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS_ROOT = REPO_ROOT / "tests" / "data" / "goldens"
RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"

if str(REPO_ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tests"))

from golden_support import sort_summary_columns  # noqa: E402
from loader_golden_support import LOADER_GOLDEN_SPECS, load_loader_snapshot  # noqa: E402

_SUITES: dict[str, Callable[[Path], None]] = {}

# Scalar oracle mirrored from tests/test_cell_readers.py (canonical Arbin .res).
PIPELINE_SMOKE_ORACLE = {
    "n_steps": 103,
    "n_cycles": 18,
    "cycle1_data_point": 1457,
}


def register_golden_suite(name: str):
    """Register a suite regen callable; ``name`` is the subdirectory under goldens/."""

    def decorator(fn: Callable[[Path], None]) -> Callable[[Path], None]:
        if name in _SUITES:
            raise ValueError(f"duplicate golden suite name: {name!r}")
        _SUITES[name] = fn
        return fn

    return decorator


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        tmp_path.write_bytes(data)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_parquet_frame(df, path: Path) -> None:
    """Write a DataFrame to parquet with stable column order and compression."""
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"expected pandas.DataFrame, got {type(df)!r}")
    ordered = df[sorted(df.columns)]
    tmp = path.with_suffix(path.suffix + ".tmp.parquet")
    ordered.to_parquet(tmp, index=False, engine="pyarrow", compression="snappy")
    _atomic_write_bytes(path, tmp.read_bytes())
    tmp.unlink(missing_ok=True)


def write_json_doc(data: dict[str, Any], path: Path) -> None:
    """Write JSON with sorted keys and a trailing newline."""
    payload = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _atomic_write_bytes(path, payload)


@register_golden_suite("pipeline_smoke")
def _regen_pipeline_smoke(out_dir: Path) -> None:
    """Canonical read → step table → summary on the Arbin .res golden file."""
    if not RES_FILE.is_file():
        raise FileNotFoundError(
            f"Missing source file {RES_FILE}. "
            "The pipeline_smoke suite needs testdata/data/20160805_test001_45_cc_01.res."
        )

    from cellpy import cellreader

    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()

    summary = sort_summary_columns(cell.data.summary.reset_index(drop=True))
    steps = cell.data.steps.reset_index(drop=True)
    metrics = {
        "cycle1_data_point": int(summary.loc[summary.index[0], "data_point"]),
        "n_cycles": int(len(summary)),
        "n_steps": int(len(steps)),
        "source": "testdata/data/20160805_test001_45_cc_01.res",
        "suite": "pipeline_smoke",
    }

    write_parquet_frame(summary, out_dir / "summary.parquet")
    write_json_doc(metrics, out_dir / "metrics.json")

    oracle_ok = (
        metrics["n_steps"] == PIPELINE_SMOKE_ORACLE["n_steps"]
        and metrics["n_cycles"] == PIPELINE_SMOKE_ORACLE["n_cycles"]
        and metrics["cycle1_data_point"] == PIPELINE_SMOKE_ORACLE["cycle1_data_point"]
    )
    print(
        f"[pipeline_smoke] wrote summary.parquet ({summary.shape[0]} rows) "
        f"and metrics.json (n_steps={metrics['n_steps']}, n_cycles={metrics['n_cycles']}, "
        f"cycle1_data_point={metrics['cycle1_data_point']})"
    )
    if not oracle_ok:
        print(
            "[pipeline_smoke] WARNING: metrics differ from the documented oracle "
            f"{PIPELINE_SMOKE_ORACLE!r}"
        )


def _register_loader_golden_suites() -> None:
    for spec in LOADER_GOLDEN_SPECS:

        def _make_regen(selected_spec=spec):
            @register_golden_suite(selected_spec.suite)
            def _regen_loader(out_dir: Path, _spec=selected_spec) -> None:
                if not _spec.source_path.is_file():
                    raise FileNotFoundError(
                        f"Missing source file {_spec.source_path} for suite {_spec.suite!r}."
                    )
                if (
                    _spec.instrument_file is not None
                    and not _spec.instrument_file_path.is_file()
                ):
                    raise FileNotFoundError(
                        f"Missing instrument file {_spec.instrument_file_path} "
                        f"for suite {_spec.suite!r}."
                    )
                raw, meta, metrics = load_loader_snapshot(_spec)
                write_parquet_frame(raw, out_dir / "raw.parquet")
                write_json_doc(meta["raw_units"], out_dir / "raw_units.json")
                write_json_doc(
                    {
                        "meta_common": meta["meta_common"],
                        "meta_test_dependent": meta["meta_test_dependent"],
                        "raw_limits": meta["raw_limits"],
                        **(
                            {"custom_info": meta["custom_info"]}
                            if "custom_info" in meta
                            else {}
                        ),
                    },
                    out_dir / "meta.json",
                )
                write_json_doc(metrics, out_dir / "metrics.json")
                print(
                    f"[{_spec.suite}] wrote raw.parquet ({metrics['n_rows']} rows, "
                    f"{metrics['n_columns']} cols), raw_units.json, meta.json, metrics.json"
                )

            return _regen_loader

        _make_regen()


_register_loader_golden_suites()


def _regenerate_suite(name: str, out_root: Path) -> None:
    if name not in _SUITES:
        known = ", ".join(sorted(_SUITES)) or "(none registered)"
        raise SystemExit(f"Unknown suite {name!r}. Registered: {known}")
    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    _SUITES[name](out_dir)


def _compare_dirs(left: Path, right: Path) -> list[str]:
    diffs: list[str] = []
    left_files = sorted(p.relative_to(left) for p in left.rglob("*") if p.is_file())
    right_files = sorted(p.relative_to(right) for p in right.rglob("*") if p.is_file())
    if left_files != right_files:
        diffs.append(f"file lists differ: {left_files!r} vs {right_files!r}")
        return diffs
    for rel in left_files:
        lpath, rpath = left / rel, right / rel
        if not filecmp.cmp(lpath, rpath, shallow=False):
            diffs.append(str(rel))
    return diffs


def _verify_suites(names: list[str]) -> None:
    for name in names:
        with (
            tempfile.TemporaryDirectory() as tmp_a,
            tempfile.TemporaryDirectory() as tmp_b,
        ):
            root_a = Path(tmp_a)
            root_b = Path(tmp_b)
            _regenerate_suite(name, root_a)
            _regenerate_suite(name, root_b)
            diffs = _compare_dirs(root_a / name, root_b / name)
            if diffs:
                raise SystemExit(
                    f"--verify failed for suite {name!r}: non-deterministic outputs: {diffs}"
                )
            print(f"[verify] {name}: byte-identical across two runs")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "suites",
        nargs="*",
        help="Suite names to regenerate (default: all registered suites)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Regenerate each suite twice to a temp dir and assert byte-identical output",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=GOLDENS_ROOT,
        help=f"Root directory for golden suites (default: {GOLDENS_ROOT})",
    )
    args = parser.parse_args(argv)

    names = args.suites or sorted(_SUITES)
    if not names:
        raise SystemExit("No golden suites registered.")

    if args.verify:
        _verify_suites(names)
        return

    for name in names:
        _regenerate_suite(name, args.output_root)
    print(f"Done. Goldens under {args.output_root}")


if __name__ == "__main__":
    main()
