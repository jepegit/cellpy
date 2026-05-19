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
    "bdf": "batmo_bdf_bdf",
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

    def pre_process(self, data):
        """Pre-processes the data before formatting."""
        # Convert time from hours to seconds
        data.raw[headers_normal.test_time_txt] = data.raw[headers_normal.test_time_txt] * 3600.0

        # We must also make sure that the step indices are cumulated and do not reset on cycle boundaries
        # Because we only have 'Step Type', we use the fact that cellpy's configurations will map
        # 'Step Type' to step_index_txt, but it is currently mapped to text values like 'charge'.
        # Actually, looking at the data, we do have a Step Index / 1 column. But wait...
        # Let's see the header again: "Protocol Name / 1,Step Type / 1,Cycle Count / 1,Step Index / 1"
        # Ah, Step Index is actually the 7th column, and looking at the output from `awk`, it seems Batmo
        # actually DOES increase the Step Index. For Cycle 1 it goes 1, 2, 3, 4, 5. For cycle 2 it goes 1, 2, 3, 4, 5.
        # Wait, that means it DOES reset per cycle!
        # Cellpy expects the step_index_txt to strictly increase during the entire run. Let's fix that.
        
        step_index_col = headers_normal.step_index_txt
        cycle_index_col = headers_normal.cycle_index_txt

        if step_index_col in data.raw.columns and cycle_index_col in data.raw.columns:
            # We want to create a strictly increasing step index
            # We can do this by finding where the step index or cycle index changes
            # We just detect any change in the combination of cycle and original step index
            group_col = data.raw[cycle_index_col].astype(str) + "_" + data.raw[step_index_col].astype(str)
            # Create a cumulated step index based on changes in group_col
            data.raw[step_index_col] = (group_col != group_col.shift()).cumsum()

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
