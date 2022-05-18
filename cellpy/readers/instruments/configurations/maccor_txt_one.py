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

file_info = {
    "raw_extension": "txt"
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
    "TestTime",
    "Rec#",
    "Cyc#",
    "Step",
    "StepTime",
    "Amp-hr",
    "Watt-hr",
    "Amps",
    "Volts",
    "State",
    "ES",
    "DPt Time",
    "ACImp/Ohms",
    "DCIR/Ohms",
]

states = {
    "column_name": "State",
    "charge_keys": ["C"],
    "discharge_keys": ["D"],
    "rest_keys": ["R"],
}

raw_units = {"current": 1.0, "charge": 1.0, "mass": 0.001}

raw_limits = {
    "current_hard": 0.000_000_000_000_1,
    "current_soft": 0.000_01,
    "stable_current_hard": 2.0,
    "stable_current_soft": 4.0,
    "stable_voltage_hard": 2.0,
    "stable_voltage_soft": 4.0,
    "stable_charge_hard": 0.001,
    "stable_charge_soft": 5.0,
    "ir_change": 0.00001,
}

formatters = {
    "skiprows": 3,  # 12 for other file
    "sep": "\t",
    "header": 0,  # 0 for other file
    "encoding": "ISO-8859-1",  # options: "ISO-8859-1", "utf-8", "cp1252"
    "decimal": ".",
    "thousands": None,
}


post_processors = {
    "split_capacity": True,
    "split_current": True,
    "set_index": True,
    "rename_headers": True,
    "set_cycle_number_not_zero": True,
    "convert_date_time_to_datetime": True,
    # "convert_step_time_to_timedelta": True,
    # "convert_test_time_to_timedelta": True,
}
