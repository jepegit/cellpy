file_info = {"raw_extension": "csv"}

raw_units = {
    "current": "A",
    "charge": "Ah",
    "mass": "g",
    "voltage": "V",
    "energy": "Wh",
    "power": "W",
    "resistance": "mOhm",
}

normal_headers_renaming_dict = {
    "data_point_txt": f"DataPoint",
    "cycle_index_txt": f"Cycle Index",
    "step_index_txt": f"Step Index",
    "current_txt": f"Current({raw_units['current']})",
    "voltage_txt": f"Voltage({raw_units['voltage']})",
    "charge_capacity_txt": f"Chg. Cap.({raw_units['charge']})",
    "charge_energy_txt": f"Chg. Energy({raw_units['energy']})",
    "discharge_capacity_txt": f"DChg. Cap.({raw_units['charge']})",
    "discharge_energy_txt": f"DChg. Energy({raw_units['energy']})",
    "datetime_txt": f"Date",
    "step_time_txt": f"Time",
    "dq_dv_txt": f"dQ/dV({raw_units['charge']}/{raw_units['voltage']})",
    "internal_resistance_txt": f"Contact resistance(mO)",
    "power_txt": f"Power({raw_units['power']})",
    "test_time_txt": f"Cumulative Time",
}

states = {
    "column_name": "Step Type",
    "charge_keys": ["CC Chg"],
    "discharge_keys": ["CC DChg"],
    "rest_keys": ["Rest"],
}


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
    "sep": None,  # will not be used since auto is on
    "header": 0,  # will not be used since auto is on
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
