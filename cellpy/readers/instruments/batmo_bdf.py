""" batmo outputs in BDF format. """

import pandas as pd

from cellpy import prms
from cellpy import exceptions
from cellpy.parameters.internal_settings import (
    base_columns_float,
    base_columns_int,
    headers_normal,
)
from cellpy.readers.instruments.base import TxtLoader

SUPPORTED_MODELS = {
    "BDF": "batmo_bdf_bdf",
}

MUST_HAVE_RAW_COLUMNS = [
    headers_normal.test_time_txt,
    headers_normal.current_txt,
    headers_normal.voltage_txt,
    headers_normal.step_index_txt,
    headers_normal.cycle_index_txt,
    headers_normal.charge_capacity_txt,
    headers_normal.discharge_capacity_txt,
]


class DataLoader(TxtLoader):
    """Class for loading data from BatMo BDF txt files."""

    instrument_name = "batmo"
    raw_ext = "csv"

    default_model = prms.Instruments.Batmo["default_model"]  # Required
    supported_models = SUPPORTED_MODELS  # Required

    def _post_rename_headers(self, data):
        """Normalize BatMo columns after they have been renamed to cellpy names."""
        data.raw[headers_normal.data_point_txt] = range(1, len(data.raw) + 1)

        test_time_col = headers_normal.test_time_txt
        data.raw[test_time_col] = pd.to_numeric(
            data.raw[test_time_col], errors="coerce"
        )
        data.raw[test_time_col] = data.raw[test_time_col] * 3600.0

        state_col = "Step Type / 1"
        current_col = headers_normal.current_txt
        if state_col in data.raw.columns and current_col in data.raw.columns:
            state = data.raw[state_col].astype(str).str.lower()
            current = pd.to_numeric(data.raw[current_col], errors="coerce").abs()
            data.raw[current_col] = current.where(~state.eq("discharge"), -current)
            data.raw.loc[state.eq("rest"), current_col] = 0.0

        step_index_col = headers_normal.step_index_txt
        cycle_index_col = headers_normal.cycle_index_txt
        if step_index_col in data.raw.columns and cycle_index_col in data.raw.columns:
            group_col = (
                data.raw[cycle_index_col].astype(str)
                + "_"
                + data.raw[step_index_col].astype(str)
            )
            data.raw[step_index_col] = (group_col != group_col.shift()).cumsum()

        step_time_col = headers_normal.step_time_txt
        data.raw[step_time_col] = data.raw[test_time_col] - data.raw.groupby(
            step_index_col
        )[test_time_col].transform("first")

        datetime_col = headers_normal.datetime_txt
        data.raw[datetime_col] = pd.Timestamp("1970-01-01") + pd.to_timedelta(
            data.raw[test_time_col], unit="s"
        )

        return data

    def validate(self, data):
        """A simple check that all the needed columns has been successfully
        loaded and that they get the correct type"""
        missing_must_have_columns = []

        # validating the float-type raw data
        for col in base_columns_float:
            if col in data.raw.columns:
                data.raw[col] = pd.to_numeric(data.raw[col], errors="coerce")
            else:
                if col in MUST_HAVE_RAW_COLUMNS:
                    missing_must_have_columns.append(col)

        # validating the integer-type raw data
        for col in base_columns_int:
            if col in data.raw.columns:
                data.raw[col] = pd.to_numeric(
                    data.raw[col], errors="coerce", downcast="integer"
                )
            else:
                if col in MUST_HAVE_RAW_COLUMNS:
                    missing_must_have_columns.append(col)

        if missing_must_have_columns:
            raise exceptions.IOError(
                f"Missing needed columns: {missing_must_have_columns}\nAborting!"
            )
        return data
