from dataclasses import dataclass
from pathlib import Path
from typing import Union, Tuple, Dict, Optional, Any, List

import pandas as pd
import numpy as np

from cellpy.parameters.internal_settings import BaseHeaders, CELLPY_FILE_VERSION


@dataclass
class HeadersSummaryV7(BaseHeaders):
    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    test_name: str = "test_name"
    data_flag: str = "data_flag"
    channel_id: str = "channel_id"

    coulombic_efficiency: str = "coulombic_efficiency"
    cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency"

    discharge_capacity: str = "discharge_capacity_gravimetric"
    charge_capacity: str = "charge_capacity_gravimetric"
    cumulated_charge_capacity: str = "cumulated_charge_capacity_gravimetric"
    cumulated_discharge_capacity: str = "cumulated_discharge_capacity_gravimetric"

    coulombic_difference: str = "coulombic_difference_gravimetric"
    cumulated_coulombic_difference: str = "cumulated_coulombic_difference_gravimetric"
    discharge_capacity_loss: str = "discharge_capacity_loss_gravimetric"
    charge_capacity_loss: str = "charge_capacity_loss_gravimetric"
    cumulated_discharge_capacity_loss: str = (
        "cumulated_discharge_capacity_loss_gravimetric"
    )
    cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss_gravimetric"

    areal_charge_capacity: str = "charge_capacity_areal"
    areal_discharge_capacity: str = "discharge_capacity_areal"

    shifted_charge_capacity: str = "shifted_charge_capacity_gravimetric"
    shifted_discharge_capacity: str = "shifted_discharge_capacity_gravimetric"

    ir_discharge: str = "ir_discharge"
    ir_charge: str = "ir_charge"
    ocv_first_min: str = "ocv_first_min"
    ocv_second_min: str = "ocv_second_min"
    ocv_first_max: str = "ocv_first_max"
    ocv_second_max: str = "ocv_second_max"
    end_voltage_discharge: str = "end_voltage_discharge"
    end_voltage_charge: str = "end_voltage_charge"
    cumulated_ric_disconnect: str = "cumulated_ric_disconnect"
    cumulated_ric_sei: str = "cumulated_ric_sei"
    cumulated_ric: str = "cumulated_ric"
    normalized_cycle_index: str = "normalized_cycle_index"
    normalized_charge_capacity: str = "normalized_charge_capacity"
    normalized_discharge_capacity: str = "normalized_discharge_capacity"
    low_level: str = "low_level"
    high_level: str = "high_level"

    temperature_last: str = "temperature_last"
    temperature_mean: str = "temperature_mean"

    charge_c_rate: str = "charge_c_rate"
    discharge_c_rate: str = "discharge_c_rate"
    # pre_aux: str = "aux_"

    # @property
    # def discharge_capacity(self) -> str:
    #     if self.mode == "gravimetric":
    #         return "discharge_capacity_gravimetric"
    #     elif self.mode == "areal":
    #         return "discharge_capacity_areal"
    #     else:
    #         return "discharge_capacity"


@dataclass
class HeadersSummaryV6(BaseHeaders):
    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    test_name: str = "test_name"
    data_flag: str = "data_flag"
    channel_id: str = "channel_id"
    discharge_capacity: str = "discharge_capacity_u_mAh_g"
    charge_capacity: str = "charge_capacity_u_mAh_g"
    cumulated_charge_capacity: str = "cumulated_charge_capacity_u_mAh_g"
    cumulated_discharge_capacity: str = "cumulated_discharge_capacity_u_mAh_g"
    coulombic_efficiency: str = "coulombic_efficiency_u_percentage"
    cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency_u_percentage"
    coulombic_difference: str = "coulombic_difference_u_mAh_g"
    cumulated_coulombic_difference: str = "cumulated_coulombic_difference_u_mAh_g"
    discharge_capacity_loss: str = "discharge_capacity_loss_u_mAh_g"
    charge_capacity_loss: str = "charge_capacity_loss_u_mAh_g"
    cumulated_discharge_capacity_loss: str = "cumulated_discharge_capacity_loss_u_mAh_g"
    cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss_u_mAh_g"
    ir_discharge: str = "ir_discharge_u_Ohms"
    ir_charge: str = "ir_charge_u_Ohms"
    ocv_first_min: str = "ocv_first_min_u_V"
    ocv_second_min: str = "ocv_second_min_u_V"
    ocv_first_max: str = "ocv_first_max_u_V"
    ocv_second_max: str = "ocv_second_max_u_V"
    end_voltage_discharge: str = "end_voltage_discharge_u_V"
    end_voltage_charge: str = "end_voltage_charge_u_V"
    cumulated_ric_disconnect: str = "cumulated_ric_disconnect_u_none"
    cumulated_ric_sei: str = "cumulated_ric_sei_u_none"
    cumulated_ric: str = "cumulated_ric_u_none"
    normalized_cycle_index: str = "normalized_cycle_index"
    normalized_charge_capacity: str = "normalized_charge_capacity"
    normalized_discharge_capacity: str = "normalized_discharge_capacity"
    low_level: str = "low_level_u_percentage"
    high_level: str = "high_level_u_percentage"
    shifted_charge_capacity: str = "shifted_charge_capacity_u_mAh_g"
    shifted_discharge_capacity: str = "shifted_discharge_capacity_u_mAh_g"
    temperature_last: str = "temperature_last_u_C"
    temperature_mean: str = "temperature_mean_u_C"
    areal_charge_capacity: str = "areal_charge_capacity_u_mAh_cm2"
    areal_discharge_capacity: str = "areal_discharge_capacity_u_mAh_cm2"
    charge_c_rate: str = "charge_c_rate"
    discharge_c_rate: str = "discharge_c_rate"
    # pre_aux: str = "aux_"


summary_header_versions = {
    1: HeadersSummaryV6(),
    2: HeadersSummaryV6(),
    3: HeadersSummaryV6(),
    4: HeadersSummaryV6(),
    5: HeadersSummaryV6(),
    6: HeadersSummaryV6(),
    7: HeadersSummaryV7(),
}


def rename_summary_columns(
    summary: pd.DataFrame,
    old_version: int,
    new_version: int = CELLPY_FILE_VERSION,
    **kwargs,
) -> pd.DataFrame:
    """Rename the summary headers to new format.

    Args:
        summary: summary dataframe in old format.
        old_version: old format (cellpy_file_format (might use summary format number instead soon)).
        new_version: new format (cellpy_file_format (might use summary format number instead soon)).
        **kwargs:
            remove_missing_in_new (bool): remove the columns that are not defined in the new format.
            populate_missing_in_old (bool): add "new-format" missing columns (with np.NAN).

    Returns:
        summary (pandas.DataFrame) with column headers in the new format.
    """

    old = summary_header_versions.get(old_version)
    new = summary_header_versions.get(new_version)
    summary = rename_columns(
        summary,
        old,
        new,
        **kwargs,
    )
    return summary


def get_column_name_mapper(
    old_columns: BaseHeaders, new_columns: BaseHeaders
) -> Tuple[Dict[str, str], List[str], List[str]]:
    """Create a dictionary that maps old column names to new column names.

    Args:
        old_columns: The BaseHeaders for the old format.
        new_columns: The BaseHeaders for the new format.

    Returns:
        Translation dictionary, list of missing keys in new format, list of missing keys in old format.
    """
    translations = {}
    missing_in_old = []
    old_columns_keys = old_columns.keys()
    new_columns_keys = new_columns.keys()
    for key in new_columns_keys:
        if old_column := old_columns.get(key):
            translations[old_column] = new_columns.get(key)
            old_columns_keys.remove(key)
        else:
            missing_in_old.append(key)

    missing_in_new = old_columns_keys
    return translations, missing_in_new, missing_in_old


def rename_columns(
    df: pd.DataFrame,
    old: BaseHeaders,
    new: BaseHeaders,
    remove_missing_in_new: bool = False,
    populate_missing_in_old: bool = True,
) -> pd.DataFrame:
    """Rename the column headers of a cells dataframe.

    Usage:
        >>>  old_format_headers = HeadersSummaryV6()
        >>>  new_format_headers = HeadersSummaryV7()
        >>>  df_new_format = rename_columns(df_old_format, old_format_headers, new_format_headers)

    Args:
        df: The dataframe.
        old: The BaseHeaders for the old format.
        new: The BaseHeaders for the new format.
        remove_missing_in_new: remove the columns that are not defined in the new format.
        populate_missing_in_old: add "new-format" missing columns (with np.NAN).

    Returns:
        Dataframe with updated columns
    """
    col_name_mapper, missing_in_new, missing_in_old = get_column_name_mapper(old, new)

    if remove_missing_in_new:
        for col in missing_in_new:
            df = df.drop(col, axis=1)

    if populate_missing_in_old:
        for col in missing_in_old:
            df[col] = np.NAN

    return df.rename(columns=col_name_mapper)


def _create_dummy_summary(columns):
    df = pd.DataFrame(
        data=np.random.rand(5, len(columns) - 1), index=range(1, 6), columns=columns[1:]
    )
    df.index.name = columns[0]
    return df


def check():
    old = HeadersSummaryV6()
    new = HeadersSummaryV7()
    df = _create_dummy_summary(columns=old.keys())
    remove_missing_in_new = False
    populate_missing_in_old = True

    df = rename_columns(
        df,
        old,
        new,
        remove_missing_in_new=remove_missing_in_new,
        populate_missing_in_old=populate_missing_in_old,
    )
    print(df.head())


if __name__ == "__main__":
    check()
