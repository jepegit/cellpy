file_info = {"raw_extension": "csv"}

raw_units = {
    "current": "mA",
    "charge": "mAh",
    "mass": "g",
    "voltage": "V",
    "energy": "mWh",
    "power": "mW",
    "resistance": "mOhm",
}

unit_labels = {
    "current": "mA",
    "charge": "mAh",
    "mass": "g",
    "voltage": "V",
    "energy": "mWh",
    "power": "mW",
    "resistance": "mO",
}

normal_headers_renaming_dict = {
    "data_point_txt": "DataPoint",
    "cycle_index_txt": "Cycle Index",
    "step_index_txt": "Step Index",
    "current_txt": "Current({{ current }})",
    "voltage_txt": "Voltage({{ voltage }})",
    "charge_capacity_txt": "Chg. Cap.({{ charge }})",
    "charge_energy_txt": "Chg. Energy({{ energy }})",
    "discharge_capacity_txt": "DChg. Cap.({{ charge }})",
    "discharge_energy_txt": "DChg. Energy({{ energy }})",
    "datetime_txt": "Date",
    "step_time_txt": "Time",
    "dq_dv_txt": "dQ/dV({{ charge }}/{{ voltage }})",
    "internal_resistance_txt": "Contact resistance({{ resistance }})",
    "power_txt": "Power({{ power }})",
    "test_time_txt": "Total Time",
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
    "sep": None,  # comma for UiO at the moment, but using auto instead
    "header": 0,  # will not be used since auto is on
    "encoding": "ISO-8859-1",  # will not be used since auto is on
    "decimal": ".",
    "thousands": None,
}

post_processors = {
    "update_headers_with_units": True,
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
