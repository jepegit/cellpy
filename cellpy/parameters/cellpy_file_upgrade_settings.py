from dataclasses import dataclass
from pathlib import Path
from typing import Union, Tuple, Dict, Optional, Any, List

import pandas as pd
import numpy as np

from cellpy.parameters.internal_settings import BaseHeaders, CELLPY_FILE_VERSION


@dataclass
class HeadersSummaryV6(BaseHeaders):
    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    discharge_capacity: str = "discharge_capacity_u_mAh_g"
    charge_capacity: str = "charge_capacity_u_mAh_g"


@dataclass
class HeadersSummaryV7(BaseHeaders):
    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    discharge_capacity: str = "discharge_capacity_gravimetric"
    charge_capacity: str = "charge_capacity_gravimetric"


summary_header_versions = {
    1: HeadersSummaryV6(),
    2: HeadersSummaryV6(),
    3: HeadersSummaryV6(),
    4: HeadersSummaryV6(),
    5: HeadersSummaryV6(),
    6: HeadersSummaryV6(),
    7: HeadersSummaryV7(),
}


def rename_summary_columns(summary, old_version, new_version=None, **kwargs):
    old = summary_header_versions.get(old_version)
    if not new_version:
        new_version = CELLPY_FILE_VERSION
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
) -> tuple[dict[str, str], list[str], list[str]]:
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
    remove_missing_in_new: bool = True,
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
