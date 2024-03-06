"""This module is used for loading data using the ``instrument="custom"`` method.
If no ``instrument_file`` is given (either directly or through the use
of the ``::`` separator), the default instrument file (yaml) will be used.
As a "short-cut", this loader will be used if you set the ``instrument``
to the name of the instrument file (with the ``.yml`` extension) e.g.
``c = cellpy.get(rawfile, instrument="instrumentfile.yml")``.
The default instrument file is defined in the cellpy configuration file
(available through ``prms.Instruments.custom_instrument_definitions_file``).
"""

# This module works, but is by no means finished. The module is meant to
# be developed further allowing for example
# to provide custom parsers. At the moment, we anticipate that it only should
# work with "simple" files (txt-files, xlsx, ...), however, it is
# possible to extend the scope to allow for providing parsers that also can read
# binary files. The future will show.

import logging
import sys
from abc import ABC
from pathlib import Path

import pandas as pd

from cellpy import prms
from cellpy.readers.instruments.base import find_delimiter_and_start, AutoLoader
from cellpy.readers.instruments.configurations import (
    register_local_configuration_from_yaml_file,
)


class DataLoader(AutoLoader, ABC):
    """Class for loading data from txt files."""

    instrument_name = "custom"
    raw_ext = "*"

    def __init__(self, instrument_file=None, **kwargs):
        if instrument_file is None:
            logging.debug("No instrument_file provided - checking default for one")
            # currently using the name custom_instrument_definitions_file for this also
            # consider adding a separate config parameter for the default instrument file
            # e.g. local_instrument_default_file
            instrument_file = prms.Instruments.custom_instrument_definitions_file
        if not instrument_file:
            raise FileExistsError(
                "Missing instrument definition file "
                "(not given and not defined in config)"
            )
        if not Path(instrument_file).is_file():
            # searching in the Instruments folder:
            instrument_dir = Path(prms.Paths.instrumentdir)
            logging.debug(f"Looking for file in {instrument_dir}")
            instrument_file_in_instrument_dir = instrument_dir / instrument_file
            if not instrument_file_in_instrument_dir.is_file():
                logging.debug(f"Could not find {instrument_file_in_instrument_dir}")
                raise FileExistsError(
                    "Instrument definition file not found! " f"({instrument_file})"
                )
            instrument_file = instrument_file_in_instrument_dir

        logging.debug(f"Instrument definition file: {instrument_file}")
        self.local_instrument_file = instrument_file
        super().__init__()

    default_model = None
    supported_models = None

    def pre_init(self):
        self.auto_register_config = False
        self.config_params = register_local_configuration_from_yaml_file(
            self.local_instrument_file
        )

    # TODO: rewrite this:
    def parse_loader_parameters(self, **kwargs):
        auto_format = kwargs.get("auto_format", False)
        if auto_format:
            self._auto_formatter()

    def _config_sub_parser(self, key_label, default_value=None, **kwargs):
        return kwargs.pop(
            key_label, self.config_params.formatters.get(key_label, default_value)
        )

    # TODO: rewrite this:
    def parse_formatter_parameters(self, **kwargs):
        self.file_format = self._config_sub_parser(
            "file_format", default_value="csv", **kwargs
        )
        # print("FORMATTERS".center(80, "="))
        # print(self.config_params.formatters)

        # rewrite this on a later stage to use functions and dict lookup instead of if - else
        if self.file_format == "csv":
            self.sep = self._config_sub_parser("sep", default_value=None, **kwargs)
            self.skiprows = self._config_sub_parser(
                "skiprows", default_value=0, **kwargs
            )
            self.header = self._config_sub_parser("header", default_value=0, **kwargs)
            self.encoding = self._config_sub_parser(
                "encoding", default_value="utf-8", **kwargs
            )
            self.decimal = self._config_sub_parser(
                "decimal", default_value=".", **kwargs
            )
            self.thousands = self._config_sub_parser(
                "thousands", default_value=None, **kwargs
            )

        elif self.file_format == "xlsx":
            self.table_name = self._config_sub_parser(
                "table_name", default_value="sheet 1", **kwargs
            )

        elif self.file_format == "xls":
            self.table_name = self._config_sub_parser(
                "table_name", default_value="sheet 1", **kwargs
            )

        elif self.file_format == "json":
            print("json not implemented yet")
            sys.exit()

        else:
            print(f"{self.file_format} not implemented yet")
            sys.exit()

    # TODO: consider rewriting this:
    def _auto_formatter(self):
        separator, first_index = find_delimiter_and_start(
            self.name,
            separators=None,
            checking_length_header=100,
            checking_length_whole=200,
        )
        self.encoding = "UTF-8"  # consider adding a find_encoding function
        self.sep = separator
        self.skiprows = first_index - 1  # consider adding a find_rows_to_skip function
        self.header = 0  # consider adding a find_header function

        logging.critical(
            f"auto-formatting:\n  {self.sep=}\n  {self.skiprows=}\n  {self.header=}\n  {self.encoding=}\n"
        )

    def query_file(self, name):
        """Query the file and return a pandas dataframe."""

        # rewrite this on a later stage to use functions and dict lookup instead of if - else
        if self.file_format == "csv":
            logging.debug(f"parsing with pandas.read_csv: {name}")
            logging.critical(
                f"{self.sep=}, {self.skiprows=}, {self.header=}, {self.encoding=}, {self.decimal=}"
            )
            data_df = pd.read_csv(
                name,
                sep=self.sep,
                skiprows=self.skiprows,
                header=self.header,
                encoding=self.encoding,
                decimal=self.decimal,
                thousands=self.thousands,
            )
        elif self.file_format == "xls":
            logging.debug(
                f"parsing with pandas.read_excel using xlrd (old format): {name}"
            )
            sheet_name = self.table_name

            raw_frame = pd.read_excel(name, engine="xlrd", sheet_name=None)
            matching = [s for s in raw_frame.keys() if s.startswith(sheet_name)]
            if matching:
                return raw_frame[matching[0]]
            raise IOError(f"Could not find the sheet {sheet_name} in {name}")

        elif self.file_format == "xlsx":
            logging.debug(f"parsing with pandas.read_excel: {name}")
            sheet_name = self.table_name
            raw_frame = pd.read_excel(
                name, engine="openpyxl", sheet_name=None
            )  # TODO: replace this with pd.ExcelReader
            matching = [s for s in raw_frame.keys() if s.startswith(sheet_name)]
            if matching:
                logging.debug(f"read sheet: {sheet_name}")
                return raw_frame[matching[0]]
            raise IOError(f"Could not find the sheet {sheet_name} in {name}")

        elif self.file_format == "json":
            raise IOError(
                f"Could not read {name}, {self.file_format} not supported yet"
            )
        else:
            raise IOError(
                f"Could not read {name}, {self.file_format} not supported yet"
            )

        return data_df


def _check_loader_from_outside_with_get():
    import pathlib

    import cellpy

    pd.options.display.max_columns = 100

    base_path_win = pathlib.Path("C:/scripting")
    base_path_mac = pathlib.Path("/Users/jepe/scripting")

    if sys.platform == "win32":
        base_path = base_path_win
        out = pathlib.Path(r"C:\scripting\trash")
    else:
        base_path = base_path_mac
        out = pathlib.Path("/Users/jepe/tmp")

    instrument = "custom"

    file_number = 3

    if file_number == 1:
        filename = "custom_data_001.csv"
        instrument_file = "cellpy/testdata/data/custom_instrument_001.yml"
    elif file_number == 2:
        filename = "custom_data_002.xlsx"
        instrument_file = "cellpy/testdata/instruments/custom_002.yml"
    elif file_number == 3:
        filename = "custom_data_003.xls"
        instrument_file = "cellpy/testdata/instruments/custom_003.yml"
    else:
        print("not implemented")
        return

    # NEXT: test hooks and make tests

    instrument_file = base_path / instrument_file
    data_dir = base_path / "cellpy/testdata/data"
    name = data_dir / filename

    print(f"File exists? {name.is_file()}")
    if not name.is_file():
        print(f"could not find {name} ")
        return

    print(" RUNNING CELLPY GET ".center(80, "="))
    print(f"{instrument=}")

    c = cellpy.get(
        filename=name,
        instrument=instrument,
        instrument_file=instrument_file,
        mass=1.0,
        auto_summary=False,
    )
    _process_cellpy_object(name, c, out)


def _process_cellpy_object(name, c, out):
    import matplotlib.pyplot as plt

    pd.options.display.max_columns = 100

    print(f"loaded the file - now lets see what we got")
    raw = c.data.raw
    raw.to_clipboard()
    print(raw.head())
    c.make_step_table()

    steps = c.data.steps
    summary = c.data.summary

    raw.to_csv(out / "raw.csv", sep=";")
    steps.to_csv(out / "steps.csv", sep=";")
    summary.to_csv(out / "summary.csv", sep=";")

    fig_1, (ax1, ax2, ax3, ax4) = plt.subplots(
        4,
        1,
        figsize=(6, 10),
        constrained_layout=True,
        sharex=True,
    )
    raw.plot(x="test_time", y="voltage", ax=ax1)
    raw.plot(x="test_time", y="current", ax=ax2)
    raw.plot(x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3)
    raw.plot(x="test_time", y="cycle_index", ax=ax4)
    fig_1.suptitle(f"{name.name}", fontsize=16)

    n = c.get_number_of_cycles()
    print(f"Number of cycles: {n}")

    plt.legend()
    plt.show()

    outfile = out / "test_out"
    c.save(outfile)


if __name__ == "__main__":
    _check_loader_from_outside_with_get()
