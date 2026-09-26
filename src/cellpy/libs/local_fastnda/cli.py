"""CLI to use fastnda conversion."""

import json
import logging
from pathlib import Path
from typing import Annotated, Literal, cast, get_args
from zipfile import BadZipFile

import typer
from tqdm import tqdm

import cellpy.libs.local_fastnda as fastnda

LOGGER = logging.getLogger(__name__)

app = typer.Typer(add_completion=False)

AcceptedFormats = Literal["csv", "parquet", "arrow", "feather", "h5", "hdf5"]
InFileArgument = Annotated[Path, typer.Argument(help="Path to .nda or .ndax file.")]
OutFileArgument = Annotated[
    Path | None, typer.Argument(help="Path to output file, if blank will use input filepath with new extension.")
]
InFolderArgument = Annotated[Path, typer.Argument(help="Path to folder containing .nda or .ndax files.")]
OutFolderArgument = Annotated[
    Path | None, typer.Argument(help="Path to folder to output to. If blank, will use input folder.")
]
OptionalFormatOption = Annotated[
    AcceptedFormats | None,
    typer.Option(
        "--format", "-f", help="Output file format. If not used, inferred from out_file, csv if out_file not used."
    ),
]
FormatOption = Annotated[
    AcceptedFormats,
    typer.Option("--format", "-f", help="Output file format."),
]
VerbosityOption = Annotated[
    int, typer.Option("--verbose", "-v", count=True, help="Increase verbosity. Use -vv for maximum detail.")
]
QuietOption = Annotated[
    int, typer.Option("--quiet", "-q", count=True, help="Decrease verbosity. Use -qq to remove progress bars.")
]
CycleModeOption = Annotated[
    Literal["chg", "dchg", "auto", "raw"], typer.Option("--cycle-mode", "-m", help="How to incremember cycle number.")
]
PandasOption = Annotated[
    bool,
    typer.Option(
        "--pandas",
        "-p",
        help="Save with old pandas-compatible format (only for parquet, arrow, feather, without --raw-categories).",
    ),
]
ColumnsOption = Annotated[
    Literal["default", "bdf"],
    typer.Option(
        "--columns",
        "-c",
        help="Format of the output columns",
    ),
]
RecursiveOption = Annotated[
    bool,
    typer.Option(
        "--recursive",
        "-r",
        help="Search for .nda/.ndax files in subfolders. Output files will have same folder structure.",
    ),
]
RawCategoriesOption = Annotated[
    bool,
    typer.Option(
        "--raw-categories", help="Store step_type categorical column as integer codes, e.g. 1 instead of 'CC_Chg'."
    ),
]


def _require_pandas() -> None:
    """Check if pandas is installed."""
    try:
        import pandas as pd  # noqa: F401, PLC0415
        import pyarrow as pa  # noqa: F401, PLC0415
    except ImportError as e:
        msg = (
            "'pandas' and 'pyarrow' optional dependencies are not installed.\n"
            "Install extras with `pip install fastnda[extras]`"
        )
        raise RuntimeError(msg) from e


def _require_tables() -> None:
    """Check if pytables is installed for hdf5."""
    try:
        import tables  # noqa: F401, PLC0415
    except ImportError as e:
        msg = "'tables' optional dependency is not installed.\nInstall extras with `pip install fastnda[extras]`"
        raise RuntimeError(msg) from e


class TqdmHandler(logging.Handler):
    """Class to handle logs while using tqdm progress bar."""

    def emit(self, record: logging.LogRecord) -> None:
        """Write log to console."""
        msg = self.format(record)
        tqdm.write(msg)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: VerbosityOption = 0,
    quiet: QuietOption = 0,
) -> None:
    """CLI for converting Neware .nda/.ndax files."""
    verbosity = verbose - quiet
    if verbosity <= -2:
        log_level = logging.ERROR
    elif verbosity == -1:
        log_level = logging.CRITICAL
    elif verbosity == 0:
        log_level = logging.WARNING
    elif verbosity == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    ctx.obj = {"verbosity": verbosity}

    handler = TqdmHandler()
    handler.setFormatter(logging.Formatter("%(name)s:%(levelname)s: %(message)s"))
    root.addHandler(handler)


@app.command()
def convert(
    in_file: InFileArgument,
    out_file: OutFileArgument = None,
    file_format: OptionalFormatOption = None,
    cycle_mode: CycleModeOption = "chg",
    columns: ColumnsOption = "default",
    *,
    pandas: PandasOption = False,
    raw_categories: RawCategoriesOption = False,
) -> None:
    """Convert a .nda or .ndax file to another type.

    Args:
        in_file: Path to .nda or .ndax file
        out_file: Path to the output file
        file_format (default csv): Format of file to convert to, e.g. csv or parquet
        cycle_mode: How to increment cycle number
            'chg': (Default) Cycle incremented by a charge step following a discharge
            'dchg': Cycle incremented by a discharge step following a charge
            'auto': Identifies the first non-rest state as the incremental state
            'raw': Leaves cycles as it is found in the Neware file
        columns: Selects how to format the output columns
            'default': fastnda columns, e.g. 'voltage_V', 'current_mA'
            'bdf': battery-data-format columns, e.g. 'voltage_volt', 'current_ampere'
        pandas: Whether to save in old pandas-safe format
        raw_categories: Return `step_type` column as integer codes.

    """
    file_format = file_format or _infer_extension(out_file) or "csv"
    if file_format in {"h5", "hdf5"}:
        _require_tables()
        _require_pandas()
    elif pandas and file_format in {"parquet", "arrow", "feather"}:
        _require_pandas()
    if out_file is None:
        out_file = in_file.with_suffix("." + file_format)
    _convert_with_type(in_file, out_file, file_format, cycle_mode, columns, pandas, raw_categories)


@app.command()
def batch_convert(
    ctx: typer.Context,
    in_folder: InFolderArgument,
    out_folder: OutFolderArgument = None,
    file_format: FormatOption = "csv",
    cycle_mode: CycleModeOption = "chg",
    columns: ColumnsOption = "default",
    *,
    recursive: RecursiveOption = False,
    pandas: PandasOption = False,
    raw_categories: RawCategoriesOption = False,
) -> None:
    """Convert a folder of .nda or .ndax files to another type.

    Args:
        in_folder: Path to a folder containing .nda and/or .ndax files
        out_folder: Path to the output file
        file_format: Type of file to convert to, e.g. csv or parquet
        cycle_mode: How to increment cycle number
            'chg': (Default) Cycle incremented by a charge step following a discharge
            'dchg': Cycle incremented by a discharge step following a charge
            'auto': Identifies the first non-rest state as the incremental state
            'raw': Leaves cycles as it is found in the Neware file
        columns: Selects how to format the output columns
            'default': fastnda columns, e.g. 'voltage_V', 'current_mA'
            'bdf': battery-data-format columns, e.g. 'voltage_volt', 'current_ampere'
        recursive: Whether to search recursively in subfolders
        pandas: Whether to save in old pandas-safe format
        raw_categories: Return `step_type` column as integer codes.

    """
    if file_format in {"h5", "hdf5"}:
        _require_pandas()
        _require_tables()
    elif pandas and file_format in {"parquet", "arrow", "feather"}:
        _require_pandas()

    if not in_folder.exists():
        msg = f"Folder {in_folder} does not exist."
        raise FileNotFoundError(msg)

    if not in_folder.is_dir():
        msg = f"{in_folder} is not a folder."
        raise FileNotFoundError(msg)

    if out_folder is None:
        out_folder = in_folder

    in_files = in_folder.rglob("*.nda*") if recursive else in_folder.glob("*.nda*")
    file_list = list(in_files)
    if len(file_list) == 0:
        msg = "No .nda or .ndax files found."
        if not recursive:
            msg += " To search in sub-folders use --recursive or -r."
        raise FileNotFoundError(msg)

    disable_tqdm = ctx.obj.get("verbosity", 0) <= -2
    LOGGER.info("Found %d files to convert in %s.", len(file_list), in_folder)
    for in_file in tqdm(file_list, desc="Converting files", disable=disable_tqdm):
        out_file = out_folder / in_file.relative_to(in_folder).with_suffix("." + file_format)
        out_file.parent.mkdir(exist_ok=True)
        try:
            _convert_with_type(in_file, out_file, file_format, cycle_mode, columns, pandas, raw_categories)
        except (ValueError, BadZipFile, KeyError, AttributeError):
            LOGGER.exception("Failed to convert %s.", in_file)


def _infer_extension(
    out_file: Path | None,
) -> AcceptedFormats | None:
    if not out_file:
        return None
    file_format = out_file.suffix[1:].lower()
    if file_format in get_args(AcceptedFormats):
        return cast("AcceptedFormats", file_format)
    return None


def _convert_with_type(
    in_file: Path,
    out_file: Path,
    file_format: FormatOption,
    cycle_mode: CycleModeOption,
    columns: ColumnsOption,
    pandas: bool,
    raw_categories: bool,
) -> None:
    df = fastnda.read(
        in_file,
        cycle_mode=cycle_mode,
        columns=columns,
        raw_categories=raw_categories,
    )

    match file_format:
        case "csv":
            df.write_csv(out_file)
        case "parquet":
            if pandas:
                df.to_pandas().to_parquet(out_file)
            else:
                df.write_parquet(out_file)
        case "arrow" | "feather":
            if pandas:
                df.to_pandas().to_feather(out_file)
            else:
                df.write_ipc(out_file)
        case "h5" | "hdf5":
            df.to_pandas().to_hdf(out_file, key="data", format="table")


@app.command()
def print_metadata(in_file: InFileArgument, indent: int | None = 4) -> None:
    """Print file metadata to terminal."""
    typer.echo(json.dumps(fastnda.read_metadata(in_file), indent=indent))


@app.command()
def convert_metadata(
    in_file: InFileArgument,
    out_file: OutFileArgument = None,
    indent: int | None = 4,
) -> None:
    """Convert .nda / .ndax metadata to json."""
    if out_file is None:
        out_file = in_file.with_suffix(".json")
    with out_file.open("w") as f:
        json.dump(fastnda.read_metadata(in_file), f, indent=indent)
