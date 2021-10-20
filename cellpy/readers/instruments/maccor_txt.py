"""Maccor txt data"""
import logging

from dateutil.parser import parse

import pandas as pd

from cellpy.readers.core import (
    FileID,
    Cell,
)
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy import prms

DEBUG_MODE = prms.Reader.diagnostics  # not used

# not updated yet
unit_labels = {
    "resistance": "Ohms",

    # not observed yet:
    "time": "s",
    "current": "A",
    "voltage": "V",
    "power": "W",
    "capacity": "Ah",
    "energy": "Wh",
    "temperature": "C",
}

# not observed yet
incremental_unit_labels = {
    "dv_dt": f"{unit_labels['voltage']}/{unit_labels['time']}",
    "dq_dv": f"{unit_labels['capacity']}/{unit_labels['voltage']}",
    "dv_dq": f"{unit_labels['voltage']}/{unit_labels['capacity']}",
}

normal_headers_renaming_dict = {
    "data_point_txt": f"Rec#",
    "datetime_txt": f"DPt Time",
    "test_time_txt": f"TestTime",
    "step_time_txt": f"StepTime",
    "cycle_index_txt": f"Cyc#",
    "step_index_txt": f"Step",
    "current_txt": f"Amps",
    "voltage_txt": f"Volts",
    "power_txt": f"Watt-hr",
    "charge_capacity_txt": f"Amp-hr",
    "charge_energy_txt": f"Watt-hr",
    "ac_impedance_txt": f"ACImp/{unit_labels['resistance']}",
    "internal_resistance_txt": f"DCIR/{unit_labels['resistance']}",

    # not observed yet:
    "sub_step_index_txt": f"Sub_Step_Index",  # new
    "sub_step_time_txt": f"Sub_Step_Time",  # new
    "discharge_capacity_txt": f"Discharge_Capacity({unit_labels['capacity']})",
    "discharge_energy_txt": f"Discharge_Energy({unit_labels['energy']})",
    "dv_dt_txt": f"dV/dt({incremental_unit_labels['dv_dt']})",  # TODO: include the new cols into internal settings
    "dq_dv_txt": f"dV/dt({incremental_unit_labels['dq_dv']})",  # TODO: include the new cols into internal settings
    "dv_dq_txt": f"dV/dt({incremental_unit_labels['dv_dq']})",  # TODO: include the new cols into internal settings
    "acr_txt": f"Internal_Resistance({unit_labels['resistance']})",  # TODO: include the new cols into internal settings
    "aci_phase_angle_txt": f"ACI_Phase_Angle",
    "ref_aci_phase_angle_txt": f"Reference_ACI_Phase_Angle",
    "ref_ac_impedance_txt": f"Reference_AC_Impedance",
    "is_fc_data_txt": f"Is_FC_Data",
    "test_id_txt": f"Test_ID",
    "ref_voltage_txt": f"Reference_Voltage({unit_labels['resistance']})",  # new
    "frequency_txt": f"Frequency",  # new
    "amplitude_txt": f"Amplitude",  # new
    "channel_id_txt": f"Channel_ID",  # new Arbin SQL Server
    "data_flag_txt": f"Data_Flags",  # new Arbin SQL Server
    "test_name_txt": f"Test_Name",  # new Arbin SQL Server

}

# not observed yet
not_implemented_in_cellpy_yet_renaming_dict = {
    f"Power({unit_labels['power']})": "power",
    f"ACR({unit_labels['resistance']})": "acr",
    f"dV/dt({incremental_unit_labels['dv_dt']})": "dv_dt",
    f"dQ/dV({incremental_unit_labels['dq_dv']})": "dq_dv",
    f"dV/dQ({incremental_unit_labels['dv_dq']})": "dv_dq",
}

columns_to_keep = [
    'TestTime',
    'Rec#',
    'Cyc#',
    'Step',
    'StepTime',
    'Amp-hr',
    'Watt-hr',
    'Amps',
    'Volts',
    'State',
    'ES',
    'DPt Time',
    'ACImp/Ohms',
    'DCIR/Ohms',
]

STATES = {
    "column_name": "State",
    "charge_keys": ["C"],
    "discharge_keys": ["D"],
    "rest_keys": ["R"],
}


class MaccorTxtLoader(Loader):
    """ Class for loading data from Maccor txt files."""

    def __init__(self, **kwargs):
        """initiates the MaccorTxtLoader class"""
        self.sep = kwargs.pop("sep", prms.Reader.sep)
        self.include_aux = kwargs.pop("include_aux", False)
        self.keep_all_columns = kwargs.pop("keep_all_columns", False)
        self.raw_headers_normal = normal_headers_renaming_dict
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings"""
        # covered by cellpy at the moment
        return get_headers_normal()

    @staticmethod
    def get_headers_aux(df):
        """Defines the so-called auxiliary table column headings"""
        headers = HeaderDict()
        for col in df.columns:
            if col.startswith("Aux_"):
                ncol = col.replace("/", "_")
                ncol = "".join(ncol.split("(")[0])
                headers[col] = ncol.lower()

        return headers

    # not updated yet
    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        return raw_units

    # not updated yet
    @staticmethod
    def get_raw_limits():
        """returns a dictionary with resolution limits"""
        raw_limits = dict()
        raw_limits["current_hard"] = 0.000_000_000_000_1
        raw_limits["current_soft"] = 0.000_01
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 0.001
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    def loader(self, name, **kwargs):
        """returns a Cell object with loaded data.

        Loads data from arbin SQL server db.

        Args:
            name (str): name of the file
            kwargs (dict): key-word arguments from raw_loader

        Returns:
            new_tests (list of data objects)
        """
        new_tests = []
        sep = kwargs.get("sep", None)
        if sep is not None:
            self.sep = sep
        data_df = self._query_csv(name)
        if not self.keep_all_columns:
            data_df = data_df[columns_to_keep]

        data = Cell()

        # metadata is unfortunately not available for csv dumps
        data.loaded_from = name
        data.channel_index = None
        data.test_ID = None
        data.test_name = name  # should fix this
        data.channel_number = None
        data.creator = None
        data.item_ID = None
        data.schedule_file_name = None
        data.start_datetime = None

        # Generating a FileID project:
        fid = FileID(name)
        data.raw_data_files.append(fid)

        data.raw = data_df
        data.raw_data_files_length.append(len(data_df))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented yet

        data = self._post_process(data)
        data = self.identify_last_data_point(data)
        new_tests.append(data)

        return new_tests

    def _post_process(self, data):
        split_caps = True
        split_current = True
        set_index = True
        rename_headers = True
        set_cycle_number_not_zero = True
        convert_date_time_to_datetime = True
        convert_step_time_to_timedelta = True
        convert_test_time_to_timedelta = True
        if rename_headers:
            columns = {}
            for key in self.cellpy_headers_normal:
                if key in normal_headers_renaming_dict:
                    old_header = normal_headers_renaming_dict[key]
                    new_header = self.cellpy_headers_normal[key]
                    columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            if self.include_aux:
                new_aux_headers = self.get_headers_aux(data.raw)
                data.raw.rename(index=str, columns=new_aux_headers, inplace=True)

            data.raw.rename(
                index=str,
                columns=not_implemented_in_cellpy_yet_renaming_dict,
                inplace=True,
            )

        if split_current:
            data.raw = current_splitter(data.raw)
        if split_caps:
            data.raw = capacity_splitter(data.raw)

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(hdr_data_point, drop=False)

        if set_cycle_number_not_zero:
            data.raw[self.cellpy_headers_normal.cycle_index_txt] += 1

        hdr_date_time = self.cellpy_headers_normal.datetime_txt
        if convert_date_time_to_datetime:
            data.raw[hdr_date_time] = pd.to_datetime(data.raw[hdr_date_time])

        if convert_step_time_to_timedelta:
            hdr_step_time = self.cellpy_headers_normal.step_time_txt
            data.raw[hdr_step_time] = pd.to_timedelta(data.raw[hdr_step_time]).dt.total_seconds()

        if convert_test_time_to_timedelta:
            hdr_test_time = self.cellpy_headers_normal.test_time_txt
            x = pd.to_timedelta(data.raw[hdr_test_time])
            data.raw[hdr_test_time] = x.dt.total_seconds()

        data.start_datetime = data.raw[hdr_date_time].iat[0]

        return data

    def _query_csv(self, name, sep=None, skiprows=2, header=1):
        sep = sep or self.sep
        data_df = pd.read_csv(name, sep=sep, skiprows=skiprows, header=header)
        return data_df


def state_splitter(
    raw, base_col_name="charge_capacity", n_charge=1, n_discharge=1, new_col_name_charge="charge_capacity",
    new_col_name_discharge="discharge_capacity",
    temp_col_name_charge="tmp_charge", temp_col_name_discharge="tmp_discharge", states=None,
):
    headers = get_headers_normal()
    cycle_index_hdr = headers["cycle_index_txt"]
    data_point = headers["data_point_txt"]
    if states is None:
        states = {
            "column_name": "State",
            "charge_keys": ["C"],
            "discharge_keys": ["D"],
            "rest_keys": ["R"],
        }
    state_column = states["column_name"]
    charge_keys = states["charge_keys"]
    rest_keys = states["rest_keys"]
    discharge_keys = states["discharge_keys"]

    raw[temp_col_name_charge] = 0
    if temp_col_name_charge != temp_col_name_discharge:
        raw[temp_col_name_discharge] = 0

    cycle_numbers = raw[cycle_index_hdr].unique()
    # cell_type = prms.Reader.cycle_mode
    good_cycles = []
    bad_cycles = []
    for i in cycle_numbers:
        try:
            charge = raw.loc[
                (raw[state_column].isin(charge_keys)) & (raw[cycle_index_hdr] == i),
                [data_point, base_col_name],
            ]

            discharge = raw.loc[
                (raw[state_column].isin(discharge_keys)) & (raw[cycle_index_hdr] == i),
                [data_point, base_col_name],
            ]

            if not charge.empty:
                charge_last_index, charge_last_val = charge.iloc[-1]
                raw[temp_col_name_charge].update(n_charge * charge[base_col_name])

                raw.loc[
                    (raw[data_point] > charge_last_index)
                    & (raw[cycle_index_hdr] == i),
                    temp_col_name_charge,
                ] = charge_last_val

            if not discharge.empty:
                (
                    discharge_last_index,
                    discharge_last_val,
                ) = discharge.iloc[-1]
                raw[temp_col_name_discharge].update(n_discharge * discharge[base_col_name])

                raw.loc[
                    (raw[data_point] > discharge_last_index)
                    & (raw[cycle_index_hdr] == i),
                    temp_col_name_discharge,
                ] = discharge_last_val

            good_cycles.append(i)
        except Exception:
            bad_cycles.append(i)
    if bad_cycles:
        logging.critical(f"The data contains bad cycles: {bad_cycles}")

    raw[new_col_name_charge] = raw[temp_col_name_charge]
    raw = raw.drop([temp_col_name_charge], axis=1)
    if temp_col_name_charge != temp_col_name_discharge:
        raw[new_col_name_discharge] = raw[temp_col_name_discharge]
        raw = raw.drop([temp_col_name_discharge], axis=1)
    return raw


def current_splitter(raw):
    headers = get_headers_normal()
    return state_splitter(
        raw,
        base_col_name="current", n_charge=1, n_discharge=-1, temp_col_name_charge="tmp_charge",
        new_col_name_charge=headers["current_txt"], new_col_name_discharge=headers["current_txt"],
        temp_col_name_discharge="tmp_charge",
        states=STATES,
    )


def capacity_splitter(raw):
    headers = get_headers_normal()
    return state_splitter(
        raw,
        base_col_name="charge_capacity", n_charge=1, n_discharge=1,
        new_col_name_charge=headers["charge_capacity_txt"], new_col_name_discharge=headers["discharge_capacity_txt"],
        temp_col_name_charge="tmp_charge", temp_col_name_discharge="tmp_discharge",
        states=STATES,
    )


def test_loader():
    import pathlib
    import matplotlib.pyplot as plt
    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"
    datadir = pathlib.Path(
        r"C:\scripts\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    print(f"Exists? {name.is_file()}")
    loader = MaccorTxtLoader(sep="\t")
    dd = loader.loader(name)
    raw = dd[0].raw
    raw.plot(x="data_point", y="current")
    raw.plot(x="data_point", y=["charge_capacity", "discharge_capacity"])
    raw.plot(x="test_time", y=["charge_capacity", "discharge_capacity"])
    raw.plot(x="step_time", y=["charge_capacity", "discharge_capacity"])
    print(raw.head())
    plt.show()


def test_loader_from_outside():
    # NOT EDITED YET!!!
    from cellpy import cellreader
    import matplotlib.pyplot as plt
    import pathlib

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


def test_loader_from_outside_with_get():
    import cellpy
    import matplotlib.pyplot as plt
    import pathlib

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripts\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripts\notebooks\Div")
    print(f"Exists? {name.is_file()}")

    c = cellpy.get(filename=name, instrument="maccor_txt", sep="\t", mass=1.0)

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


if __name__ == "__main__":
    test_loader_from_outside_with_get()
