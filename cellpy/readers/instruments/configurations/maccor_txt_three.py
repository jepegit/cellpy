unit_labels = {
    "resistance": "Ohms",
    "time": "s",
    "current": "Amps",
    "voltage": "Volts",
    "power": "Watt-hr",
    "capacity": "Amp-hr",
    "energy": "Wh",
    "temperature": "C",
}

prefixes = {
    "G": 1000_000_000,
    "M": 1000_000,
    "k": 1000.0,
    "h": 100.0,
    "d": 10.0,
    "c": 0.01,
    "m": 0.001,
    "micro": 0.000_001,
    "n": 0.000_000_001,
}

normal_headers_renaming_dict = {
    "data_point_txt": f"Rec#",
    "datetime_txt": f"DPt Time",
    "test_time_txt": f"TestTime",
    "step_time_txt": f"StepTime",
    "cycle_index_txt": f"Cyc#",
    "step_index_txt": f"Step",
}


states = {
    "column_name": "State",
    "charge_keys": ["C"],
    "discharge_keys": ["D"],
    "rest_keys": ["R"],
}

raw_units = {
    "voltage": 0.001,
}

# raw_limits = {
#     "current_hard": 0.000_000_000_000_1,
#     "current_soft": 0.000_01,
#     "stable_current_hard": 2.0,
#     "stable_current_soft": 4.0,
#     "stable_voltage_hard": 2.0,
#     "stable_voltage_soft": 4.0,
#     "stable_charge_hard": 0.001,
#     "stable_charge_soft": 5.0,
#     "ir_change": 0.00001,
# }

formatters = {
    "skiprows": 3,  # 12 for other file
    "sep": "\t",
    "header": 0,  # 0 for other file
    "encoding": "ISO-8859-1",  # options: "ISO-8859-1", "utf-8", "cp1252"
    "decimal": ".",
    "thousands": ",",
}

pre_processors = {}

post_processors = {
    "get_column_names": True,
    "split_capacity": True,
    "split_current": False,
    "set_index": True,
    "rename_headers": True,
    "set_cycle_number_not_zero": True,
    "convert_date_time_to_datetime": True,
    "convert_step_time_to_timedelta": True,
    "convert_test_time_to_timedelta": True,
    "convert_units": True,
    "select_columns_to_keep": True,
}
