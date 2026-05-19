file_info = {"raw_extension": "csv"}

raw_units = {
    "current": "A",
    "charge": "Ah",
    "mass": "g",
    "voltage": "V",
    "energy": "Wh",
    "power": "W",
    "resistance": "Ohm",
}

normal_headers_renaming_dict = {
    "test_time_txt": "Test Time / h",
    "current_txt": "Current / A",
    "voltage_txt": "Voltage / V",
    "step_index_txt": "Step Index / 1",
    "cycle_index_txt": "Cycle Count / 1",
    "charge_capacity_txt": "Charge Capacity / Ah",
    "discharge_capacity_txt": "Discharge Capacity / Ah",
}

states = {
    "column_name": "Step Type / 1",
    "charge_keys": ["charge"],
    "discharge_keys": ["discharge"],
    "rest_keys": ["rest"],
}

raw_limits = {
    # TODO: From neware documentation, review the limits and their values for this specific instrument
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
    "skiprows": 0,
    "sep": ",",
    "header": 0,
    "encoding": "utf-8",
    "decimal": ".",
    "thousands": None,
}

post_processors = {
    # TODO: review the post-processing steps and their order
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
