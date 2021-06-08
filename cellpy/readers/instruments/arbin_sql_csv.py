"""arbin MS SQL Server csv data"""

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
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file  # not used

# Not used yet - only supporting loading raw data (normal)
FILE_NAME_POST_LABEL = {
    "statistics_cycle": "_StatisticByCycle.CSV",
    "statistics_step": "_StatisticBySteps.CSV",
    "normal": "_Wb_1.CSV",
}

unit_labels = {
    "time": "s",
    "current": "A",
    "voltage": "V",
    "power": "W",
    "capacity": "Ah",
    "energy": "Wh",
    "resistance": "Ohm",
    "temperature": "C",
}

incremental_unit_labels = {
    "dv_dt": f"{unit_labels['voltage']}/{unit_labels['time']}",
    "dq_dv": f"{unit_labels['capacity']}/{unit_labels['voltage']}",
    "dv_dq": f"{unit_labels['voltage']}/{unit_labels['capacity']}",
}

# Contains several headers not encountered yet in the Arbin SQL Server tables
normal_headers_renaming_dict = {
    "data_point_txt": f"Data_Point",
    "datetime_txt": f"Date_Time",
    "test_time_txt": f"Test_Time({unit_labels['time']})",
    "step_time_txt": f"Step_Time({unit_labels['time']})",
    "cycle_index_txt": f"Cycle_Index",
    "step_index_txt": f"Step_Index",
    "sub_step_index_txt": f"Sub_Step_Index",  # new
    "sub_step_time_txt": f"Sub_Step_Time",  # new
    "current_txt": f"Current({unit_labels['current']})",
    "voltage_txt": f"Voltage({unit_labels['voltage']})",
    "power_txt": f"Power({unit_labels['power']})",  # TODO: include the new cols into internal settings
    "charge_capacity_txt": f"Charge_Capacity({unit_labels['capacity']})",
    "charge_energy_txt": f"Charge_Energy({unit_labels['energy']})",
    "discharge_capacity_txt": f"Discharge_Capacity({unit_labels['capacity']})",
    "discharge_energy_txt": f"Discharge_Energy({unit_labels['energy']})",
    "acr_txt": f"Internal_Resistance({unit_labels['resistance']})",  # TODO: include the new cols into internal settings
    "internal_resistance_txt": f"Internal_Resistance({unit_labels['resistance']})",
    "dv_dt_txt": f"dV/dt({incremental_unit_labels['dv_dt']})",  # TODO: include the new cols into internal settings
    "dq_dv_txt": f"dV/dt({incremental_unit_labels['dq_dv']})",  # TODO: include the new cols into internal settings
    "dv_dq_txt": f"dV/dt({incremental_unit_labels['dv_dq']})",  # TODO: include the new cols into internal settings
    "aci_phase_angle_txt": f"ACI_Phase_Angle",  # not observed yet
    "ref_aci_phase_angle_txt": f"Reference_ACI_Phase_Angle",
    "ac_impedance_txt": f"AC_Impedance({unit_labels['resistance']})",
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

not_implemented_in_cellpy_yet_renaming_dict = {
    f"Power({unit_labels['power']})": "power",
    f"ACR({unit_labels['resistance']})": "acr",
    f"dV/dt({incremental_unit_labels['dv_dt']})": "dv_dt",
    f"dQ/dV({incremental_unit_labels['dq_dv']})": "dq_dv",
    f"dV/dQ({incremental_unit_labels['dv_dq']})": "dv_dq",
}


class ArbinCsvLoader(Loader):
    """ Class for loading arbin-data from MS SQL server."""

    def __init__(self):
        """initiates the ArbinSQLLoader class"""
        self.arbin_headers_normal = (
            self.get_headers_normal()
        )  # the column headers defined by Arbin
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings for Arbin SQL Server csv"""
        # covered by cellpy at the moment
        return get_headers_normal()

    @staticmethod
    def get_headers_aux(df):
        """Defines the so-called auxiliary table column headings for Arbin SQL Server csv"""
        headers = HeaderDict()
        for col in df.columns:
            if col.startswith("Aux_"):
                ncol = col.replace("/", "_")
                ncol = "".join(ncol.split("(")[0])
                headers[col] = ncol.lower()

        return headers

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        return raw_units

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

    # TODO: rename this (for all instruments) to e.g. load
    # TODO: implement more options (bad_cycles, ...)
    def loader(self, name, **kwargs):
        """returns a Cell object with loaded data.

        Loads data from arbin SQL server db.

        Args:
            name (str): name of the file

        Returns:
            new_tests (list of data objects)
        """
        new_tests = []

        data_df = self._query_csv(name)

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
        set_index = True
        rename_headers = True
        if rename_headers:
            columns = {}
            for key in self.arbin_headers_normal:
                old_header = normal_headers_renaming_dict[key]
                new_header = self.cellpy_headers_normal[key]
                columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            new_aux_headers = self.get_headers_aux(data.raw)
            data.raw.rename(index=str, columns=new_aux_headers, inplace=True)

            data.raw.rename(
                index=str,
                columns=not_implemented_in_cellpy_yet_renaming_dict,
                inplace=True,
            )

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(hdr_data_point, drop=False)

        hdr_date_time = self.arbin_headers_normal.datetime_txt
        data.start_datetime = parse(data.raw[hdr_date_time].iat[0])

        return data

    def _query_csv(self, name):
        # NOTE! I am using the prms.Reader.sep prm as the delimiter.
        data_df = pd.read_csv(name, sep=prms.Reader.sep)
        return data_df


def test_csv_loader():
    import pathlib

    datadir = pathlib.Path(
        r"C:\scripts\cellpy\dev_data\arbin_new\2021_02_02_standardageing_1C_25dC_1_2021_02_02_130709"
    )
    name = datadir / "2021_02_02_standardageing_1C_25dC_1_Channel_1_Wb_1.CSV"
    loader = ArbinCsvLoader()
    out = pathlib.Path(r"C:\scripts\notebooks\Div")
    dd = loader.loader(name)


def test_loader_from_outside():
    from cellpy import cellreader
    import matplotlib.pyplot as plt
    import pathlib

    datadir = pathlib.Path(
        r"C:\scripts\cellpy\dev_data\arbin_new\2021_02_02_standardageing_1C_25dC_1_2021_02_02_130709"
    )
    name = datadir / "2021_02_02_standardageing_1C_25dC_1_Channel_1_Wb_1.CSV"
    c = cellreader.CellpyData()
    c.set_instrument("arbin_sql_csv")

    c.from_raw(name)
    c.set_mass(1000)

    c.make_step_table()
    c.make_summary()

    # raw = c.cell.raw
    # steps = c.cell.steps
    # summary = c.cell.summary
    # raw.to_csv(r"C:\scripts\notebooks\Div\trash\raw.csv", sep=";")
    # steps.to_csv(r"C:\scripts\notebooks\Div\trash\steps.csv", sep=";")
    # summary.to_csv(r"C:\scripts\notebooks\Div\trash\summary.csv", sep=";")
    #
    # n = c.get_number_of_cycles()
    # print(f"number of cycles: {n}")
    #
    # cycle = c.get_cap(1, method="forth")
    # print(cycle.head())
    # # cycle.plot(x="capacity", y="voltage")
    # # plt.show()
    #
    # s = c.get_step_numbers()
    # t = c.sget_timestamp(1, s[1])
    # v = c.sget_voltage(1, s[1])
    # steps = c.sget_step_numbers(1, s[1])
    #
    # print("step numbers:")
    # print(s)
    # print("/ntesttime:")
    # print(t)
    # print("/nvoltage")
    # print(v)
    # plt.plot(t, v)
    # plt.plot(t, steps)
    # plt.show()

    outfile = datadir / "test_out"
    c.save(outfile)


def test_seamless_files():
    from cellpy import cellreader, prms
    import matplotlib.pyplot as plt
    import pathlib

    datadir = pathlib.Path(
        r"\\ad.ife.no\dfs\Org\MPT-BAT-LAB\Processed\Experiments\seamless\Raw data_excel"
    )
    name1 = datadir / r"20210430_seam10_01_01_cc_01_2021_04_30_172207\20210430_seam10_01_01_cc_01_Channel_48_Wb_1.csv"
    name2 = datadir / r"20210430_seam10_01_01_cc_01_2021_04_30_172207\20210430_seam10_01_01_cc_01_Channel_48_Wb_1.csv"

    c = cellreader.CellpyData()
    c.set_instrument("arbin_sql_csv")

    prms.Reader.sep = ";"

    c.from_raw(name1)
    c.set_mass(0.016569)

    c.make_step_table()
    c.make_summary()

    names = [name1, name2]
    cell_data = cellreader.CellpyData()
    cell_data.set_instrument("arbin_sql_csv")
    cell_data.loadcell(names, mass=0.016569, )


if __name__ == "__main__":
    test_seamless_files()
