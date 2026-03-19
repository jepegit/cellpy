"""Module to read Neware NDAX files."""

import logging
import re
import zipfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import polars as pl
import xmltodict
from defusedxml import ElementTree

from cellpy.libs.local_fastnda.dicts import (
    AUX_CHL_MAP,
    MULTIPLIER_MAP,
)
from cellpy.libs.local_fastnda.utils import _count_changes

try:
    import zlib

    from isal import isal_zlib

    zlib.decompress = isal_zlib.decompress
    zlib.decompressobj = isal_zlib.decompressobj
    ISAL_AVAILABLE = True
except ImportError:
    ISAL_AVAILABLE = False

logger = logging.getLogger(__name__)


def read_ndax(file: str | Path) -> pl.DataFrame:
    """Read data from a Neware .ndax zipped file.

    Args:
        file: Path to .ndax file to read

    Returns:
        DataFrame containing all records in the file

    """
    logger.debug("RUNNING LOCAL FASTNDA NDAX")
    with zipfile.ZipFile(str(file)) as zf:
        # Get auxiliary channel files and info
        aux_ch_dict = _find_auxiliary_channels(zf)

        # Extract and parse all of the .ndc files into dataframes in parallel
        files_to_read = ["data.ndc", "data_runInfo.ndc", "data_step.ndc", *aux_ch_dict.keys()]
        dfs = {}
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(_extract_and_bytes_to_df, zf, fname): fname for fname in files_to_read}
            for future in as_completed(futures):
                fname, df = future.result()
                if df is not None:
                    dfs[fname] = df

    # Main data (voltage, current) is always called data.ndc
    df = dfs["data.ndc"]

    # 'runInfo' contains times, capacities, energies, and needs to be forward-filled/interpolated
    if "data_runInfo.ndc" in dfs:
        df = df.join(dfs["data_runInfo.ndc"], how="left", on="index")
        df = _data_interpolation(df)

        # 'step' contains cycle count, step index, step_type for each step
        if "data_step.ndc" in dfs:
            df = df.join(dfs["data_step.ndc"], how="left", on="step_count")

    # Merge the aux data if it exists
    logger.debug(f"Merging aux data: {aux_ch_dict.keys()}")
    for i, (f, aux_dict) in enumerate(aux_ch_dict.items()):
        logger.debug(f"Processing aux file: {f}")
        logger.debug(f"Aux dict: {aux_dict}")
        aux_df = dfs.get(f)
        if aux_df is not None:
            # Get aux ID, use -i if not present to avoid conflicts
            aux_id = aux_dict.get("AuxID", -i)
            logger.debug(f"Aux ID not found: {aux_id}")

            # If ? column exists, rename name by ChlType (T, t, H)
            if "?" in aux_df.columns and aux_dict.get("ChlType") in AUX_CHL_MAP:
                col = AUX_CHL_MAP[aux_dict["ChlType"]]
                aux_df = aux_df.rename({"?": f"aux{aux_id}_{col}"})
            else:  # Otherwise just append aux ID to column names
                aux_df = aux_df.rename({col: f"aux{aux_id}_{col}" for col in aux_df.columns if col not in ["index"]})
            df = df.join(aux_df, how="left", on="index")

    return df


def read_ndax_metadata(file: str | Path) -> dict[str, str | float]:
    """Read metadata from VersionInfo.xml and Step.xml in a Neware .ndax file."""
    metadata = {}
    with zipfile.ZipFile(str(file)) as zf:
        xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
        for xml_file in xml_files:
            name = xml_file.split("/")[-1].split(".")[0]
            xml_tree = ElementTree.fromstring(zf.read(xml_file).decode(errors="ignore")).find("config")
            metadata[name] = xmltodict.parse(ElementTree.tostring(xml_tree).decode(), attr_prefix="")["config"]
    return metadata


def _find_auxiliary_channels(zf: zipfile.ZipFile) -> dict[str, dict]:
    """Find all auxiliary channel files.

    Args:
        zf: open zipfile (ndax)

    Returns:
        dict: keys = filenames, values = dict of attributes of aux channel

    """
    # Auxiliary files files need to be matched to entries in TestInfo.xml
    # Sort by the numbers in the filename, assume same order in TestInfo.xml
    aux_data = []
    for f in zf.namelist():
        m = re.search(r"data_AUX_(\d+)_(\d+)_(\d+)\.ndc", f)
        if m:
            aux_data.append((f, list(map(int, m.groups()))))
        else:
            m = re.search(r".*_(\d+)\.ndc", f)
            if m:
                aux_data.append((f, [int(m.group(1)), 0, 0]))

    # Sort by the three integers
    aux_data.sort(key=lambda x: x[1])
    aux_filenames = [f for f, _ in aux_data]

    # Find all auxiliary channel dicts in TestInfo.xml
    aux_dicts: list[dict] = []
    if aux_filenames:
        try:
            step = zf.read("TestInfo.xml").decode("gb2312")
            test_info = ElementTree.fromstring(step).find("config/TestInfo")
            if test_info is not None:
                aux_dicts.extend(
                    {k: int(v) if v.isdigit() else v for k, v in child.attrib.items()}
                    for child in test_info
                    if "aux" in child.tag.lower()
                )
        except Exception:
            logger.exception("Aux files found, but could not read TestInfo.xml!")

    # ASSUME channel files are in the same order as TestInfo.xml, map filenames to dicts
    if len(aux_dicts) == len(aux_filenames):
        return dict(zip(aux_filenames, aux_dicts, strict=True))
    logger.critical("Found a different number of aux channels in files and TestInfo.xml!")
    return {}


def _extract_and_bytes_to_df(zf: zipfile.ZipFile, filename: str) -> tuple[str, pl.DataFrame | None]:
    """Extract .ndc from a zipfile and reads it into a DataFrame."""
    if filename in zf.namelist():
        buf = zf.read(filename)
        return filename, _read_ndc(buf)
    return filename, None


def _data_interpolation(df: pl.DataFrame) -> pl.DataFrame:
    """Forward fill and interpolate missing data in the DataFrame."""
    # Get time by forward filling differences
    df = (
        df.with_columns(
            [
                pl.col("step_time_s").is_null().alias("nan_mask"),
                pl.col("step_time_s").is_not_null().cum_sum().shift(1).fill_null(0).alias("group_idx"),
                pl.col(
                    "dt",
                    "step_count",
                    "step_time_s",
                    "unix_time_s",
                    "charge_capacity_mAh",
                    "discharge_capacity_mAh",
                    "charge_energy_mWh",
                    "discharge_energy_mWh",
                ).fill_null(strategy="forward"),
            ]
        )
        .with_columns(
            [
                (pl.col("dt").cum_sum().over("group_idx") * (pl.col("nan_mask"))).alias("cdt"),
                ((pl.col("dt") * pl.col("current_mA") / 3600).cum_sum().over("group_idx") * pl.col("nan_mask")).alias(
                    "inc_capacity"
                ),
                (
                    (pl.col("dt") * pl.col("voltage_V") * pl.col("current_mA") / 3600).cum_sum().over("group_idx")
                    * pl.col("nan_mask")
                ).alias("inc_energy"),
            ]
        )
        .with_columns(
            [
                (pl.col("step_time_s") + pl.col("cdt")).alias("step_time_s"),
                (pl.col("unix_time_s") + pl.col("cdt")).alias("unix_time_s"),
                (pl.col("charge_capacity_mAh").abs() + pl.col("inc_capacity").clip(lower_bound=0)).alias(
                    "charge_capacity_mAh"
                ),
                (pl.col("discharge_capacity_mAh").abs() - pl.col("inc_capacity").clip(upper_bound=0)).alias(
                    "discharge_capacity_mAh"
                ),
                (pl.col("charge_energy_mWh").abs() + pl.col("inc_energy").clip(lower_bound=0)).alias(
                    "charge_energy_mWh"
                ),
                (pl.col("discharge_energy_mWh").abs() - pl.col("inc_energy").clip(upper_bound=0)).alias(
                    "discharge_energy_mWh"
                ),
            ]
        )
        .drop(["nan_mask", "group_idx", "cdt", "inc_capacity", "inc_energy", "dt"])
    )

    # Sanity checks
    if (df["unix_time_s"].diff() < 0).any():
        logger.warning(
            "IMPORTANT: This ndax has negative jumps in the 'unix_time_s' column! "
            "Use the 'total_time_s' column for analysis.",
        )

    return df


def _read_ndc(buf: bytes) -> pl.DataFrame:
    """Read electrochemical data from a Neware ndc binary file.

    Args:
        buf: Bytes object for the .ndc file to read
    Returns:
        DataFrame containing all records in the file

    """
    # Get ndc file version and filetype
    ndc_filetype = int(buf[0])
    ndc_version = int(buf[2])
    reader = NDC_READERS.get((ndc_version, ndc_filetype))
    if reader is None:
        msg = f"ndc version {ndc_version} filetype {ndc_filetype} is not yet supported!"
        raise NotImplementedError(msg) from None
    logger.debug("Reading ndc version %d filetype %d", ndc_version, ndc_filetype)
    return reader(buf)


def _read_ndc_2_filetype_1(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("_pad1", "V8"),
            ("index", "<u4"),
            ("cycle_count", "<u4"),
            ("step_index", "<u1"),
            ("step_type", "<u1"),
            ("_pad2", "V5"),
            ("step_time_s", "<u8"),
            ("voltage_V", "<i4"),
            ("current_mA", "<i4"),
            ("_pad3", "V4"),
            ("charge_capacity_mAh", "<i8"),
            ("discharge_capacity_mAh", "<i8"),
            ("charge_energy_mWh", "<i8"),
            ("discharge_energy_mWh", "<i8"),
            ("Y", "<u2"),
            ("M", "<u1"),
            ("D", "<u1"),
            ("h", "<u1"),
            ("m", "<u1"),
            ("s", "<u1"),
            ("range", "<i4"),
            ("_pad4", "V8"),
        ]
    )
    return (
        _bytes_to_df(buf, dtype, data_start_ind=5, record_size=512, use_bitmask=False)
        .with_columns(
            [
                pl.col("cycle_count") + 1,
                pl.col("step_time_s").cast(pl.Float64) * 1e-3,
                pl.col("voltage_V").cast(pl.Float32) * 1e-4,
                pl.col("range").replace_strict(MULTIPLIER_MAP, return_dtype=pl.Float64).alias("multiplier"),
                pl.datetime(pl.col("Y"), pl.col("M"), pl.col("D"), pl.col("h"), pl.col("m"), pl.col("s")).alias(
                    "timestamp"
                ),
                _count_changes(pl.col("step_index")).alias("step_count"),
            ]
        )
        .with_columns(
            [
                pl.col("current_mA") * pl.col("multiplier"),
                (
                    pl.col(
                        ["charge_capacity_mAh", "discharge_capacity_mAh", "charge_energy_mWh", "discharge_energy_mWh"],
                    )
                    * pl.col("multiplier")
                    / 3600
                ).cast(pl.Float32),
                (pl.col("timestamp").cast(pl.Float64) / 1e6).alias("unix_time_s"),
            ]
        )
        .drop(["Y", "M", "D", "h", "m", "s"])
    )


def _read_ndc_2_filetype_5(buf: bytes) -> pl.DataFrame:
    # This dtype is missing humudity % column - does not exist in current test data
    dtype = np.dtype(
        [
            ("_pad2", "V8"),
            ("index", "<u4"),
            ("_pad3", "V19"),
            ("voltage_V", "<i4"),
            ("_pad4", "V6"),
            ("temperature_degC", "<i2"),
            ("temperature_setpoint_degC", "<i2"),
            ("_pad5", "V49"),
        ]
    )
    df = _bytes_to_df(buf, dtype, data_start_ind=5, record_size=512, use_bitmask=False).with_columns(
        pl.col("voltage_V").cast(pl.Float32) / 10000,
        pl.col("temperature_degC").cast(pl.Float32) * 0.1,
        pl.col("temperature_setpoint_degC").cast(pl.Float32) * 0.1,
    )
    # Drop empty columns
    cols_to_drop = [
        col
        for col in ["voltage_V", "temperature_degC", "temperature_setpoint_degC"]
        if df.filter(pl.col(col) != 0).is_empty()
    ]
    return df.select(pl.exclude(cols_to_drop))


def _read_ndc_5_filetype_1(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("_pad1", "V1"),
            ("index", "<u4"),
            ("cycle_count", "<u4"),
            ("step_index", "<u1"),
            ("step_type", "<u1"),
            ("_pad2", "V5"),
            ("step_time_s", "<u8"),
            ("voltage_V", "<i4"),
            ("current_mA", "<i4"),
            ("_pad3", "V4"),
            ("charge_capacity_mAh", "<i8"),
            ("discharge_capacity_mAh", "<i8"),
            ("charge_energy_mWh", "<i8"),
            ("discharge_energy_mWh", "<i8"),
            ("Y", "<u2"),
            ("M", "<u1"),
            ("D", "<u1"),
            ("h", "<u1"),
            ("m", "<u1"),
            ("s", "<u1"),
            ("range", "<i4"),
            ("_pad4", "V8"),
        ]
    )
    return (
        _bytes_to_df(buf, dtype)
        .with_columns(
            [
                pl.col("cycle_count") + 1,
                pl.col("step_time_s").cast(pl.Float64) * 1e-3,
                pl.col("voltage_V").cast(pl.Float32) * 1e-4,
                pl.col("range").replace_strict(MULTIPLIER_MAP, return_dtype=pl.Float64).alias("multiplier"),
                pl.datetime(pl.col("Y"), pl.col("M"), pl.col("D"), pl.col("h"), pl.col("m"), pl.col("s")).alias(
                    "timestamp"
                ),
                _count_changes(pl.col("step_index")).alias("step_count"),
            ]
        )
        .with_columns(
            [
                pl.col("current_mA") * pl.col("multiplier"),
                (
                    pl.col(
                        ["charge_capacity_mAh", "discharge_capacity_mAh", "charge_energy_mWh", "discharge_energy_mWh"],
                    )
                    * pl.col("multiplier")
                    / 3600
                ).cast(pl.Float32),
                (pl.col("timestamp").cast(pl.Float64) / 1e6).alias("unix_time_s"),
            ]
        )
        .drop(["Y", "M", "D", "h", "m", "s"])
    )


def _read_ndc_5_filetype_5(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("_pad2", "V1"),
            ("index", "<u4"),
            ("_pad3", "V19"),
            ("voltage_V", "<i4"),
            ("_pad4", "V6"),
            ("temperature_degC", "<i2"),
            ("temperature_setpoint_degC", "<i2"),
            ("_pad5", "V49"),
        ]
    )
    df = _bytes_to_df(buf, dtype).with_columns(
        pl.col("voltage_V").cast(pl.Float32) * 1e-4,
        pl.col("temperature_degC").cast(pl.Float32) * 0.1,
        pl.col("temperature_setpoint_degC").cast(pl.Float32) * 0.1,
    )
    # Drop empty columns
    cols_to_drop = [
        col
        for col in ["voltage_V", "temperature_degC", "temperature_setpoint_degC"]
        if df.filter(pl.col(col) != 0).is_empty()
    ]
    return df.select(pl.exclude(cols_to_drop))


def _read_ndc_11_filetype_1(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("voltage_V", "<f4"),
            ("current_mA", "<f4"),
        ]
    )
    return _bytes_to_df(buf, dtype, add_index=True).with_columns(
        [
            pl.col("voltage_V") * 1e-4,  # 0.1mV -> V
        ]
    )


def _read_ndc_11_filetype_5(buf: bytes) -> pl.DataFrame:
    header = 4096
    identifier = buf[header + 132 : header + 133]
    if identifier == b"\x65":
        dtype = np.dtype(
            [
                ("_mask", "<i1"),
                ("voltage_V", "<f4"),
                ("temperature_degC", "<i2"),
            ]
        )
        df = _bytes_to_df(buf, dtype).with_columns(
            [
                pl.col("voltage_V") * 1e-4,  # 0.1 mV -> V
                pl.col("temperature_degC").cast(pl.Float32) * 0.1,  # 0.1'C -> 'C
                pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("index"),
            ]
        )
        # Drop empty columns
        cols_to_drop = [col for col in ["voltage_V", "temperature_degC"] if df.filter(pl.col(col) != 0).is_empty()]
        return df.select(pl.exclude(cols_to_drop))

    if identifier == b"\x74":
        dtype = np.dtype(
            [
                ("_pad1", "V1"),
                ("index", "<u4"),
                ("Aux", "<i1"),
                ("_pad2", "V29"),
                ("temperature_degC", "<i2"),
                ("_pad3", "V51"),
            ]
        )
        return (
            _bytes_to_df(buf, dtype)
            .with_columns(
                [
                    pl.col("temperature_degC").cast(pl.Float32) * 0.1,  # 0.1'C -> 'C
                ]
            )
            .drop("Aux")
        )  # Aux channel inferred from TestInfo.xml

    msg = "Unknown file structure for ndc version 11 filetype 5."
    raise NotImplementedError(msg)


def _read_ndc_11_filetype_7(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("cycle_count", "<u4"),
            ("step_index", "<u4"),
            ("_pad1", "V16"),
            ("step_type", "<u1"),
            ("_pad2", "V12"),
        ]
    )
    return _bytes_to_df(buf, dtype).with_columns(
        [
            pl.col("cycle_count") + 1,
            pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("step_count"),
        ]
    )


def _read_ndc_11_filetype_18(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("step_time_s", "<u4"),
            ("_pad1", "V1"),
            ("charge_capacity_mAh", "<f4"),
            ("discharge_capacity_mAh", "<f4"),
            ("charge_energy_mWh", "<f4"),
            ("discharge_energy_mWh", "<f4"),
            ("_pad2", "V8"),
            ("dt", "<i4"),
            ("unix_time_s", "<u4"),
            ("step_count", "<u4"),
            ("index", "<u4"),
            ("uts_ms", "<u2"),
        ]
    )
    return (
        _bytes_to_df(buf, dtype)
        .with_columns(
            [
                pl.col("step_time_s", "dt").cast(pl.Float64) / 1000,  # ms -> s
                pl.col("charge_capacity_mAh", "discharge_capacity_mAh", "charge_energy_mWh", "discharge_energy_mWh")
                / 3600,  # mAs|mWs -> mAh|mWh
                (pl.col("unix_time_s") + pl.col("uts_ms") / 1000).alias("unix_time_s"),
                _count_changes(pl.col("step_count")).alias("step_count"),
            ]
        )
        .drop("uts_ms")
        .unique(subset="index", keep="first")
    )


def _read_ndc_14_filetype_1(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("voltage_V", "<f4"),
            ("current_mA", "<f4"),
        ]
    )
    return _bytes_to_df(buf, dtype, add_index=True).with_columns(
        [
            pl.col("current_mA") * 1000,
        ]
    )


def _read_ndc_14_filetype_5(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("?", "<f4"),  # Column name is assigned later from TestInfo.xml
        ]
    )
    return _bytes_to_df(buf, dtype, add_index=True).with_columns(
        [
            pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("index"),
        ]
    )


def _read_ndc_14_filetype_7(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("cycle_count", "<u4"),
            ("step_index", "<u4"),
            ("_pad1", "V16"),
            ("step_type", "<u1"),
            ("_pad2", "V12"),
        ]
    )
    return _bytes_to_df(buf, dtype).with_columns(
        [
            pl.col("cycle_count") + 1,
            pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("step_count"),
        ]
    )


def _read_ndc_14_filetype_18(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("step_time_s", "<u4"),
            ("_pad1", "V1"),
            ("charge_capacity_mAh", "<f4"),
            ("discharge_capacity_mAh", "<f4"),
            ("charge_energy_mWh", "<f4"),
            ("discharge_energy_mWh", "<f4"),
            ("_pad2", "V8"),
            ("dt", "<i4"),
            ("unix_time_s", "<u4"),
            ("step_count", "<u4"),
            ("index", "<u4"),
            ("uts_ms", "<i2"),
            ("_pad3", "V8"),
        ]
    )
    return (
        _bytes_to_df(buf, dtype)
        .with_columns(
            [
                pl.col("step_time_s", "dt").cast(pl.Float64) / 1000,  # ms -> s
                pl.col("charge_capacity_mAh", "discharge_capacity_mAh", "charge_energy_mWh", "discharge_energy_mWh")
                * 1000,  # Ah|Wh -> mAh|mWh
                (pl.col("unix_time_s") + pl.col("uts_ms") / 1000).alias("unix_time_s"),
                pl.col("step_count").diff().fill_null(1).abs().gt(0).cum_sum().alias("step_count"),
            ]
        )
        .drop("uts_ms")
        .unique(subset="index", keep="first")
    )


def _read_ndc_16_filetype_1(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("voltage_V", "<f4"),
            ("current_mA", "<f4"),
        ]
    )
    return _bytes_to_df(buf, dtype, add_index=True).with_columns(
        [
            pl.col("voltage_V") / 10000,
            pl.col("current_mA"),
        ]
    )


def _read_ndc_16_filetype_5(buf: bytes) -> pl.DataFrame:
    header = 4096
    if buf[header + 132 : header + 133] == b"\x65":
        dtype = np.dtype(
            [
                ("_mask", "<i1"),
                ("voltage_V", "<f4"),
                ("temperature_degC", "<i2"),
            ]
        )
        df = _bytes_to_df(buf, dtype).with_columns(
            [
                pl.col("voltage_V") / 10000,  # 0.1 mV -> V
                pl.col("temperature_degC").cast(pl.Float32) * 0.1,  # 0.1'C -> 'C
                pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("index"),
            ]
        )
        # Drop empty columns
        cols_to_drop = [col for col in ["voltage_V", "temperature_degC"] if df.filter(pl.col(col) != 0).is_empty()]
        return df.select(pl.exclude(cols_to_drop))
    msg = "Unknown file structure for ndc version 16 filetype 5."
    raise NotImplementedError(msg)


def _read_ndc_16_filetype_7(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("cycle_count", "<u4"),
            ("step_index", "<u4"),
            ("_pad1", "V16"),
            ("step_type", "<u1"),
            ("_pad2", "V8"),
            ("index", "<u4"),
            ("_pad3", "V63"),
        ]
    )
    return _bytes_to_df(buf, dtype).with_columns(
        [
            pl.col("cycle_count") + 1,
            _count_changes(pl.col("step_index")).alias("step_count"),
        ]
    )


def _read_ndc_16_filetype_18(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("step_time_s", "<u4"),
            ("_pad1", "V1"),
            ("charge_capacity_mAh", "<f4"),
            ("discharge_capacity_mAh", "<f4"),
            ("charge_energy_mWh", "<f4"),
            ("discharge_energy_mWh", "<f4"),
            ("_pad2", "V8"),
            ("dt", "<i4"),
            ("unix_time_s", "<u4"),
            ("step_count", "<u4"),
            ("index", "<u4"),
            ("uts_ms", "<u2"),
            ("_pad3", "V53"),
        ]
    )
    return (
        _bytes_to_df(buf, dtype)
        .with_columns(
            [
                pl.col("step_time_s", "dt").cast(pl.Float64) / 1000,
                (
                    pl.col("charge_capacity_mAh", "discharge_capacity_mAh", "charge_energy_mWh", "discharge_energy_mWh")
                    / 3600
                ).cast(pl.Float32),  # mAs|mWs -> mAh|mWh
                (pl.col("unix_time_s") + pl.col("uts_ms") / 1000).alias("unix_time_s"),
            ]
        )
        .drop("uts_ms")
        .unique(subset="index", keep="first")
    )


def _read_ndc_17_filetype_1(buf: bytes) -> pl.DataFrame:
    return _read_ndc_14_filetype_1(buf)


def _read_ndc_17_filetype_7(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("cycle_count", "<u4"),
            ("step_index", "<u4"),
            ("_pad1", "V16"),
            ("step_type", "<u1"),
            ("_pad2", "V8"),
            ("step_count", "<u4"),
            ("_pad3", "V63"),
        ]
    )
    return _bytes_to_df(buf, dtype).with_columns(
        [
            pl.col("cycle_count") + 1,
            pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("step_count"),
        ]
    )


def _read_ndc_17_filetype_18(buf: bytes) -> pl.DataFrame:
    dtype = np.dtype(
        [
            ("step_time_s", "<u4"),
            ("_pad1", "V1"),
            ("charge_capacity_mAh", "<f4"),
            ("discharge_capacity_mAh", "<f4"),
            ("charge_energy_mWh", "<f4"),
            ("discharge_energy_mWh", "<f4"),
            ("_pad2", "V8"),
            ("dt", "<i4"),
            ("unix_time_s", "<u4"),
            ("step_count", "<u4"),
            ("index", "<u4"),
            ("uts_ms", "<u2"),
            ("_pad3", "V53"),
        ]
    )
    return (
        _bytes_to_df(buf, dtype)
        .with_columns(
            [
                pl.col("step_time_s", "dt").cast(pl.Float64) / 1000,
                (
                    pl.col("charge_capacity_mAh", "discharge_capacity_mAh", "charge_energy_mWh", "discharge_energy_mWh")
                    * 1000
                ).cast(pl.Float32),  # Ah|Wh -> mAh|mWh
                (pl.col("unix_time_s") + pl.col("uts_ms") / 1000).alias("unix_time_s"),
            ]
        )
        .drop("uts_ms")
        .unique(subset="index", keep="first")
    )


def _bytes_to_df(
    buf: bytes,
    dtype: np.dtype,
    data_start_ind: int = 132,
    record_size: int = 4096,
    file_header_records: int = 1,
    record_end_pad: int = 1,
    *,
    use_bitmask: bool = True,
    add_index: bool = False,
) -> pl.DataFrame:
    """Read bytes into a polars DataFrame.

    Args:
        buf: Bytes object containing the binary data.
        dtype: Numpy dtype describing the record structure.
        data_start_ind: Index in bytes of the start of the data in the record.
        record_size: Total size of a single record in bytes.
        file_header_records: Number of records in the file header.
        record_end_pad: Number of bytes at the end of the record that cannot contain data.
        use_bitmask: Whether to use bitmask to filter data.
        add_index: Whether to add an index column, used for filetype 1.

    Returns:
        DataFrame containing the data, dropping columns starting with '_'.

    """
    # Read entire file into 1 byte array nrecords x record_size
    num_records = len(buf) // record_size - file_header_records
    arr = np.frombuffer(
        buf,
        dtype=np.uint8,
        offset=record_size * file_header_records,
    ).reshape((num_records, record_size))
    rows_per_record = (record_size - data_start_ind - record_end_pad) // dtype.itemsize

    if use_bitmask:
        bitmask_start = 4
        bits_in_bitmask = int(np.ceil(rows_per_record / 8))
        bitmask = arr[:, bitmask_start : bitmask_start + bits_in_bitmask]
        bitmask = np.unpackbits(bitmask, bitorder="little", axis=1)[:, :rows_per_record].ravel()

    # Remove padding columns
    useful_cols = [name for name in dtype.names if not name.startswith("_")]
    dtype_no_pad = dtype[useful_cols]

    # Slice the data
    data_end_ind = data_start_ind + dtype.itemsize * rows_per_record
    data = np.ascontiguousarray(arr[:, data_start_ind:data_end_ind]).view(dtype_no_pad).ravel()

    df = pl.DataFrame(data)

    if not use_bitmask:
        return df.filter(pl.col("index") != 0)
    if add_index:
        df = df.with_columns(pl.int_range(1, pl.len() + 1, dtype=pl.Int32).alias("index"))
    return df.filter(pl.Series(bitmask).ne(0))


# Map NDC (version, filetype) to handler functions
NDC_READERS: dict[tuple[int, int], Callable[[bytes], pl.DataFrame]] = {
    (2, 1): _read_ndc_2_filetype_1,
    (2, 5): _read_ndc_2_filetype_5,
    (5, 1): _read_ndc_5_filetype_1,
    (5, 5): _read_ndc_5_filetype_5,
    (11, 1): _read_ndc_11_filetype_1,
    (11, 5): _read_ndc_11_filetype_5,
    (11, 7): _read_ndc_11_filetype_7,
    (11, 18): _read_ndc_11_filetype_18,
    (14, 1): _read_ndc_14_filetype_1,
    (14, 5): _read_ndc_14_filetype_5,
    (14, 7): _read_ndc_14_filetype_7,
    (14, 18): _read_ndc_14_filetype_18,
    (16, 1): _read_ndc_16_filetype_1,
    (16, 5): _read_ndc_16_filetype_5,
    (16, 7): _read_ndc_16_filetype_7,
    (16, 18): _read_ndc_16_filetype_18,
    (17, 1): _read_ndc_17_filetype_1,
    (17, 5): _read_ndc_14_filetype_5,
    (17, 7): _read_ndc_17_filetype_7,
    (17, 18): _read_ndc_17_filetype_18,
}
