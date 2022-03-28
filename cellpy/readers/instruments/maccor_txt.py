"""Maccor txt data"""

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

DEBUG_MODE = prms.Reader.diagnostics  # not used

SUPPORTED_MODELS = {
    "ZERO": "maccor_txt_zero",
    "ONE": "maccor_txt_one",
    "TWO": "maccor_txt_two",
    "THREE": "maccor_txt_three",
    "FOUR": "maccor_txt_four",
    "WMG_SIMBA": "maccor_txt_three",
    "KIT_SIMBA": "maccor_txt_four",
    "KIT_COMMA_SIMBA": "maccor_txt_two",
    "UBHAM_SIMBA": "maccor_txt_three",
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


class MaccorTxtLoader(TxtLoader):
    """Class for loading data from Maccor txt files."""

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
        """A simple check that all the needed columns has been successfully loaded and that they get the correct type"""
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


def check_retrieve_file(n=1):
    import pathlib

    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"
    data_root = pathlib.Path(r"C:\scripting\cellpy_dev_resources")
    data_dir = data_root / r"2021_leafs_data\Charge-Discharge\Maccor series 4000"
    if n == 2:
        name = data_dir / "KIT-Full-cell-PW-HC-CT-cell016.txt"
    else:
        name = data_dir / "01_UBham_M50_Validation_0deg_01.txt"
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
    # prms.Reader.sep = "\t"

    sep = "\t"
    loader1 = MaccorTxtLoader(sep=sep, model=model)
    loader2 = MaccorTxtLoader(model="one")
    loader3 = MaccorTxtLoader(model="zero")
    loader4 = MaccorTxtLoader(model="zero")
    dd = loader1.loader(name)
    dd = loader2.loader(name)
    dd = loader3.loader(name)
    dd = loader4.loader(name)
    raw = dd[0].raw
    print(len(raw))


def check_dev_loader2(name=None, model=None, sep=None, number=2):
    if name is None:
        name = check_retrieve_file(number)

    pd.options.display.max_columns = 100

    if sep is not None and sep != "none":
        loader3 = MaccorTxtLoader(sep=sep, model=model)
    elif sep == "none":
        loader3 = MaccorTxtLoader(sep=None, model=model)
    else:
        loader3 = MaccorTxtLoader(model=model)

    dd = loader3.loader(name)

    raw = dd[0].raw
    print(len(raw))
    print(raw)


def check_loader(name=None, number=1, model="one"):
    import matplotlib.pyplot as plt

    if name is None:
        name = check_retrieve_file(number)
    print(name)
    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"

    loader = MaccorTxtLoader(sep="\t", model=model)
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


def check_loader_from_outside():
    # NOT EDITED YET!!!
    import pathlib

    import matplotlib.pyplot as plt

    from cellpy import cellreader

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripts\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripts\notebooks\Div")
    print(f"Exists? {name.is_file()}")

    c = cellreader.CellpyData()
    c.set_instrument("maccor_txt", sep="\t")

    c.from_raw(name)
    c.set_mass(1000)

    c.make_step_table()
    c.make_summary()

    raw = c.cell.raw
    steps = c.cell.steps
    summary = c.cell.summary
    raw.to_csv(r"C:\scripts\notebooks\Div\trash\raw.csv", sep=";")
    steps.to_csv(r"C:\scripts\notebooks\Div\trash\steps.csv", sep=";")
    summary.to_csv(r"C:\scripts\notebooks\Div\trash\summary.csv", sep=";")

    fig_1, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 10))
    raw.plot(x="test_time", y="voltage", ax=ax1)
    raw.plot(x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3)
    raw.plot(x="test_time", y="current", ax=ax2)

    n = c.get_number_of_cycles()
    print(f"number of cycles: {n}")

    cycle = c.get_cap(1, method="forth-and-forth")
    print(cycle.head())

    fig_2, (ax4, ax5, ax6) = plt.subplots(1, 3)
    cycle.plot(x="capacity", y="voltage", ax=ax4)
    s = c.get_step_numbers()
    t = c.sget_timestamp(1, s[1])
    v = c.sget_voltage(1, s[1])
    steps = c.sget_step_numbers(1, s[1])

    print("step numbers:")
    print(s)
    print("sget step numbers:")
    print(steps)
    print("\ntesttime:")
    print(t)
    print("\nvoltage")
    print(v)

    ax5.plot(t, v, label="voltage")
    ax6.plot(t, steps, label="steps")

    fig_3, (ax7, ax8) = plt.subplots(2, sharex=True)
    raw.plot(x="test_time", y="voltage", ax=ax7)
    raw.plot(x="test_time", y="step_index", ax=ax8)

    plt.legend()
    plt.show()

    outfile = out / "test_out"
    c.save(outfile)


def check_loader_from_outside_with_get():
    import pathlib

    import matplotlib.pyplot as plt

    import cellpy

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripting\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripting\trash")
    print(f"File exists? {name.is_file()}")
    if not name.is_file():
        print(f"could not find {name} ")
        return

    c = cellpy.get(filename=name, instrument="maccor_txt", model="one", mass=1.0)
    print("loaded")
    raw = c.cell.raw
    steps = c.cell.steps
    summary = c.cell.summary

    raw.to_csv(r"C:\scripting\trash\raw.csv", sep=";")
    steps.to_csv(r"C:\scripting\trash\steps.csv", sep=";")
    summary.to_csv(r"C:\scripting\trash\summary.csv", sep=";")

    fig_1, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 10))
    raw.plot(x="test_time", y="voltage", ax=ax1, title="voltage")
    raw.plot(
        x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3, title="caps"
    )
    raw.plot(x="test_time", y="current", ax=ax2, title="current")

    n = c.get_number_of_cycles()
    print(f"number of cycles: {n}")

    cycle = c.get_cap(1, method="forth-and-forth")

    fig_2, (ax4, ax5, ax6) = plt.subplots(1, 3)
    # cycle.plot(x="capacity", y="voltage", ax=ax4)
    s = c.get_step_numbers()
    t = c.sget_timestamp(1, s[1])
    v = c.sget_voltage(1, s[1])
    steps = c.sget_step_numbers(1, s[1])

    print("step numbers:")
    print(s)
    print("sget step numbers:")
    print(steps)
    print("\ntesttime:")
    print(t)
    print("\nvoltage")
    print(v)

    ax5.plot(t, v, label="voltage")
    ax6.plot(t, steps, label="steps")

    fig_3, (ax7, ax8) = plt.subplots(2, sharex=True)
    raw.plot(x="test_time", y="voltage", ax=ax7, title="voltage")
    raw.plot(x="test_time", y="step_index", ax=ax8, title="step index")

    plt.legend()
    plt.show()

    outfile = out / "test_out"
    c.save(outfile)


def check_loader_from_outside_with_get2():
    import pathlib

    import matplotlib.pyplot as plt

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

    # zero: auto
    # one:
    # two: KIT
    # three | WMB_SIMBA: WMG new
    INSTRUMENT = "maccor_txt"
    MODEL = "WMG_SIMBA"
    # MODEL = "two"
    # MODEL = None
    # MODEL = "KIT_SIMBA"
    # FILENAME = "1044-CT-MaccorExport.txt"  # WMG_SIMBA
    # FILENAME = "01_UBham_M50_Validation_0deg_01.txt"  # WMG_SIMBA and NONE
    # FILENAME = "KIT-Full-cell-PW-HC-CT-cell002.txt"
    # FILENAME = "KIT-Full-cell-PW-HC-CT-cell016.txt"
    # FILENAME = "KIT-Full-cell-PW-HC-CT-cell013.txt"  # Two
    # FILENAME = "KIT-Full-cell-PW-HC-CT-cell009.txt"  # FAILS in convert_date_time_to_datetime!
    FILENAME = "SIM-A7-1047-ET - 079.txt"
    DATADIR = r"C:\scripting\processing_cellpy\notebooks\test\new\data"

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(DATADIR)
    name = datadir / FILENAME
    out = pathlib.Path(r"C:\scripting\trash")
    print(f"File exists? {name.is_file()}")
    if not name.is_file():
        print(f"could not find {name} ")
        return

    c = cellpy.get(
        filename=name, instrument=INSTRUMENT, model=MODEL, mass=1.0, auto_summary=False
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
    raw.plot(x="test_time", y="voltage", ax=ax1, xlabel="")
    raw.plot(x="test_time", y="current", ax=ax2, xlabel="")
    raw.plot(
        x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3, xlabel=""
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
    # check_dev_loader2(model="two")
    # check_loader(number=2, model="two")
    check_loader_from_outside_with_get2()
