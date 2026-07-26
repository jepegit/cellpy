"""Pure output writers (batch v3, #701).

Each writer takes a frame and an explicit path and writes it -- nothing more.
Exporting never creates directory trees implicitly (that is
``layout.ensure_dirs``); the parent directory must already exist.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


def write_csv(frame: pl.DataFrame, path: Path | str) -> Path:
    """Write ``frame`` to a CSV file at ``path``."""
    path = Path(path)
    frame.write_csv(path)
    return path


def write_parquet(frame: pl.DataFrame, path: Path | str) -> Path:
    """Write ``frame`` to a Parquet file at ``path``."""
    path = Path(path)
    frame.write_parquet(path)
    return path


def write_excel(frame: pl.DataFrame, path: Path | str) -> Path:
    """Write ``frame`` to an ``.xlsx`` file at ``path`` (via openpyxl)."""
    path = Path(path)
    frame.to_pandas().to_excel(path, index=False, engine="openpyxl")
    return path
