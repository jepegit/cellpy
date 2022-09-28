# Works for data from KIT (SIMBA project) with ',' as decimal and dropping bad last rows.

unit_labels = {
    "resistance": "Ohms",
    "time": "s",
    "current": "A",
    "voltage": "V",
    "power": "W",
    "capacity": "Ah",
    "energy": "Wh",
    "temperature": "C",
}

file_info = {"raw_extension": "txt"}

normal_headers_renaming_dict = {
    "data_point_txt": "Rec",
    "cycle_index_txt": "Cycle C",
    "step_index_txt": "Step",
    "test_time_txt": "TestTime",
    "step_time_txt": "StepTime",
    "charge_capacity_txt": "Cap. [Ah]",
    "charge_energy_txt": "Ener. [Wh]",
    "current_txt": "Current [A]",
    "voltage_txt": "Voltage [V]",
    "datetime_txt": "DPT Time",
}

states = {
    "column_name": "Md",
    "charge_keys": ["C"],
    "discharge_keys": ["D"],
    "rest_keys": ["R"],
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
    "skiprows": 12,  # 12 for other file
    "sep": "\t",
    "header": 0,  # 0 for other file
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
    "remove_last_if_bad": True,
    "set_cycle_number_not_zero": True,
    "convert_date_time_to_datetime": True,
}
