"""Internal settings and definitions and functions for getting them."""

import collections


class HeaderDict(collections.UserDict):
    """Sub-classing dict to allow for tab-completion."""

    def __setitem__(self, key, value):
        if key == "data":
            raise KeyError("protected key")
        super().__setitem__(key, value)
        self.__dict__[key] = value


cellpy_units = HeaderDict()
cellpy_limits = HeaderDict()
headers_normal = HeaderDict()
headers_summary = HeaderDict()
headers_step_table = HeaderDict()
headers_journal = HeaderDict()

# cellpy attributes that should be loaded from cellpy-files:

ATTRS_CELLPYFILE = [
    "mass",
    "channel_index",
    "channel_number",
    "creator",
    "schedule_file_name",
    "start_datetime",
    "test_ID",
    "cell_no",
    "name",
    "nom_cap",
    "material",
    "item_ID",
    "active_electrode_area",
    "active_electrode_thickness",
    "electrolyte_type",
    "electrolyte_volume",
    "active_electrode_type",
    "counter_electrode_type",
    "reference_electrode_type",
    "experiment_type",
    "cell_type",
    "active_electrode_current_collector",
    "reference_electrode_current_collector",
    "comment",
]

# Attributes that should be copied when duplicating cellpy objects:

# current attributes for the cellpy.cellpydata objects
ATTRS_CELLPYDATA = [
    "auto_dirs",
    "capacity_modifiers",
    "cellpy_datadir",
    "cycle_mode",
    "daniel_number",
    "ensure_step_table",
    "file_names",
    "filestatuschecker",
    "force_all",
    "force_step_table_creation",
    "forced_errors",
    "limit_loaded_cycles",
    "load_only_summary",
    "minimum_selection",
    "name",
    "number_of_datasets",
    "profile",
    "raw_datadir",
    "raw_limits",
    "raw_units",
    "select_minimal",
    "selected_cell_number",
    "selected_scans",
    "sep",
    "status_datasets",
    "summary_exists",
    "table_names",
    "tester",
]

# current attributes used for the cellpy.cell objects
ATTRS_DATASET = [
    "cellpy_file_version",
    "channel_index",
    "channel_number",
    "charge_steps",
    "creator",
    # "data",
    "discharge_steps",
    "file_errors",
    "ir_steps",
    "item_ID",
    "loaded_from",
    "mass",
    "mass_given",
    "material",
    "merged",
    "name",
    "no_cycles",
    "nom_cap",
    "ocv_steps",
    "raw_data_files_length",
    "raw_limits",
    "raw_units",
    "schedule_file_name",
    "start_datetime",
    # "summary",
    "test_ID",
    "cell_no",
    "tot_mass",
]

ATTRS_DATASET_DEEP = ["raw_data_files"]

# cellpy units:

cellpy_units["current"] = 0.001  # mA
cellpy_units["charge"] = 0.001  # Ah
cellpy_units["mass"] = 0.001  # mg (used for input of mass)
cellpy_units["specific"] = 1.0  # g (used for calc. of e.g. spec. capacity)
cellpy_units["voltage"] = 1.0  # V (not implemented yet)


# cellpy limits:

cellpy_limits["current_hard"] = 0.0000000000001
cellpy_limits["current_soft"] = 0.00001
cellpy_limits["stable_current_hard"] = 2.0
cellpy_limits["stable_current_soft"] = 4.0
cellpy_limits["stable_voltage_hard"] = 2.0
cellpy_limits["stable_voltage_soft"] = 4.0
cellpy_limits["stable_charge_hard"] = 0.9
cellpy_limits["stable_charge_soft"] = 5.0
cellpy_limits["ir_change"] = 0.00001


# headers for out-files:

# 01.05.2020: renamed the column names to the form cycle_index, discharge_capacity_u_mAh_g, etc.

# - normal (data) -

headers_normal["aci_phase_angle_txt"] = "aci_phase_angle"
headers_normal["ref_aci_phase_angle_txt"] = "ref_aci_phase_angle"
headers_normal["ac_impedance_txt"] = "ac_impedance"
headers_normal["ref_ac_impedance_txt"] = "ref_ac_impedance"  # new
headers_normal["charge_capacity_txt"] = "charge_capacity"
headers_normal["charge_energy_txt"] = "charge_energy"
headers_normal["current_txt"] = "current"
headers_normal["cycle_index_txt"] = "cycle_index"
headers_normal["data_point_txt"] = "data_point"
headers_normal["datetime_txt"] = "date_time"
headers_normal["discharge_capacity_txt"] = "discharge_capacity"
headers_normal["discharge_energy_txt"] = "discharge_energy"
headers_normal["internal_resistance_txt"] = "internal_resistance"
headers_normal["is_fc_data_txt"] = "is_fc_data"
headers_normal["step_index_txt"] = "step_index"
headers_normal["sub_step_index_txt"] = "sub_step_index"  # new
headers_normal["step_time_txt"] = "step_time"
headers_normal["sub_step_time_txt"] = "sub_step_time"  # new
headers_normal["test_id_txt"] = "test_id"
headers_normal["test_time_txt"] = "test_time"
headers_normal["voltage_txt"] = "voltage"
headers_normal["ref_voltage_txt"] = "reference_voltage"  # new
headers_normal["dv_dt_txt"] = "dv_dt"
headers_normal["frequency_txt"] = "frequency"  # new
headers_normal["amplitude_txt"] = "amplitude"  # new

# - summary -

# 08.12.2016: added temperature_last, temperature_mean, aux_
headers_summary["cycle_index"] = headers_normal["cycle_index_txt"]
headers_summary["data_point"] = headers_normal["data_point_txt"]
headers_summary["test_time"] = headers_normal["test_time_txt"]
headers_summary["datetime"] = headers_normal["datetime_txt"]
headers_summary["discharge_capacity_raw"] = headers_normal["discharge_capacity_txt"]
headers_summary["charge_capacity_raw"] = headers_normal["charge_capacity_txt"]

headers_summary["discharge_capacity"] = "discharge_capacity_u_mAh_g"
headers_summary["charge_capacity"] = "charge_capacity_u_mAh_g"
headers_summary["cumulated_charge_capacity"] = "cumulated_charge_capacity_u_mAh_g"
headers_summary["cumulated_discharge_capacity"] = "cumulated_discharge_capacity_u_mAh_g"
headers_summary["coulombic_efficiency"] = "coulombic_efficiency_u_percentage"
headers_summary[
    "cumulated_coulombic_efficiency"
] = "cumulated_coulombic_efficiency_u_percentage"
headers_summary["coulombic_difference"] = "coulombic_difference_u_mAh_g"
headers_summary[
    "cumulated_coulombic_difference"
] = "cumulated_coulombic_difference_u_mAh_g"
headers_summary["discharge_capacity_loss"] = "discharge_capacity_loss_u_mAh_g"
headers_summary["charge_capacity_loss"] = "charge_capacity_loss_u_mAh_g"
headers_summary[
    "cumulated_discharge_capacity_loss"
] = "cumulated_discharge_capacity_loss_u_mAh_g"
headers_summary[
    "cumulated_charge_capacity_loss"
] = "cumulated_charge_capacity_loss_u_mAh_g"
headers_summary["ir_discharge"] = "ir_discharge_u_Ohms"
headers_summary["ir_charge"] = "ir_charge_u_Ohms"
headers_summary["ocv_first_min"] = "ocv_first_min_u_V"
headers_summary["ocv_second_min"] = "ocv_second_min_u_V"
headers_summary["ocv_first_max"] = "ocv_first_max_u_V"
headers_summary["ocv_second_max"] = "ocv_second_max_u_V"
headers_summary["end_voltage_discharge"] = "end_voltage_discharge_u_V"
headers_summary["end_voltage_charge"] = "end_voltage_charge_u_V"
headers_summary["cumulated_ric_disconnect"] = "cumulated_ric_disconnect_u_none"
headers_summary["cumulated_ric_sei"] = "cumulated_ric_sei_u_none"
headers_summary["cumulated_ric"] = "cumulated_ric_u_none"

headers_summary["normalized_cycle_index"] = "normalized_cycle_index"
headers_summary["normalized_charge_capacity"] = "normalized_charge_capacity"
headers_summary["normalized_discharge_capacity"] = "normalized_discharge_capacity"

# Sum of irreversible capacity:
headers_summary["low_level"] = "low_level_u_percentage"
# SEI loss:
headers_summary["high_level"] = "high_level_u_percentage"
# Shifted capacities:
headers_summary["shifted_charge_capacity"] = "shifted_charge_capacity_u_mAh_g"
headers_summary["shifted_discharge_capacity"] = "shifted_discharge_capacity_u_mAh_g"
# Other
headers_summary["temperature_last"] = "temperature_last_u_C"
headers_summary["temperature_mean"] = "temperature_mean_u_C"
headers_summary["areal_charge_capacity"] = "areal_charge_capacity_u_mAh_cm2"
headers_summary["areal_discharge_capacity"] = "areal_discharge_capacity_u_mAh_cm2"
headers_summary["charge_c_rate"] = "charge_c_rate"
headers_summary["discharge_c_rate"] = "discharge_c_rate"
headers_summary["pre_aux"] = "aux_"

# - step table -

# 08.12.2016: added sub_step, sub_type, and pre_time

headers_step_table["test"] = "test"
headers_step_table["ustep"] = "ustep"
headers_step_table["cycle"] = "cycle"
headers_step_table["step"] = "step"
headers_step_table["test_time"] = "test_time"
headers_step_table["step_time"] = "step_time"
headers_step_table["sub_step"] = "sub_step"
headers_step_table["type"] = "type"
headers_step_table["sub_type"] = "sub_type"
headers_step_table["info"] = "info"
headers_step_table["voltage"] = "voltage"
headers_step_table["current"] = "current"
headers_step_table["charge"] = "charge"
headers_step_table["discharge"] = "discharge"
headers_step_table["point"] = "point"
headers_step_table["internal_resistance"] = "ir"
headers_step_table["internal_resistance_change"] = "ir_pct_change"
headers_step_table["rate_avr"] = "rate_avr"

# 01.05.2020: added fix column names and renamed to singular form.
# 08.07.2020: added nominal capacity, experiment type and comment.
headers_journal["filename"] = "filename"
headers_journal["mass"] = "mass"
headers_journal["total_mass"] = "total_mass"
headers_journal["loading"] = "loading"
headers_journal["nom_cap"] = "nom_cap"
headers_journal["experiment"] = "experiment"
headers_journal["fixed"] = "fixed"
headers_journal["label"] = "label"
headers_journal["cell_type"] = "cell_type"
headers_journal["raw_file_names"] = "raw_file_names"
headers_journal["cellpy_file_name"] = "cellpy_file_name"
headers_journal["group"] = "group"
headers_journal["sub_group"] = "sub_group"
headers_journal["comment"] = "comment"


def get_headers_summary():
    """Returns a dictionary containing the header-strings for the summary
    (used as column headers for the summary pandas DataFrames)"""
    # maybe I can do some tricks in here so that tab completion works?
    # ctrl + space works
    return headers_summary


def get_cellpy_units():
    """Returns a dictionary with units"""
    return cellpy_units


def get_headers_normal():
    """Returns a dictionary containing the header-strings for the normal data
        (used as column headers for the main data pandas DataFrames)"""
    return headers_normal


def get_headers_step_table():
    """Returns a dictionary containing the header-strings for the steps table
        (used as column headers for the steps pandas DataFrames)"""
    return headers_step_table


def get_headers_journal():
    """Returns a dictionary containing the header-strings for the journal (batch)
            (used as column headers for the journal pandas DataFrames)"""
    return headers_journal
