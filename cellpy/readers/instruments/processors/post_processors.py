"""Post-processing methods for instrument loaders.

All methods must implement the following parameters/arguments:
    filename: Union[str, pathlib.Path], *args: str, **kwargs: str

All methods should return None (i.e. nothing).

"""

import logging

import pandas as pd

from cellpy.parameters.internal_settings import headers_normal
from cellpy.readers.core import Cell
from cellpy.readers.instruments.configurations import ModelParameters


def set_cycle_number_not_zero(data: Cell, config_params: ModelParameters) -> Cell:
    data.raw[headers_normal.cycle_index_txt] += 1
    return data


def convert_date_time_to_datetime(data: Cell, config_params: ModelParameters) -> Cell:
    hdr_date_time = headers_normal.datetime_txt
    data.raw[hdr_date_time] = pd.to_datetime(data.raw[hdr_date_time])
    return data


def convert_step_time_to_timedelta(data: Cell, config_params: ModelParameters) -> Cell:
    hdr_step_time = headers_normal.step_time_txt
    data.raw[hdr_step_time] = pd.to_timedelta(
        data.raw[hdr_step_time]
    ).dt.total_seconds()
    return data


def convert_test_time_to_timedelta(data: Cell, config_params: ModelParameters) -> Cell:
    hdr_test_time = headers_normal.test_time_txt
    x = pd.to_timedelta(data.raw[hdr_test_time])
    data.raw[hdr_test_time] = x.dt.total_seconds()
    return data


def set_index(data: Cell, config_params: ModelParameters) -> Cell:
    hdr_data_point = headers_normal.data_point_txt
    if data.raw.index.name != hdr_data_point:
        data.raw = data.raw.set_index(hdr_data_point, drop=False)
    return data


def rename_headers(data: Cell, config_params: ModelParameters) -> Cell:
    columns = {}
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
        states: dictionary defining the state identification character/string

    Returns: raw data

    """
    if base_col_name is None:
        base_col_name = headers_normal.charge_capacity_txt
    cycle_index_hdr = headers_normal.cycle_index_txt
    data_point = headers_normal.data_point_txt
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
                charge_last_index, charge_last_val = charge.iloc[-1]
                raw[temp_col_name_charge].update(n_charge * charge[base_col_name])

                raw.loc[
                    (raw[data_point] > charge_last_index) & (raw[cycle_index_hdr] == i),
                    temp_col_name_charge,
                ] = charge_last_val

            if not discharge.empty:
                (discharge_last_index, discharge_last_val) = discharge.iloc[-1]
                raw[temp_col_name_discharge].update(
                    n_discharge * discharge[base_col_name]
                )

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


def split_current(data: Cell, config_params: ModelParameters) -> Cell:
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
        states=config_params.states,
    )
    return data


def split_capacity(data: Cell, config_params: ModelParameters) -> Cell:
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
        states=config_params.states,
    )
    return data


