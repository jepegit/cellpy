"""Neware txt data - with explanations.txt


1. Update SUPPORTED_MODELS and raw_ext
2. Add instrument to prms.py
    a. create the boxed item:

        Neware = {"default_model": "UIO"}
        Neware = box.Box(Neware)

        ...
    b. add it to Instruments:
        Instruments = InstrumentsClass(
        ...
        Neware=Neware
        )

    c. Update the dataclass in prms.py:

        @dataclass
        class InstrumentsClass(CellPyConfig):
            tester: str
            custom_instrument_definitions_file: Union[str, None]
            Arbin: box.Box
            Maccor: box.Box
            Neware: box.Box

3. (optionally) add Neware defaults to .cellpy_prms_default.conf

4. Create instrument configuration file in readers/instruments/configurations

    formatters
    states
    normal_headers_renaming_dict
    file_info
    raw_units
    post_processors

"""

import pandas as pd

from cellpy import prms
from cellpy import exceptions
from cellpy.parameters.internal_settings import (
    HeaderDict,
    base_columns_float,
    base_columns_int,
    headers_normal,
)
from cellpy.readers.instruments.base import TxtLoader


SUPPORTED_MODELS = {
    "UIO": "neware_txt_zero",
}


MUST_HAVE_RAW_COLUMNS = [
    headers_normal.test_time_txt,
    headers_normal.step_time_txt,
    headers_normal.current_txt,
    headers_normal.voltage_txt,
    headers_normal.step_index_txt,
    headers_normal.cycle_index_txt,
    headers_normal.charge_capacity_txt,
    headers_normal.discharge_capacity_txt,
]


class DataLoader(TxtLoader):
    """Class for loading data from Neware txt files."""

    name = "neware_txt"
    raw_ext = "csv"

    default_model = prms.Instruments.Maccor["default_model"]  # Required
    supported_models = SUPPORTED_MODELS  # Required

    @staticmethod
    def get_headers_aux(raw):
        """Defines the so-called auxiliary table column headings"""

        headers = HeaderDict()
        for col in raw.columns:
            if col.startswith("Aux_"):
                ncol = col.replace("/", "_")
                ncol = "".join(ncol.split("(")[0])
                headers[col] = ncol.lower()

        return headers

    def validate(self, data):
        """A simple check that all the needed columns has been successfully
        loaded and that they get the correct type"""
        missing_must_have_columns = []

        # validating the float-type raw data
        for col in base_columns_float:
            if col in data.raw.columns:
                data.raw[col] = pd.to_numeric(data.raw[col], errors="coerce")
            else:
                if col in MUST_HAVE_RAW_COLUMNS:
                    missing_must_have_columns.append(col)

        # validating the integer-type raw data
        for col in base_columns_int:
            if col in data.raw.columns:
                data.raw[col] = pd.to_numeric(
                    data.raw[col], errors="coerce", downcast="integer"
                )
            else:
                if col in MUST_HAVE_RAW_COLUMNS:
                    missing_must_have_columns.append(col)

        if missing_must_have_columns:
            raise exceptions.IOError(
                f"Missing needed columns: {missing_must_have_columns}\nAborting!"
            )
        return data


def check_retrieve_file():
    import pathlib

    pd.options.display.max_columns = 100
    data_root = pathlib.Path(r"C:\scripting\cellpy_dev_resources\dev_data\agnieszka")
    name = data_root / r"Si80Gr20-3.csv"
    print(name)
    print(f"Exists? {name.is_file()}")
    if name.is_file():
        return name
    else:
        raise IOError(f"could not locate the file {name}")


def check_dev_loader(name=None, model=None):
    if name is None:
        name = check_retrieve_file()

    pd.options.display.max_columns = 100

    sep = ","
    loader1 = DataLoader(sep=sep, model=model)
    dd = loader1.loader(name)

    raw = dd[0].raw
    print(len(raw))
    print(raw.columns)



def check_loader(name=None, number=1, model="one"):
    import matplotlib.pyplot as plt

    if name is None:
        name = check_retrieve_file(number)
    print(name)
    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"

    loader = DataLoader(sep="\t", model=model)
    dd = loader.loader(name)
    raw = dd[0].raw
    raw.plot(x="data_point", y="current", title="current vs data-point")
    raw.plot(
        x="data_point",
        y=["charge_capacity", "discharge_capacity"],
        title="capacity vs data-point",
    )
    raw.plot(
        x="test_time",
        y=["charge_capacity", "discharge_capacity"],
        title="capacity vs test-time",
    )
    raw.plot(
        x="step_time",
        y=["charge_capacity", "discharge_capacity"],
        title="capacity vs step-time",
    )
    print(raw.head())
    plt.show()


if __name__ == "__main__":
    check_dev_loader(model="UIO")
