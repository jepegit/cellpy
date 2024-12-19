import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .. import externals as externals
from cellpy.parameters.internal_settings import BaseHeaders, CELLPY_FILE_VERSION

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


@dataclass
class HeadersRawV4(BaseHeaders):
    aci_phase_angle_txt: str = "ACI_Phase_Angle"
    ref_aci_phase_angle_txt: str = "Reference_ACI_Phase_Angle"
    ac_impedance_txt: str = "AC_Impedance"
    ref_ac_impedance_txt: str = "Reference_AC_Impedance"
    charge_capacity_txt: str = "Charge_Capacity"
    charge_energy_txt: str = "Charge_Energy"
    current_txt: str = "Current"
    cycle_index_txt: str = "Cycle_Index"
    data_point_txt: str = "Data_Point"
    datetime_txt: str = "DateTime"
    discharge_capacity_txt: str = "Discharge_Capacity"
    discharge_energy_txt: str = "Discharge_Energy"
    internal_resistance_txt: str = "Internal_Resistance"
    is_fc_data_txt: str = "Is_FC_Data"
    step_index_txt: str = "Step_Index"
    sub_step_index_txt: str = "Sub_Step_Index"
    step_time_txt: str = "Step_Time"
    sub_step_time_txt: str = "Sub_Step_Time"
    test_id_txt: str = "Test_ID"
    test_time_txt: str = "Test_Time"
    voltage_txt: str = "Voltage"
    ref_voltage_txt: str = "Reference_Voltage"
    dv_dt_txt: str = "dV/dt"
    frequency_txt: str = "Frequency"
    amplitude_txt: str = "Amplitude"


@dataclass
class HeadersRawV5(BaseHeaders):
    aci_phase_angle_txt: str = "ACI_Phase_Angle"
    ref_aci_phase_angle_txt: str = "Reference_ACI_Phase_Angle"
    ac_impedance_txt: str = "AC_Impedance"
    ref_ac_impedance_txt: str = "Reference_AC_Impedance"
    charge_capacity_txt: str = "Charge_Capacity"
    charge_energy_txt: str = "Charge_Energy"
    current_txt: str = "Current"
    cycle_index_txt: str = "Cycle_Index"
    data_point_txt: str = "Data_Point"
    datetime_txt: str = "DateTime"
    discharge_capacity_txt: str = "Discharge_Capacity"
    discharge_energy_txt: str = "Discharge_Energy"
    internal_resistance_txt: str = "Internal_Resistance"
    is_fc_data_txt: str = "Is_FC_Data"
    step_index_txt: str = "Step_Index"
    sub_step_index_txt: str = "Sub_Step_Index"
    step_time_txt: str = "Step_Time"
    sub_step_time_txt: str = "Sub_Step_Time"
    test_id_txt: str = "Test_ID"
    test_time_txt: str = "Test_Time"
    voltage_txt: str = "Voltage"
    ref_voltage_txt: str = "Reference_Voltage"
    dv_dt_txt: str = "dV/dt"
    frequency_txt: str = "Frequency"
    amplitude_txt: str = "Amplitude"


@dataclass
class HeadersRawV6(BaseHeaders):
    aci_phase_angle_txt: str = "ACI_Phase_Angle"
    ref_aci_phase_angle_txt: str = "Reference_ACI_Phase_Angle"
    ac_impedance_txt: str = "AC_Impedance"
    ref_ac_impedance_txt: str = "Reference_AC_Impedance"
    charge_capacity_txt: str = "Charge_Capacity"
    charge_energy_txt: str = "Charge_Energy"
    current_txt: str = "Current"
    cycle_index_txt: str = "Cycle_Index"
    data_point_txt: str = "Data_Point"
    datetime_txt: str = "DateTime"
    discharge_capacity_txt: str = "Discharge_Capacity"
    discharge_energy_txt: str = "Discharge_Energy"
    internal_resistance_txt: str = "Internal_Resistance"
    is_fc_data_txt: str = "Is_FC_Data"
    step_index_txt: str = "Step_Index"
    sub_step_index_txt: str = "Sub_Step_Index"
    step_time_txt: str = "Step_Time"
    sub_step_time_txt: str = "Sub_Step_Time"
    test_id_txt: str = "Test_ID"
    test_time_txt: str = "Test_Time"
    voltage_txt: str = "Voltage"
    ref_voltage_txt: str = "Reference_Voltage"
    dv_dt_txt: str = "dV/dt"
    frequency_txt: str = "Frequency"
    amplitude_txt: str = "Amplitude"


@dataclass
class HeadersRawV7(BaseHeaders):
    aci_phase_angle_txt: str = "aci_phase_angle"
    ref_aci_phase_angle_txt: str = "ref_aci_phase_angle"
    ac_impedance_txt: str = "ac_impedance"
    ref_ac_impedance_txt: str = "ref_ac_impedance"
    charge_capacity_txt: str = "charge_capacity"
    charge_energy_txt: str = "charge_energy"
    current_txt: str = "current"
    cycle_index_txt: str = "cycle_index"
    data_point_txt: str = "data_point"
    datetime_txt: str = "date_time"
    discharge_capacity_txt: str = "discharge_capacity"
    discharge_energy_txt: str = "discharge_energy"
    internal_resistance_txt: str = "internal_resistance"
    power_txt: str = "power"
    is_fc_data_txt: str = "is_fc_data"
    step_index_txt: str = "step_index"
    sub_step_index_txt: str = "sub_step_index"
    step_time_txt: str = "step_time"
    sub_step_time_txt: str = "sub_step_time"
    test_id_txt: str = "test_id"
    test_time_txt: str = "test_time"
    voltage_txt: str = "voltage"
    ref_voltage_txt: str = "reference_voltage"
    dv_dt_txt: str = "dv_dt"
    frequency_txt: str = "frequency"
    amplitude_txt: str = "amplitude"
    channel_id_txt: str = "channel_id"
    data_flag_txt: str = "data_flag"
    test_name_txt: str = "test_name"


@dataclass
class HeadersSummaryV5(BaseHeaders):
    cycle_index: str = "Cycle_Index"
    data_point: str = "Data_Point"
    test_time: str = "Test_Time"
    datetime: str = "DateTime"
    discharge_capacity_raw: str = "Discharge_Capacity"
    charge_capacity_raw: str = "Charge_Capacity"

    discharge_capacity: str = "discharge_capacity_u_mAh_g"
    charge_capacity: str = "charge_capacity_u_mAh_g"
    cumulated_charge_capacity: str = "cumulated_charge_capacity_u_mAh_g"
    cumulated_discharge_capacity: str = "cumulated_discharge_capacity_u_mAh_g"

    coulombic_efficiency: str = "Coulombic_Efficiency(percentage)"

    cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency_u_percentage"
    coulombic_difference: str = "coulombic_difference_u_mAh_g"
    cumulated_coulombic_difference: str = "cumulated_coulombic_difference_u_mAh_g"
    discharge_capacity_loss: str = "discharge_capacity_loss_u_mAh_g"
    charge_capacity_loss: str = "charge_capacity_loss_u_mAh_g"
    cumulated_discharge_capacity_loss: str = "cumulated_discharge_capacity_loss_u_mAh_g"
    cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss_u_mAh_g"

    ir_discharge: str = "IR_Discharge(Ohms)"
    ir_charge: str = "IR_Charge(Ohms)"
    ocv_first_min: str = "OCV_First_Min(V)"
    ocv_second_min: str = "OCV_Second_Min(V)"
    ocv_first_max: str = "OCV_First_Max(V)"
    ocv_second_max: str = "OCV_Second_Max(V)"
    end_voltage_discharge: str = "End_Voltage_Discharge(V)"
    end_voltage_charge: str = "End_Voltage_Charge(V)"
    cumulated_ric_disconnect: str = "RIC_Disconnect(none)"
    cumulated_ric_sei: str = "RIC_SEI(none)"
    cumulated_ric: str = "RIC(none)"

    normalized_cycle_index: str = "Normalized_Cycle_Index"

    normalized_charge_capacity: str = "normalized_charge_capacity"
    normalized_discharge_capacity: str = "normalized_discharge_capacity"

    low_level: str = "Low_Level(percentage)"
    high_level: str = "High_Level(percentage)"
    shifted_charge_capacity: str = "Charge_Endpoint_Slippage(mAh/g)"
    shifted_discharge_capacity: str = "Discharge_Endpoint_Slippage(mAh/g)"
    temperature_last: str = "Last_Temperature(C)"
    temperature_mean: str = "Average_Temperature(C)"

    areal_charge_capacity: str = "areal_charge_capacity_u_mAh_cm2"
    areal_discharge_capacity: str = "areal_discharge_capacity_u_mAh_cm2"

    charge_c_rate: str = "Charge_C_rate"
    discharge_c_rate: str = "Discharge_C_rate"
    # pre_aux: str = "aux_"


@dataclass
class HeadersSummaryV6(BaseHeaders):
    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    test_name: str = "test_name"
    data_flag: str = "data_flag"
    channel_id: str = "channel_id"
    discharge_capacity: str = "discharge_capacity_u_mAh_g"
    charge_capacity: str = "charge_capacity_u_mAh_g"
    cumulated_charge_capacity: str = "cumulated_charge_capacity_u_mAh_g"
    cumulated_discharge_capacity: str = "cumulated_discharge_capacity_u_mAh_g"
    coulombic_efficiency: str = "coulombic_efficiency_u_percentage"
    cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency_u_percentage"
    coulombic_difference: str = "coulombic_difference_u_mAh_g"
    cumulated_coulombic_difference: str = "cumulated_coulombic_difference_u_mAh_g"
    discharge_capacity_loss: str = "discharge_capacity_loss_u_mAh_g"
    charge_capacity_loss: str = "charge_capacity_loss_u_mAh_g"
    cumulated_discharge_capacity_loss: str = "cumulated_discharge_capacity_loss_u_mAh_g"
    cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss_u_mAh_g"
    ir_discharge: str = "ir_discharge_u_Ohms"
    ir_charge: str = "ir_charge_u_Ohms"
    ocv_first_min: str = "ocv_first_min_u_V"
    ocv_second_min: str = "ocv_second_min_u_V"
    ocv_first_max: str = "ocv_first_max_u_V"
    ocv_second_max: str = "ocv_second_max_u_V"
    end_voltage_discharge: str = "end_voltage_discharge_u_V"
    end_voltage_charge: str = "end_voltage_charge_u_V"
    cumulated_ric_disconnect: str = "cumulated_ric_disconnect_u_none"
    cumulated_ric_sei: str = "cumulated_ric_sei_u_none"
    cumulated_ric: str = "cumulated_ric_u_none"
    normalized_cycle_index: str = "normalized_cycle_index"
    normalized_charge_capacity: str = "normalized_charge_capacity"
    normalized_discharge_capacity: str = "normalized_discharge_capacity"
    low_level: str = "low_level_u_percentage"
    high_level: str = "high_level_u_percentage"
    shifted_charge_capacity: str = "shifted_charge_capacity_u_mAh_g"
    shifted_discharge_capacity: str = "shifted_discharge_capacity_u_mAh_g"
    temperature_last: str = "temperature_last_u_C"
    temperature_mean: str = "temperature_mean_u_C"
    areal_charge_capacity: str = "areal_charge_capacity_u_mAh_cm2"
    areal_discharge_capacity: str = "areal_discharge_capacity_u_mAh_cm2"
    charge_c_rate: str = "charge_c_rate"
    discharge_c_rate: str = "discharge_c_rate"
    # pre_aux: str = "aux_"


@dataclass
class HeadersSummaryV7(BaseHeaders):
    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    test_name: str = "test_name"
    data_flag: str = "data_flag"
    channel_id: str = "channel_id"

    coulombic_efficiency: str = "coulombic_efficiency"
    cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency"

    discharge_capacity: str = "discharge_capacity_gravimetric"
    charge_capacity: str = "charge_capacity_gravimetric"
    cumulated_charge_capacity: str = "cumulated_charge_capacity_gravimetric"
    cumulated_discharge_capacity: str = "cumulated_discharge_capacity_gravimetric"

    coulombic_difference: str = "coulombic_difference_gravimetric"
    cumulated_coulombic_difference: str = "cumulated_coulombic_difference_gravimetric"
    discharge_capacity_loss: str = "discharge_capacity_loss_gravimetric"
    charge_capacity_loss: str = "charge_capacity_loss_gravimetric"
    cumulated_discharge_capacity_loss: str = "cumulated_discharge_capacity_loss_gravimetric"
    cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss_gravimetric"

    areal_charge_capacity: str = "charge_capacity_areal"
    areal_discharge_capacity: str = "discharge_capacity_areal"

    shifted_charge_capacity: str = "shifted_charge_capacity_gravimetric"
    shifted_discharge_capacity: str = "shifted_discharge_capacity_gravimetric"

    ir_discharge: str = "ir_discharge"
    ir_charge: str = "ir_charge"
    ocv_first_min: str = "ocv_first_min"
    ocv_second_min: str = "ocv_second_min"
    ocv_first_max: str = "ocv_first_max"
    ocv_second_max: str = "ocv_second_max"
    end_voltage_discharge: str = "end_voltage_discharge"
    end_voltage_charge: str = "end_voltage_charge"
    cumulated_ric_disconnect: str = "cumulated_ric_disconnect"
    cumulated_ric_sei: str = "cumulated_ric_sei"
    cumulated_ric: str = "cumulated_ric"
    normalized_cycle_index: str = "normalized_cycle_index"
    normalized_charge_capacity: str = "normalized_charge_capacity"
    normalized_discharge_capacity: str = "normalized_discharge_capacity"
    low_level: str = "low_level"
    high_level: str = "high_level"

    temperature_last: str = "temperature_last"
    temperature_mean: str = "temperature_mean"

    charge_c_rate: str = "charge_c_rate"
    discharge_c_rate: str = "discharge_c_rate"


@dataclass
class HeadersStepTableV7(BaseHeaders):
    test: str = "test"
    ustep: str = "ustep"
    cycle: str = "cycle"
    step: str = "step"
    test_time: str = "test_time"
    step_time: str = "step_time"
    sub_step: str = "sub_step"
    type: str = "type"
    sub_type: str = "sub_type"
    info: str = "info"
    voltage: str = "voltage"
    current: str = "current"
    charge: str = "charge"
    discharge: str = "discharge"
    point: str = "point"
    internal_resistance: str = "ir"
    internal_resistance_change: str = "ir_pct_change"
    rate_avr: str = "rate_avr"


@dataclass
class HeadersJournalV5(BaseHeaders):
    filename: str = "filenames"
    mass: str = "masses"
    total_mass: str = "total_masses"
    loading: str = "loadings"
    fixed: str = "fixed"
    label: str = "labels"
    cell_type: str = "cell_types"
    raw_file_names: str = "raw_file_names"
    cellpy_file_name: str = "cellpy_file_names"
    group: str = "groups"
    sub_group: str = "sub_groups"


@dataclass
class HeadersJournalV7(BaseHeaders):
    filename: str = "filename"
    mass: str = "mass"
    total_mass: str = "total_mass"
    loading: str = "loading"
    nom_cap: str = "nom_cap"
    experiment: str = "experiment"
    fixed: str = "fixed"
    label: str = "label"
    cell_type: str = "cell_type"
    instrument: str = "instrument"
    raw_file_names: str = "raw_file_names"
    cellpy_file_name: str = "cellpy_file_name"
    group: str = "group"
    sub_group: str = "sub_group"
    comment: str = "comment"
    argument: str = "argument"


summary_header_versions = {
    1: HeadersSummaryV5(),
    2: HeadersSummaryV5(),
    3: HeadersSummaryV5(),
    4: HeadersSummaryV5(),
    5: HeadersSummaryV5(),
    6: HeadersSummaryV6(),
    7: HeadersSummaryV7(),
    8: HeadersSummaryV7(),
}

raw_header_versions = {
    1: HeadersRawV4(),
    2: HeadersRawV4(),
    3: HeadersRawV4(),
    4: HeadersRawV4(),
    5: HeadersRawV5(),
    6: HeadersRawV6(),
    7: HeadersRawV7(),
    8: HeadersRawV7(),
}

steps_header_versions = {
    1: HeadersStepTableV7(),
    2: HeadersStepTableV7(),
    3: HeadersStepTableV7(),
    4: HeadersStepTableV7(),
    5: HeadersStepTableV7(),
    6: HeadersStepTableV7(),
    7: HeadersStepTableV7(),
    8: HeadersStepTableV7(),
}

journal_header_versions = {
    1: HeadersJournalV5(),
    2: HeadersJournalV5(),
    3: HeadersJournalV5(),
    4: HeadersJournalV5(),
    5: HeadersJournalV5(),
    6: HeadersJournalV7(),
    7: HeadersJournalV7(),
    8: HeadersJournalV7(),
}


headers_journal_v0 = HeadersJournalV5()


def rename_step_columns(
    steps: "externals.pandas.DataFrame",
    old_version: int,
    new_version: int = CELLPY_FILE_VERSION,
    **kwargs,
) -> "externals.pandas.DataFrame":
    logging.debug("renaming headers")
    old = summary_header_versions.get(old_version)
    new = summary_header_versions.get(new_version)
    steps = rename_columns(
        steps,
        old,
        new,
        **kwargs,
    )
    return steps


def rename_raw_columns(
    raw: "externals.pandas.DataFrame",
    old_version: int,
    new_version: int = CELLPY_FILE_VERSION,
    **kwargs,
) -> "externals.pandas.DataFrame":
    logging.debug("renaming headers")
    old = raw_header_versions.get(old_version)
    new = raw_header_versions.get(new_version)
    raw = rename_columns(
        raw,
        old,
        new,
        **kwargs,
    )
    return raw


def rename_summary_columns(
    summary: "externals.pandas.DataFrame",
    old_version: int,
    new_version: int = CELLPY_FILE_VERSION,
    **kwargs,
) -> "externals.pandas.DataFrame":
    """Rename the summary headers to new format.

    Args:
        summary: summary dataframe in old format.
        old_version: old format (cellpy_file_format (might use summary format number instead soon)).
        new_version: new format (cellpy_file_format (might use summary format number instead soon)).
        **kwargs:
            remove_missing_in_new (bool): remove the columns that are not defined in the new format.
            populate_missing_in_old (bool): add "new-format" missing columns (with np.NAN).

    Returns:
        summary (pandas.DataFrame) with column headers in the new format.
    """
    logging.debug("renaming headers")
    old = summary_header_versions.get(old_version)
    new = summary_header_versions.get(new_version)
    summary = rename_columns(
        summary,
        old,
        new,
        **kwargs,
    )
    return summary


def rename_fid_columns(
    fid_table: "externals.pandas.DataFrame",
    old_version: int,
    new_version: int = CELLPY_FILE_VERSION,
    **kwargs,
) -> "externals.pandas.DataFrame":
    logging.debug("renaming headers")
    logging.critical("RENAMING NOT IMPLEMENTED YET -> Please, create an issue on Github")
    return fid_table


def get_column_name_mapper(
    old_columns: BaseHeaders, new_columns: BaseHeaders
) -> Tuple[Dict[str, str], List[str], List[str]]:
    """Create a dictionary that maps old column names to new column names.

    Args:
        old_columns: The BaseHeaders for the old format.
        new_columns: The BaseHeaders for the new format.

    Returns:
        Translation dictionary, list of missing keys in new format, list of missing keys in old format.
    """
    translations = {}
    missing_in_old = []
    old_columns_keys = old_columns.keys()
    new_columns_keys = new_columns.keys()
    for key in new_columns_keys:
        if old_column := old_columns.get(key):
            translations[old_column] = new_columns.get(key)
            old_columns_keys.remove(key)
        else:
            missing_in_old.append(key)

    missing_in_new = old_columns_keys
    return translations, missing_in_new, missing_in_old


def rename_columns(
    df: "externals.pandas.DataFrame",
    old: BaseHeaders,
    new: BaseHeaders,
    remove_missing_in_new: bool = False,
    populate_missing_in_old: bool = True,
) -> "externals.pandas.DataFrame":
    """Rename the column headers of a cells dataframe.

    Usage:
        >>>  old_format_headers = HeadersSummaryV6()
        >>>  new_format_headers = HeadersSummaryV7()
        >>>  df_new_format = rename_columns(df_old_format, old_format_headers, new_format_headers)

    Args:
        df: The dataframe.
        old: The BaseHeaders for the old format.
        new: The BaseHeaders for the new format.
        remove_missing_in_new: remove the columns that are not defined in the new format.
        populate_missing_in_old: add "new-format" missing columns (with np.NAN).

    Returns:
        Dataframe with updated columns
    """
    col_name_mapper, missing_in_new, missing_in_old = get_column_name_mapper(old, new)

    if remove_missing_in_new:
        for col in missing_in_new:
            df = df.drop(col, axis=1)

    if populate_missing_in_old:
        for col in missing_in_old:
            df[col] = externals.numpy.nan

    return df.rename(columns=col_name_mapper)


def _create_dummy_summary(columns):
    df = externals.pandas.DataFrame(
        data=externals.numpy.random.rand(5, len(columns) - 1), index=range(1, 6), columns=columns[1:]
    )
    df.index.name = columns[0]
    return df


# Use this as inspiration if you want to implement translation of step table headers:
# HEADERS_KEYS_STEP_TABLE_EXTENDED = [
#     "point",
#     "test_time",
#     "step_time",
#     "current",
#     "voltage",
#     "charge",
#     "discharge",
#     "internal_resistance",
# ]
# HEADERS_STEP_TABLE_EXTENSIONS = ["min", "max", "avr", "first", "last", "delta", "std"]
#
#
# headers_step_table_v5["test"] = "test"
# headers_step_table_v5["ustep"] = "ustep"
# headers_step_table_v5["cycle"] = "cycle"
# headers_step_table_v5["step"] = "step"
# headers_step_table_v5["test_time"] = "test_time"
# headers_step_table_v5["step_time"] = "step_time"
# headers_step_table_v5["sub_step"] = "sub_step"
# headers_step_table_v5["type"] = "type"
# headers_step_table_v5["sub_type"] = "sub_type"
# headers_step_table_v5["info"] = "info"
# headers_step_table_v5["voltage"] = "voltage"
# headers_step_table_v5["current"] = "current"
# headers_step_table_v5["charge"] = "charge"
# headers_step_table_v5["discharge"] = "discharge"
# headers_step_table_v5["point"] = "point"
# headers_step_table_v5["internal_resistance"] = "ir"
# headers_step_table_v5["internal_resistance_change"] = "ir_pct_change"
# headers_step_table_v5["rate_avr"] = "rate_avr"

# def translate_headers(data_sets, cellpy_file_version):
#     # this works for upgrading to versions 6,
#     # remark that the extensions for the step table is hard-coded
#     logging.debug(f"translate headers from v{cellpy_file_version}")
#
#     summary_rename_dict = {
#         headers_summary_v5[key]: HEADERS_SUMMARY[key]
#         for key in HEADERS_SUMMARY
#         if key in headers_summary_v5
#     }
#
#     steps_rename_dict = {
#         headers_step_table_v5[key]: HEADERS_STEP_TABLE[key]
#         for key in HEADERS_STEP_TABLE
#         if key in headers_step_table_v5
#     }
#
#     steps_rename_dict_extensions = {}
#     for key in HEADERS_KEYS_STEP_TABLE_EXTENDED:
#         for extension in HEADERS_STEP_TABLE_EXTENSIONS:
#             old = "_".join([HEADERS_STEP_TABLE[key], extension])
#             new = "_".join([headers_step_table_v5[key], extension])
#             steps_rename_dict_extensions[old] = new
#
#     raw_rename_dict = {
#         headers_normal_v5[key]: HEADERS_NORMAL[key] for key in HEADERS_NORMAL
#     }
#
#     summary_index_name = HEADERS_SUMMARY["cycle_index"]
#     raw_index_name = HEADERS_NORMAL["data_point_txt"]
#
#     # from pprint import pprint
#     # pprint(summary_rename_dict)
#     # pprint(steps_rename_dict)
#     # pprint(steps_rename_dict_extensions)
#     # pprint(raw_rename_dict)
#
#     new_data_sets = []
#     for data_set in data_sets:
#         data_set.summary.rename(columns=summary_rename_dict, inplace=True)
#         data_set.raw.rename(columns=raw_rename_dict, inplace=True)
#         data_set.steps.rename(columns=steps_rename_dict, inplace=True)
#         data_set.steps.rename(columns=steps_rename_dict_extensions, inplace=True)
#
#         # we also need to update the index-name
#         data_set.summary.index.name = summary_index_name
#         data_set.raw.index.name = raw_index_name
#
#         new_data_sets.append(data_set)
#
#         # pprint(data_set.summary.columns)
#         # pprint(data_set.steps.columns)
#         # pprint(data_set.raw.columns)
#     # check(new_data_sets)
#     return new_data_sets


def _check():
    old = HeadersSummaryV6()
    new = HeadersSummaryV7()
    df = _create_dummy_summary(columns=old.keys())
    remove_missing_in_new = False
    populate_missing_in_old = True

    df = rename_columns(
        df,
        old,
        new,
        remove_missing_in_new=remove_missing_in_new,
        populate_missing_in_old=populate_missing_in_old,
    )
    print(df.head())


if __name__ == "__main__":
    _check()
