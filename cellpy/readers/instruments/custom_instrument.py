"""This module is used for loading data using the `instrument="custom"` method.
If no `instrument_file` is given (either directly or through the use
of the :: separator), the default instrument file (yaml) will be used."""

# This module is currently almost equal to the local_instrument module
# It might be best to merge them into one (tweak set_instrument)

from cellpy import prms
from cellpy.readers.instruments.base import TxtLoader
from cellpy.readers.instruments.configurations import (
    register_local_configuration_from_yaml_file,
)


# TODO:
#  0. check what happens if no instrument file is given
#  1. fix tests
#  2. implement from old custom
#  3. check with round robin data
#  4. check units vs raw_units
#  5. method for generating column headers from units etc (might already be
#     implemented somewhere, maybe in the configuration module?)
#  6. check if it is possible to use CustomTxtLoader for loading
#     arbin txt files.
#  7. implement registering plug-ins and loaders


class CustomTxtLoader(TxtLoader):
    """Class for loading data from txt files."""

    def __init__(self, instrument_file=None):
        if instrument_file is None:
            instrument_file = prms.Instruments.custom_instrument_definitions_file
        if not instrument_file:
            raise FileExistsError("Missing instrument definition file "
                                  "(not given and not defined in config)")
        self.local_instrument_file = instrument_file
        super().__init__()

    default_model = None
    supported_models = None

    def pre_init(self):
        self.auto_register_config = False
        self.config_params = register_local_configuration_from_yaml_file(
            self.local_instrument_file
        )


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
