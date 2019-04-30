"""Internal settings and definitions and functions for getting them."""

import box

cellpy_units = dict()
cellpy_limits = dict()
headers_normal = dict()
headers_summary = dict()
headers_step_table = dict()

################################ cellpy attributes##############################

cellpy_attributes = [
    "mass",
    "channel_index",
    "channel_number",
    "creator",
    "schedule_file_name",
    "start_datetime",
    "test_ID",
    "test_no",
    "name",
    "nom_cap",
]

################################ cellpy units ##################################

cellpy_units["current"] = 0.001  # mA
cellpy_units["charge"] = 0.001  # Ah
cellpy_units["mass"] = 0.001  # mg (used for input of mass)
cellpy_units["specific"] = 1.0  # g (used for calc. of e.g. spec. capacity)
cellpy_units["voltage"] = 1.0  # V (not implemented yet)

################################ cellpy limits #################################

cellpy_limits["current_hard"] = 0.0000000000001
cellpy_limits["current_soft"] = 0.00001
cellpy_limits["stable_current_hard"] = 2.0
cellpy_limits["stable_current_soft"] = 4.0
cellpy_limits["stable_voltage_hard"] = 2.0
cellpy_limits["stable_voltage_soft"] = 4.0
cellpy_limits["stable_charge_hard"] = 0.9
cellpy_limits["stable_charge_soft"] = 5.0
cellpy_limits["ir_change"] = 0.00001

######################## headers for out-files #################################

########################### Summary ############################################

# 08.12.2016: added temperature_last, temperature_mean, aux_

headers_summary["discharge_capacity"] = "Discharge_Capacity(mAh/g)"
headers_summary["charge_capacity"] = "Charge_Capacity(mAh/g)"
headers_summary["cumulated_charge_capacity"] = \
    "Cumulated_Charge_Capacity(mAh/g)"
headers_summary["cumulated_discharge_capacity"] = \
    "Cumulated_Discharge_Capacity(mAh/g)"
headers_summary["coulombic_efficiency"] = \
    "Coulombic_Efficiency(percentage)"
headers_summary["cumulated_coulombic_efficiency"] = \
    "Cumulated_Coulombic_Efficiency(percentage)"
headers_summary["coulombic_difference"] = "Coulombic_Difference(mAh/g)"
headers_summary["cumulated_coulombic_difference"] = \
    "Cumulated_Coulombic_Difference(mAh/g)"
headers_summary["discharge_capacity_loss"] = \
    "Discharge_Capacity_Loss(mAh/g)"
headers_summary["charge_capacity_loss"] = "Charge_Capacity_Loss(mAh/g)"
headers_summary["cumulated_discharge_capacity_loss"] = \
    "Cumulated_Discharge_Capacity_Loss(mAh/g)"
headers_summary["cumulated_charge_capacity_loss"] = \
    "Cumulated_Charge_Capacity_Loss(mAh/g)"
headers_summary["ir_discharge"] = "IR_Discharge(Ohms)"
headers_summary["ir_charge"] = "IR_Charge(Ohms)"
headers_summary["ocv_first_min"] = "OCV_First_Min(V)"
headers_summary["ocv_second_min"] = "OCV_Second_Min(V)"
headers_summary["ocv_first_max"] = "OCV_First_Max(V)"
headers_summary["ocv_second_max"] = "OCV_Second_Max(V)"
headers_summary["date_time_txt"] = "Date_Time_Txt(str)"
headers_summary["end_voltage_discharge"] = "End_Voltage_Discharge(V)"
headers_summary["end_voltage_charge"] = "End_Voltage_Charge(V)"
headers_summary["cumulated_ric_disconnect"] = "RIC_Disconnect(none)"
headers_summary["cumulated_ric_sei"] = "RIC_SEI(none)"
headers_summary["cumulated_ric"] = "RIC(none)"
# Sum of irreversible capacity:
headers_summary["low_level"] = "Low_Level(percentage)"
# SEI loss:
headers_summary["high_level"] = "High_Level(percentage)"
headers_summary["shifted_charge_capacity"] = \
    "Charge_Endpoint_Slippage(mAh/g)"
headers_summary["shifted_discharge_capacity"] = \
    "Discharge_Endpoint_Slippage(mAh/g)"
headers_summary["temperature_last"] = "Last_Temperature(C)"
headers_summary["temperature_mean"] = "Average_Temperature(C)"
headers_summary["pre_aux"] = "Aux_"

headers_summary = box.Box(headers_summary)

############################# Normal ###########################################

headers_normal['aci_phase_angle_txt'] = 'ACI_Phase_Angle'
headers_normal['ref_aci_phase_angle_txt'] = 'Reference_ACI_Phase_Angle'

headers_normal['ac_impedance_txt'] = 'AC_Impedance'
headers_normal['ref_ac_impedance_txt'] = 'Reference_AC_Impedance'  # new

headers_normal['charge_capacity_txt'] = 'Charge_Capacity'
headers_normal['charge_energy_txt'] = 'Charge_Energy'
headers_normal['current_txt'] = 'Current'
headers_normal['cycle_index_txt'] = 'Cycle_Index'
headers_normal['data_point_txt'] = 'Data_Point'
headers_normal['datetime_txt'] = 'DateTime'
headers_normal['discharge_capacity_txt'] = 'Discharge_Capacity'
headers_normal['discharge_energy_txt'] = 'Discharge_Energy'
headers_normal['internal_resistance_txt'] = 'Internal_Resistance'

headers_normal['is_fc_data_txt'] = 'Is_FC_Data'
headers_normal['step_index_txt'] = 'Step_Index'
headers_normal['sub_step_index_txt'] = 'Sub_Step_Index'  # new

headers_normal['step_time_txt'] = 'Step_Time'
headers_normal['sub_step_time_txt'] = 'Sub_Step_Time'  # new

headers_normal['test_id_txt'] = 'Test_ID'
headers_normal['test_time_txt'] = 'Test_Time'

headers_normal['voltage_txt'] = 'Voltage'
headers_normal['ref_voltage_txt'] = 'Reference_Voltage'  # new

headers_normal['dv_dt_txt'] = 'dV/dt'
headers_normal['frequency_txt'] = 'Frequency'  # new
headers_normal['amplitude_txt'] = 'Amplitude'  # new

headers_normal = box.Box(headers_normal)

############################### step table #####################################

# 08.12.2016: added sub_step, sub_type, and pre_time

headers_step_table["test"] = "test"
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


# #fix this (old)
# headers_step_table["pre_current"] = "I_"
# headers_step_table["pre_voltage"] = "V_"
# headers_step_table["pre_charge"] = "Charge_"
# headers_step_table["pre_discharge"] = "Discharge_"
# headers_step_table["pre_point"] = "datapoint_"
# headers_step_table["pre_time"] = "time_"
# headers_step_table["post_mean"] = "avr"
# headers_step_table["post_std"] = "std"
# headers_step_table["post_max"] = "max"
# headers_step_table["post_min"] = "min"
# headers_step_table["post_start"] = "start"  # first
# headers_step_table["post_end"] = "end"  # last
# headers_step_table["post_delta"] = "delta"
# headers_step_table["post_rate"] = "rate"  # does not exist anymore


headers_step_table = box.Box(headers_step_table)


def get_headers_summary():
    """Returns a dictionary containing the header-strings for the summary
    (used as column headers for the summary pandas DataFrames)"""
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
