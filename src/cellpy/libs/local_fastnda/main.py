"""Main module for reading Neware NDA and NDAX files."""

import logging
from pathlib import Path
from typing import Literal, cast

import polars as pl

from cellpy.libs.local_fastnda.dicts import DTYPE_MAP, STEP_TYPE_MAP
from cellpy.libs.local_fastnda.formats import to_bdf
from cellpy.libs.local_fastnda.nda import read_nda, read_nda_metadata
from cellpy.libs.local_fastnda.ndax import read_ndax, read_ndax_metadata
from cellpy.libs.local_fastnda.utils import _generate_cycle_number

logger = logging.getLogger(__name__)


def read(
    file: str | Path,
    cycle_mode: Literal["chg", "dchg", "auto", "raw"] = "chg",
    columns: Literal["default", "bdf"] = "default",
    *,
    raw_categories: bool = False,
) -> pl.DataFrame:
    """Read Neware nda or ndax binary file into polars DataFrame.

    Args:
        file: Path of .nda or .ndax file to read
        cycle_mode: Selects how the cycle is incremented.
            'chg': (Default) Cycle incremented by a charge step following a discharge.
            'dchg': Cycle incremented by a discharge step following a charge.
            'auto': Identifies the first non-rest state as the incremental state.
            'raw': Leaves cycles as it is found in the Neware file.
        columns: Selects how to format the output columns
            'default': fastnda columns, e.g. 'voltage_V', 'current_mA'
            'bdf': battery-data-format columns, e.g. 'voltage_volt', 'current_ampere'
        raw_categories: Return `step_type` column as integer codes.

    Returns:
        DataFrame containing all records in the file

    """
    # Read file and generate DataFrame
    file = Path(file)
    if file.suffix == ".nda":
        df = read_nda(file)
    elif file.suffix == ".ndax":
        df = read_ndax(file)
    else:
        msg = "File type not supported!"
        raise ValueError(msg)

    # Generate cycle number if requested or missing
    if "cycle_count" not in df.columns and cycle_mode == "raw":
        logger.warning("Raw cycle column missing for this file type, using 'auto'.")
        cycle_mode = "auto"
    if cycle_mode in {"chg", "dchg", "auto"}:
        cycle_mode = cast("Literal['chg', 'dchg', 'auto']", cycle_mode)
        df = _generate_cycle_number(df, cycle_mode)

    if "total_time_s" not in df.columns:
        max_df = (
            df.group_by("step_count")
            .agg(pl.col("step_time_s").max().alias("max_step_time_s"))
            .sort("step_count")
            .with_columns(pl.col("max_step_time_s").shift(1).fill_null(0).cum_sum())
        )
        df = df.join(max_df, on="step_count", how="left").with_columns(
            (pl.col("step_time_s") + pl.col("max_step_time_s")).alias("total_time_s")
        )

    # Round time to us, step_type -> categories, merge charge/discharge capacity/energy
    cols = [
        pl.col("step_time_s").round(6),
        pl.col("total_time_s").round(6),
        pl.col("unix_time_s").round(6),
    ]
    if not raw_categories:
        cols += [
            pl.col("step_type").replace_strict(STEP_TYPE_MAP, default=None, return_dtype=pl.Categorical),
        ]
    if "capacity_mAh" not in df.columns:
        cols += [
            (pl.col("charge_capacity_mAh") - pl.col("discharge_capacity_mAh")).alias("capacity_mAh"),
            (pl.col("charge_energy_mWh") - pl.col("discharge_energy_mWh")).alias("energy_mWh"),
        ]
    df = df.with_columns(cols)

    # Ensure columns have correct data types
    dtype_map = dict(DTYPE_MAP)
    if raw_categories:
        dtype_map["step_type"] = pl.UInt8
    df = df.with_columns([pl.col(name).cast(dtype_map[name]) for name in df.columns if name in dtype_map])

    # Reorder columns
    non_aux_columns = [name for name in DTYPE_MAP if name in df.columns]
    aux_columns = [name for name in df.columns if name.startswith("aux")]
    df = df.select(non_aux_columns + aux_columns)

    if columns == "bdf":
        return to_bdf(df)
    return df


def read_metadata(file: str | Path) -> dict[str, str | float]:
    """Read metadata from a Neware .nda or .ndax file.

    Args:
        file: Path of .nda or .ndax file

    Returns:
        Dictionary containing metadata

    """
    file = Path(file)
    if file.suffix == ".nda":
        return read_nda_metadata(file)
    if file.suffix == ".ndax":
        return read_ndax_metadata(file)
    msg = "File type not supported!"
    raise ValueError(msg)
