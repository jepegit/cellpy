"""Internal legacy definitions for loading old file formats."""

# Supported versions: 3, 4, 5

import logging

from cellpy.parameters.internal_settings import (
    get_headers_summary,
    get_headers_normal,
    get_headers_step_table,
)

HEADERS_NORMAL = get_headers_normal()
HEADERS_SUMMARY = get_headers_summary()
HEADERS_STEP_TABLE = get_headers_step_table()

# TODO: this should be defined in internal_settings
HEADERS_KEYS_STEP_TABLE_EXTENDED = [
    "point",
    "test_time",
    "step_time",
    "current",
    "voltage",
    "charge",
    "discharge",
    "internal_resistance",
]
HEADERS_STEP_TABLE_EXTENSIONS = ["min", "max", "avr", "first", "last", "delta", "std"]

headers_normal_v5 = dict()
headers_summary_v5 = dict()
headers_step_table_v5 = dict()
headers_journal_v0 = dict()

headers_summary_v5["cycle_index"] = "Cycle_Index"
headers_summary_v5["data_point"] = "Data_Point"
headers_summary_v5["test_time"] = "Test_Time"
headers_summary_v5["datetime"] = "DateTime"
headers_summary_v5["discharge_capacity"] = "Discharge_Capacity(mAh/g)"
headers_summary_v5["charge_capacity"] = "Charge_Capacity(mAh/g)"
headers_summary_v5["discharge_capacity_raw"] = "Discharge_Capacity"
headers_summary_v5["charge_capacity_raw"] = "Charge_Capacity"

headers_summary_v5["cumulated_charge_capacity"] = "Cumulated_Charge_Capacity(mAh/g)"
headers_summary_v5[
    "cumulated_discharge_capacity"
] = "Cumulated_Discharge_Capacity(mAh/g)"
headers_summary_v5["coulombic_efficiency"] = "Coulombic_Efficiency(percentage)"
headers_summary_v5[
    "cumulated_coulombic_efficiency"
] = "Cumulated_Coulombic_Efficiency(percentage)"
headers_summary_v5["coulombic_difference"] = "Coulombic_Difference(mAh/g)"
headers_summary_v5[
    "cumulated_coulombic_difference"
] = "Cumulated_Coulombic_Difference(mAh/g)"
headers_summary_v5["discharge_capacity_loss"] = "Discharge_Capacity_Loss(mAh/g)"
headers_summary_v5["charge_capacity_loss"] = "Charge_Capacity_Loss(mAh/g)"
headers_summary_v5[
    "cumulated_discharge_capacity_loss"
] = "Cumulated_Discharge_Capacity_Loss(mAh/g)"
headers_summary_v5[
    "cumulated_charge_capacity_loss"
] = "Cumulated_Charge_Capacity_Loss(mAh/g)"
headers_summary_v5["ir_discharge"] = "IR_Discharge(Ohms)"
headers_summary_v5["ir_charge"] = "IR_Charge(Ohms)"
headers_summary_v5["ocv_first_min"] = "OCV_First_Min(V)"
headers_summary_v5["ocv_second_min"] = "OCV_Second_Min(V)"
headers_summary_v5["ocv_first_max"] = "OCV_First_Max(V)"
headers_summary_v5["ocv_second_max"] = "OCV_Second_Max(V)"
headers_summary_v5["end_voltage_discharge"] = "End_Voltage_Discharge(V)"
headers_summary_v5["end_voltage_charge"] = "End_Voltage_Charge(V)"
headers_summary_v5["cumulated_ric_disconnect"] = "RIC_Disconnect(none)"
headers_summary_v5["cumulated_ric_sei"] = "RIC_SEI(none)"
headers_summary_v5["cumulated_ric"] = "RIC(none)"

headers_summary_v5["normalized_cycle_index"] = "Normalized_Cycle_Index"
# Sum of irreversible capacity:
headers_summary_v5["low_level"] = "Low_Level(percentage)"
# SEI loss:
headers_summary_v5["high_level"] = "High_Level(percentage)"
headers_summary_v5["shifted_charge_capacity"] = "Charge_Endpoint_Slippage(mAh/g)"
headers_summary_v5["shifted_discharge_capacity"] = "Discharge_Endpoint_Slippage(mAh/g)"
headers_summary_v5["temperature_last"] = "Last_Temperature(C)"
headers_summary_v5["temperature_mean"] = "Average_Temperature(C)"
headers_summary_v5["charge_c_rate"] = "Charge_C_rate"
headers_summary_v5["discharge_c_rate"] = "Discharge_C_rate"
headers_summary_v5["pre_aux"] = "Aux_"

# - normal (data) -

headers_normal_v5["aci_phase_angle_txt"] = "ACI_Phase_Angle"
headers_normal_v5["ref_aci_phase_angle_txt"] = "Reference_ACI_Phase_Angle"

headers_normal_v5["ac_impedance_txt"] = "AC_Impedance"
headers_normal_v5["ref_ac_impedance_txt"] = "Reference_AC_Impedance"  # new

headers_normal_v5["charge_capacity_txt"] = "Charge_Capacity"
headers_normal_v5["charge_energy_txt"] = "Charge_Energy"
headers_normal_v5["current_txt"] = "Current"
headers_normal_v5["cycle_index_txt"] = "Cycle_Index"
headers_normal_v5["data_point_txt"] = "Data_Point"
headers_normal_v5["datetime_txt"] = "DateTime"
headers_normal_v5["discharge_capacity_txt"] = "Discharge_Capacity"
headers_normal_v5["discharge_energy_txt"] = "Discharge_Energy"
headers_normal_v5["internal_resistance_txt"] = "Internal_Resistance"

headers_normal_v5["is_fc_data_txt"] = "Is_FC_Data"
headers_normal_v5["step_index_txt"] = "Step_Index"
headers_normal_v5["sub_step_index_txt"] = "Sub_Step_Index"  # new

headers_normal_v5["step_time_txt"] = "Step_Time"
headers_normal_v5["sub_step_time_txt"] = "Sub_Step_Time"  # new

headers_normal_v5["test_id_txt"] = "Test_ID"
headers_normal_v5["test_time_txt"] = "Test_Time"

headers_normal_v5["voltage_txt"] = "Voltage"
headers_normal_v5["ref_voltage_txt"] = "Reference_Voltage"  # new

headers_normal_v5["dv_dt_txt"] = "dV/dt"
headers_normal_v5["frequency_txt"] = "Frequency"  # new
headers_normal_v5["amplitude_txt"] = "Amplitude"  # new

# - step table -

headers_step_table_v5["test"] = "test"
headers_step_table_v5["ustep"] = "ustep"
headers_step_table_v5["cycle"] = "cycle"
headers_step_table_v5["step"] = "step"
headers_step_table_v5["test_time"] = "test_time"
headers_step_table_v5["step_time"] = "step_time"
headers_step_table_v5["sub_step"] = "sub_step"
headers_step_table_v5["type"] = "type"
headers_step_table_v5["sub_type"] = "sub_type"
headers_step_table_v5["info"] = "info"
headers_step_table_v5["voltage"] = "voltage"
headers_step_table_v5["current"] = "current"
headers_step_table_v5["charge"] = "charge"
headers_step_table_v5["discharge"] = "discharge"
headers_step_table_v5["point"] = "point"
headers_step_table_v5["internal_resistance"] = "ir"
headers_step_table_v5["internal_resistance_change"] = "ir_pct_change"
headers_step_table_v5["rate_avr"] = "rate_avr"


headers_journal_v0["filename"] = "filenames"
headers_journal_v0["mass"] = "masses"
headers_journal_v0["total_mass"] = "total_masses"
headers_journal_v0["loading"] = "loadings"
headers_journal_v0["fixed"] = "fixed"
headers_journal_v0["label"] = "labels"
headers_journal_v0["cell_type"] = "cell_types"
headers_journal_v0["raw_file_names"] = "raw_file_names"
headers_journal_v0["cellpy_file_name"] = "cellpy_file_names"
headers_journal_v0["group"] = "groups"
headers_journal_v0["sub_group"] = "sub_groups"


def translate_headers(data_sets, cellpy_file_version):
    # this works for upgrading to versions 6,
    # remark that the extensions for the step table is hard-coded
    logging.debug(f"translate headers from v{cellpy_file_version}")

    summary_rename_dict = {
        headers_summary_v5[key]: HEADERS_SUMMARY[key]
        for key in HEADERS_SUMMARY
        if key in headers_summary_v5
    }

    steps_rename_dict = {
        headers_step_table_v5[key]: HEADERS_STEP_TABLE[key]
        for key in HEADERS_STEP_TABLE
        if key in headers_step_table_v5
    }

    steps_rename_dict_extensions = {}
    for key in HEADERS_KEYS_STEP_TABLE_EXTENDED:
        for extension in HEADERS_STEP_TABLE_EXTENSIONS:
            old = "_".join([HEADERS_STEP_TABLE[key], extension])
            new = "_".join([headers_step_table_v5[key], extension])
            steps_rename_dict_extensions[old] = new

    raw_rename_dict = {
        headers_normal_v5[key]: HEADERS_NORMAL[key] for key in HEADERS_NORMAL
    }

    summary_index_name = HEADERS_SUMMARY["cycle_index"]
    raw_index_name = HEADERS_NORMAL["data_point_txt"]

    # from pprint import pprint
    # pprint(summary_rename_dict)
    # pprint(steps_rename_dict)
    # pprint(steps_rename_dict_extensions)
    # pprint(raw_rename_dict)

    new_data_sets = []
    for data_set in data_sets:
        data_set.summary.rename(columns=summary_rename_dict, inplace=True)
        data_set.raw.rename(columns=raw_rename_dict, inplace=True)
        data_set.steps.rename(columns=steps_rename_dict, inplace=True)
        data_set.steps.rename(columns=steps_rename_dict_extensions, inplace=True)

        # we also need to update the index-name
        data_set.summary.index.name = summary_index_name
        data_set.raw.index.name = raw_index_name

        new_data_sets.append(data_set)

        # pprint(data_set.summary.columns)
        # pprint(data_set.steps.columns)
        # pprint(data_set.raw.columns)
    # check(new_data_sets)
    return new_data_sets


def check(data_sets):
    for data_set in data_sets:
        print(" checking ".center(80, "-"))
        print("RAW")
        print(data_set.raw.columns)
        print("SUMMARY")
        print(data_set.summary.columns)
        print("STEPS")
        print(data_set.steps.columns)
    print("OK?")
