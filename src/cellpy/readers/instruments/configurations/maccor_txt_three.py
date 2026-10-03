"""Configuration for tab-delimited Maccor txt files with two comment rows (used by WMG in the SIMBA project)."""

# currently skips the comment rows instead of parsing them (change this by modifying the formatters
# and add preprocessing step for parsing them)

file_info = {"raw_extension": "txt"}

# not used yet:
unit_labels = {
    "resistance": "Ohms",
    "time": "s",
    "current": "mA",
    "voltage": "mV",
    "power": "mW",
    "capacity": "mAh",
    "energy": "mWh",
    "temperature": "C",
}

normal_headers_renaming_dict = {
    "data_point_txt": "Rec#",
    "cycle_index_txt": "Cyc#",
    "step_index_txt": "Step",
    "test_time_txt": "TestTime",
    "step_time_txt": "StepTime",
    "charge_capacity_txt": "mAmp-hr",
    "charge_energy_txt": "mWatt-hr",
    "current_txt": "mAmps",
    "voltage_txt": "Volts",
    "datetime_txt": "DPt Time",
}

raw_units = {"current": "mA", "charge": "mAh", "mass": "g", "voltage": "mV"}

states = {
    "column_name": "State",
    "charge_keys": ["C"],
    "discharge_keys": ["D"],
    "rest_keys": ["R"],
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
    "skiprows": 2,
    "sep": "\t",
    "header": 0,
    "encoding": "ISO-8859-1",  # options: "ISO-8859-1", "utf-8", "cp1252"
    "decimal": ",",
    "thousands": None,
}

pre_processors = {
    "remove_empty_lines": True,
}

post_processors = {
    "split_capacity": True,
    "split_current": True,
    "set_index": True,
    "rename_headers": True,
    "set_cycle_number_not_zero": True,
    "remove_last_if_bad": True,
    "convert_date_time_to_datetime": True,
    "convert_step_time_to_timedelta": True,
    "convert_test_time_to_timedelta": True,
}
