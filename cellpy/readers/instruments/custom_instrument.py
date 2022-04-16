"""This module is used for loading data using the `instrument="custom"` method.
If no `instrument_file` is given (either directly or through the use
of the :: separator), the default instrument file (yaml) will be used."""

# This module is currently almost equal to the local_instrument module
# It might be best to merge them into one (tweak set_instrument)
import logging
from abc import ABC
from pathlib import Path

import pandas as pd

from cellpy import prms
from cellpy.readers.instruments.base import find_delimiter_and_start, AutoLoader
from cellpy.readers.instruments.configurations import (
    register_local_configuration_from_yaml_file,
)


# TODO:
#  1. fix tests
#  2. implement from old custom
#  3. check with round robin data
#  4. check units vs raw_units
#  5. method for generating column headers from units etc (might already be
#     implemented somewhere, maybe in the configuration module?)
#  6. check if it is possible to use CustomTxtLoader for loading
#     arbin txt files.
#  7. implement registering plug-ins and loaders


class CustomTxtLoader(AutoLoader, ABC):
    """Class for loading data from txt files."""

    def __init__(self, instrument_file=None):
        if instrument_file is None:
            logging.debug("No instrument_file provided - checking default")
            instrument_file = prms.Instruments.custom_instrument_definitions_file
        if not instrument_file:
            raise FileExistsError("Missing instrument definition file "
                                  "(not given and not defined in config)")
        if not Path(instrument_file).is_file():
            # searching in the Instruments folder:
            instrument_dir = Path(prms.Paths.instrumentdir)
            logging.debug(f"Looking for file in {instrument_dir}")
            instrument_file_in_instrument_dir = instrument_dir / instrument_file
            if not instrument_file_in_instrument_dir.is_file():
                logging.debug(f"Could not find {instrument_file_in_instrument_dir}")
                raise FileExistsError("Instrument definition file not found! "
                                      f"({instrument_file})")
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
        sep = kwargs.get("sep", None)
        if sep is not None:
            self.sep = sep
        if self.sep is None:
            self._auto_formatter()

    # TODO: rewrite this:
    def parse_formatter_parameters(self, **kwargs):
        if not self.config_params.formatters:
            # check for "over-rides" from arguments in class initialization
            self.sep = kwargs.pop("sep", None)
            self.skiprows = kwargs.pop("skiprows", 0)
            self.header = kwargs.pop("header", 0)
            self.encoding = kwargs.pop("encoding", "utf-8")
            self.decimal = kwargs.pop("decimal", ".")
            self.thousands = kwargs.pop("thousands", None)

        else:
            self.sep = kwargs.pop("sep", self.config_params.formatters["sep"])
            self.skiprows = kwargs.pop(
                "skiprows", self.config_params.formatters["skiprows"]
            )
            self.header = kwargs.pop("header", self.config_params.formatters["header"])
            self.encoding = kwargs.pop(
                "encoding", self.config_params.formatters["encoding"]
            )
            self.decimal = kwargs.pop(
                "decimal", self.config_params.formatters["decimal"]
            )
            self.thousands = kwargs.pop(
                "thousands", self.config_params.formatters["thousands"]
            )

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

    # TODO: rewrite this so that the query_file method can use other functions than pd.read_csv:
    def query_file(self, name):
        logging.debug(f"parsing with pandas.read_csv: {name}")
        logging.critical(f"{self.sep=}, {self.skiprows=}, {self.header=}, {self.encoding=}, {self.decimal=}")
        data_df = pd.read_csv(
            name,
            sep=self.sep,
            skiprows=self.skiprows,
            header=self.header,
            encoding=self.encoding,
            decimal=self.decimal,
            thousands=self.thousands,
        )
        return data_df


def check_loader_from_outside_with_get():
    import pathlib
    import sys

    import matplotlib.pyplot as plt
    import pandas as pd

    import cellpy
    from cellpy.parameters.internal_settings import headers_normal

    keep = [
        headers_normal.data_point_txt,
        headers_normal.test_time_txt,
        headers_normal.step_time_txt,
        headers_normal.step_index_txt,
        headers_normal.cycle_index_txt,
        headers_normal.current_txt,
        headers_normal.voltage_txt,
        headers_normal.ref_voltage_txt,
        headers_normal.charge_capacity_txt,
        headers_normal.discharge_capacity_txt,
        headers_normal.internal_resistance_txt,
        # "ir_pct_change"
    ]

    INSTRUMENT = "custom"
    INSTRUMENT_FILE = "/Users/jepe/scripting/cellpy/testdata/data/custom_instrument_001.yml"
    FILENAME = "custom_data_001.csv"
    DATADIR = r"/Users/jepe/scripting/cellpy/testdata/data"

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(DATADIR)
    name = datadir / FILENAME
    out = pathlib.Path("/Users/jepe/tmp")
    print(f"File exists? {name.is_file()}")
    if not name.is_file():
        print(f"could not find {name} ")
        return

    print("RUNNING CELLPY GET")
    print(f"{INSTRUMENT=}")
    c = cellpy.get(
        filename=name, instrument=INSTRUMENT, instrument_file=INSTRUMENT_FILE,
        mass=1.0, auto_summary=False
    )

    print(f"loaded the file - now lets see what we got")
    raw = c.cell.raw
    raw.to_clipboard()
    print(raw.head())
    c.make_step_table()

    steps = c.cell.steps
    summary = c.cell.summary

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
    raw.plot(
        x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3
    )
    raw.plot(x="test_time", y="cycle_index", ax=ax4)
    fig_1.suptitle(f"{name.name}", fontsize=16)

    n = c.get_number_of_cycles()
    print(f"Number of cycles: {n}")

    plt.legend()
    plt.show()

    outfile = out / "test_out"
    c.save(outfile)


if __name__ == "__main__":
    check_loader_from_outside_with_get()
