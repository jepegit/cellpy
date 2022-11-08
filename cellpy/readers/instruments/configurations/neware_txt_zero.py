file_info = {"raw_extension": "csv"}

normal_headers_renaming_dict = {
    "data_point_txt": f"DataPoint",
    "cycle_index_txt": f"Cycle Index",
    "step_index_txt": f"Step Index",
    "current_txt": f"Current(A)",
    "voltage_txt": f"Voltage(V)",
    "charge_capacity_txt": f"Chg. Cap.(Ah)",
    "charge_energy_txt": f"Chg. Energy(Wh)",
    "discharge_capacity_txt": f"DChg. Cap.(Ah)",
    "discharge_energy_txt": f"DChg. Energy(Wh)",
    "datetime_txt": f"Date",
    "step_time_txt": f"Time",
    "dq_dv_txt": f"dQ/dV(mAh/V)",
    "internal_resistance_txt": f"Contact resistance(mO)",
    "power_txt": f"Power(W)",
    "test_time_txt": f"Cumulative Time",
}

states = {
    "column_name": "Step Type",
    "charge_keys": ["CC Chg"],
    "discharge_keys": ["CC DChg"],
    "rest_keys": ["Rest"],
}

raw_units = {"current": "A", "charge": "Ah", "mass": "g", "voltage": "V"}

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
    "skiprows": 0,  # will not be used since auto is on
    "sep": None,  # comma for UiO at the moment, but using auto instead
    "header": 0,  # 0 for other file
    "encoding": "ISO-8859-1",  # will not be used since auto is on
    "decimal": ".",
    "thousands": None,
}


post_processors = {
    "split_capacity": False,
    "split_current": False,
    "cumulate_capacity_within_cycle": True,
    "set_index": True,
    "rename_headers": True,
    "set_cycle_number_not_zero": False,
    "convert_date_time_to_datetime": True,
    "convert_step_time_to_timedelta": True,
    "convert_test_time_to_timedelta": True,
}
