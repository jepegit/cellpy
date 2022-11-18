"""Post-processing methods for instrument loaders.

All methods must implement the following parameters/arguments:
    data: Data object
    config_params: ModelParameters

All methods should return the modified Data object.

You can access the individual parameters for the post processor from
the config_params.post_processor[<name of post processor>].

"""
import datetime
import logging
import sys

import pandas as pd
import numpy as np

from cellpy.parameters.internal_settings import headers_normal
from cellpy.parameters.prms import _minimum_columns_to_keep_for_raw_if_exists
from cellpy.readers.core import Data
from cellpy.readers.instruments.configurations import ModelParameters

ORDERED_POST_PROCESSING_STEPS = [
    "get_column_names",
    "rename_headers",
    "select_columns_to_keep",
    "remove_last_if_bad",
]

# TODO: implement from old custom
#  1. implement proper unit conversion
#     a. find out how it works now
#     b. make sure that the user can define preferred units (config)
#     c. make sure the used units are stored in the cellpy files
#     d. make sure the loaded data is converted to the expected units
#     e. implement parser for finding units based on headers or meta-data
#  2. parse top part (meta)
#     a. add key-word for format of meta data (key_value_pairs, etc.)
#     b. load meta-part and pares it (use the ATTRS_CELLPYFILE and setattr)
#  3. the old custom loader has methods for parsing csv, xls,
#     and xlsx - implement them if needed. [DONE]
#  4. Consider adding x_time_conversion key-words and methods from old custom.
#  5. Check if CustomTxtLoader properly implements inspect() and
#     _generate_fid().


def remove_last_if_bad(data: Data, config_params: ModelParameters) -> Data:
    """Drop the last row if it contains more NaNs than second to last."""
    number_of_nans_2nd_last = data.raw.iloc[-2].isna().sum()
    number_of_nans_last = data.raw.iloc[-1].isna().sum()
    if number_of_nans_last > number_of_nans_2nd_last:
        data.raw = data.raw.drop(data.raw.tail(1).index)  # drop last row
    return data


def convert_units(data: Data, config_params: ModelParameters) -> Data:
    raise Exception("THIS FUNCTION NEEDS TO BE UPDATED")
    # TODO: implement all
    if x := config_params.raw_units.get("voltage", None):
        logging.debug(f"converting voltage ({x})")
        data.raw[headers_normal.voltage_txt] = data.raw[headers_normal.voltage_txt] * x

    if config_params.raw_units.get("current", None):
        logging.debug("converting current - not implemented yet")

    if config_params.raw_units.get("charge", None):
        logging.debug("converting charge - not implemented yet")

    # TODO: add time as raw unit
    if config_params.raw_units.get("time", None):
        logging.debug("converting time - not implemented yet")

    return data


def set_cycle_number_not_zero(data: Data, config_params: ModelParameters) -> Data:
    data.raw[headers_normal.cycle_index_txt] += 1
    return data


def select_columns_to_keep(data: Data, config_params: ModelParameters) -> Data:
    config_params.columns_to_keep.extend(
        headers_normal[h] for h in _minimum_columns_to_keep_for_raw_if_exists
    )
    if config_params.states:
        config_params.columns_to_keep.append(config_params.states["column_name"])
    config_params.columns_to_keep = list(set(config_params.columns_to_keep))
    columns_to_keep = [
        col for col in config_params.columns_to_keep if col in data.raw.columns
    ]
    data.raw = data.raw[columns_to_keep]
    return data


def get_column_names(data: Data, config_params: ModelParameters) -> Data:
    # TODO: add custom "splitter"
    # TODO: test
    raise Exception("THIS FUNCTION NEEDS TO BE UPDATED")
    if not config_params.prefixes:
        config_params.prefixes = {
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

    DEFAULT_RAW_UNITS = {
        "current": 1.0,
        "charge": 1.0,
        "mass": 1.0,
        "voltage": 1.0,
    }

    renaming = config_params.normal_headers_renaming_dict
    unit_labels = config_params.unit_labels

    for label in ["current", "voltage", "power", "capacity", "energy"]:
        unit_label = unit_labels[label]
        prefix = None
        header = None

        if h := data.raw.columns[data.raw.columns.str.endswith(unit_label)].values:
            header = h[0]
            prefix, _ = header.split(unit_label)
            if label == "capacity":
                renaming[f"charge_{label}_txt"] = header
                label = "charge"
            else:
                renaming[f"{label}_txt"] = header

            if label not in config_params.raw_units:
                if prefix:
                    config_params.raw_units[label] = config_params.prefixes[prefix]
                else:
                    config_params.raw_units[label] = 1.0

        for k in DEFAULT_RAW_UNITS:
            config_params.raw_units[k] = config_params.raw_units.get(
                k, DEFAULT_RAW_UNITS[k]
            )
    return data


def convert_date_time_to_datetime(data: Data, config_params: ModelParameters) -> Data:
    hdr_date_time = headers_normal.datetime_txt
    data.raw[hdr_date_time] = pd.to_datetime(data.raw[hdr_date_time])
    return data


def date_time_from_test_time(data: Data, config_params: ModelParameters) -> Data:
    """add a date_time column (based on the test_time column)."""
    hdr_date_time = headers_normal.datetime_txt
    hdr_test_time = headers_normal.test_time_txt

    # replace this with something that can parse a date-string if implementing start_date in config_params.
    # currently, it will always use current date-time as start date.
    start_date = config_params.meta_keys.get("start_date", datetime.datetime.now())
    start_time = data.raw[hdr_test_time].iloc[0]
    data.raw[hdr_date_time] = (
        pd.to_timedelta(data.raw[hdr_test_time] - start_time) + start_date
    )
    return data


def convert_step_time_to_timedelta(data: Data, config_params: ModelParameters) -> Data:
    hdr_step_time = headers_normal.step_time_txt
    if data.raw[hdr_step_time].dtype == "datetime64[ns]":
        logging.debug("already datetime64[ns] - need to convert to back first")
        data.raw[hdr_step_time] = data.raw[hdr_step_time].view("int64")
        data.raw[hdr_step_time] = (
            data.raw[hdr_step_time] - data.raw[hdr_step_time].iloc[0]
        )

    data.raw[hdr_step_time] = pd.to_timedelta(
        data.raw[hdr_step_time]
    ).dt.total_seconds()
    return data


def convert_test_time_to_timedelta(data: Data, config_params: ModelParameters) -> Data:
    hdr_test_time = headers_normal.test_time_txt
    if data.raw[hdr_test_time].dtype == "datetime64[ns]":
        logging.debug("already datetime64[ns] - need to convert to back first")
        data.raw[hdr_test_time] = data.raw[hdr_test_time].view("int64")
        data.raw[hdr_test_time] = (
            data.raw[hdr_test_time] - data.raw[hdr_test_time].iloc[0]
        )
    data.raw[hdr_test_time] = pd.to_timedelta(
        data.raw[hdr_test_time]
    ).dt.total_seconds()
    return data


def set_index(data: Data, config_params: ModelParameters) -> Data:
    hdr_data_point = headers_normal.data_point_txt
    if data.raw.index.name != hdr_data_point:
        data.raw = data.raw.set_index(hdr_data_point, drop=False)
    return data


def cumulate_capacity_within_cycle(data: Data, config_params: ModelParameters) -> Data:
    """Cumulates the capacity within each cycle"""
    # state_column = config_params.states["column_name"]
    # is_charge = config_params.states["charge_keys"]
    # is_discharge = config_params.states["discharge_keys"]
    cycles = data.raw.groupby("cycle_index")
    cumulated = []
    charge_hdr = "charge_capacity"
    discharge_hdr = "discharge_capacity"

    for i, (cycle_number, cycle) in enumerate(cycles):
        steps = cycle.groupby("step_index")
        last_charge = 0.0
        last_discharge = 0.0
        for step_number, step in steps:
            step[charge_hdr] = step[charge_hdr] + last_charge
            step[discharge_hdr] = step[discharge_hdr] + last_discharge
            last_charge = step.at[step.index[-1], charge_hdr]
            last_discharge = step.at[step.index[-1], discharge_hdr]
            cumulated.append(step)
    data.raw = pd.concat(cumulated)
    return data


def replace(data: Data, config_params: ModelParameters) -> Data:
    print("NOT IMPLEMENTED")
    print("input:")
    print(config_params.post_processors["replace"])


def rename_headers(data: Data, config_params: ModelParameters) -> Data:
    columns = {}
    renaming_dict = config_params.normal_headers_renaming_dict
    # ---- special cases ----
    # 1. datetime_txt and test_time_txt same column
    if "datetime_txt" in renaming_dict and "test_time_txt" in renaming_dict:
        datetime_hdr = renaming_dict["datetime_txt"]
        test_time_hdr = renaming_dict["test_time_txt"]
        if datetime_hdr == test_time_hdr:
            logging.debug("both test_time and datetime assigned to same column")
            logging.debug("duplicating the column")
            new_test_time_hdr = (
                f"_{test_time_hdr}_cellpy_temporary_col_name_for_test_time"
            )
            data.raw[new_test_time_hdr] = data.raw[datetime_hdr]
            renaming_dict["test_time_txt"] = new_test_time_hdr

    for key in headers_normal:
        if key in config_params.normal_headers_renaming_dict:
            old_header = config_params.normal_headers_renaming_dict[key]
            new_header = headers_normal[key]
            # print(f"renaming {old_header} to {new_header}")
            columns[old_header] = new_header
    data.raw.rename(index=str, columns=columns, inplace=True)

    data.raw.rename(
        index=str,
        columns=config_params.not_implemented_in_cellpy_yet_renaming_dict,
        inplace=True,
    )
    return data


def _state_splitter(
    raw: pd.DataFrame,
    base_col_name="charge_capacity",
    n_charge=1,
    n_discharge=1,
    new_col_name_charge="charge_capacity",
    new_col_name_discharge="discharge_capacity",
    temp_col_name_charge="tmp_charge",
    temp_col_name_discharge="tmp_discharge",
    propagate=True,
    to_numeric=True,
    states=None,
) -> pd.DataFrame:
    """Split states.

    Args:
        raw: the raw data dataframe
        base_col_name: what column to split
        n_charge: sign of charge (e.g. 1 for positive)
        n_discharge: sign of discharge (e.g. -1 for negative)
        new_col_name_charge: str
        new_col_name_discharge: str
        temp_col_name_charge: str
        temp_col_name_discharge: str
        propagate: bool
        to_numeric: bool
        states: dictionary defining the state identification character/string

    Returns: raw data

    """
    if base_col_name is None:
        base_col_name = headers_normal.charge_capacity_txt
    cycle_index_hdr = headers_normal.cycle_index_txt
    data_point = headers_normal.data_point_txt

    if to_numeric:
        raw[base_col_name] = pd.to_numeric(raw[base_col_name], errors="coerce")

    if states is None:
        states = {
            "column_name": "State",
            "charge_keys": ["C"],
            "discharge_keys": ["D"],
            "rest_keys": ["R"],
        }
    state_column = states["column_name"]
    charge_keys = states["charge_keys"]
    rest_keys = states["rest_keys"]
    discharge_keys = states["discharge_keys"]

    raw[temp_col_name_charge] = 0
    if temp_col_name_charge != temp_col_name_discharge:
        raw[temp_col_name_discharge] = 0

    cycle_numbers = raw[cycle_index_hdr].unique()
    good_cycles = []
    bad_cycles = []

    for i in cycle_numbers:
        try:
            charge = raw.loc[
                (raw[state_column].isin(charge_keys)) & (raw[cycle_index_hdr] == i),
                [data_point, base_col_name],
            ]

            discharge = raw.loc[
                (raw[state_column].isin(discharge_keys)) & (raw[cycle_index_hdr] == i),
                [data_point, base_col_name],
            ]

            if not charge.empty:
                raw[temp_col_name_charge].update(n_charge * charge[base_col_name])
                if propagate:
                    charge_last_index, charge_last_val = charge.iloc[-1]
                    raw.loc[
                        (raw[data_point] > charge_last_index)
                        & (raw[cycle_index_hdr] == i),
                        temp_col_name_charge,
                    ] = charge_last_val

            if not discharge.empty:
                raw[temp_col_name_discharge].update(
                    n_discharge * discharge[base_col_name]
                )
                if propagate:
                    (discharge_last_index, discharge_last_val) = discharge.iloc[-1]
                    raw.loc[
                        (raw[data_point] > discharge_last_index)
                        & (raw[cycle_index_hdr] == i),
                        temp_col_name_discharge,
                    ] = discharge_last_val
            good_cycles.append(i)

        except Exception:
            bad_cycles.append(i)
    if bad_cycles:
        logging.critical(f"The data contains bad cycles: {bad_cycles}")

    raw[new_col_name_charge] = raw[temp_col_name_charge]
    raw = raw.drop([temp_col_name_charge], axis=1)
    if temp_col_name_charge != temp_col_name_discharge:
        raw[new_col_name_discharge] = raw[temp_col_name_discharge]
        raw = raw.drop([temp_col_name_discharge], axis=1)
    return raw


def split_current(data: Data, config_params: ModelParameters) -> Data:
    """Split current into positive and negative"""
    data.raw = _state_splitter(
        data.raw,
        base_col_name="current",
        n_charge=1,
        n_discharge=-1,
        temp_col_name_charge="tmp_charge",
        new_col_name_charge=headers_normal.current_txt,
        new_col_name_discharge=headers_normal.current_txt,
        temp_col_name_discharge="tmp_charge",
        propagate=False,
        states=config_params.states,
    )
    return data


def split_capacity(data: Data, config_params: ModelParameters) -> Data:
    """split capacity into charge and discharge"""
    data.raw = _state_splitter(
        data.raw,
        base_col_name=headers_normal.charge_capacity_txt,
        n_charge=1,
        n_discharge=1,
        new_col_name_charge=headers_normal.charge_capacity_txt,
        new_col_name_discharge=headers_normal.discharge_capacity_txt,
        temp_col_name_charge="tmp_charge",
        temp_col_name_discharge="tmp_discharge",
        propagate=True,
        states=config_params.states,
    )
    return data
