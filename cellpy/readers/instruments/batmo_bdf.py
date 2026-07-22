""" batmo outputs in BDF format. """
import cellpy.config as config

import pandas as pd

from cellpy import exceptions
from cellpy.parameters.internal_settings import (
    base_columns_float,
    base_columns_int,
    get_headers_normal,
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

    default_model = config.instruments.Batmo.default_model  # Required
    supported_models = SUPPORTED_MODELS  # Required

    def parse(self, source, **kwargs):
        """Vendor stage (#560 Phase C): BDF decode into a cellpy-named frame.

        BatMo's inherited ``TxtLoader.parse()`` only reads the CSV. The real
        decoding — hours→seconds, signed current from ``Step Type``, continuous
        step indices, step_time, synthetic ``data_point`` / ``date_time`` —
        lives in :meth:`_post_rename_headers` and used to run only on the
        legacy ``loader()`` path. Under ``harmonize(parse())`` that left
        ``test_time`` in hours (#621). Mirror the biologics pattern: ``parse()``
        performs the decode, ``declarations()`` maps the resulting cellpy
        headers to native.
        """
        import polars as pl

        from cellpy.readers.data_structures import Data
        from cellpy.readers.instruments.processors import post_processors

        vendor = super().parse(source, **kwargs)
        if not isinstance(vendor, pd.DataFrame):
            vendor = vendor.to_pandas()

        data = Data()
        data.raw = vendor
        # rename_headers is what turns "Test Time / h" into test_time, etc.
        data = post_processors.rename_headers(data, self.config_params)
        data = self._post_rename_headers(data)
        self._parsed_raw = data.raw
        self._parsed = True
        return pl.from_pandas(data.raw.reset_index(drop=True))

    def declarations(self):
        """Declarations for BatMo BDF (#560 Phase C).

        The parsed frame already uses cellpy header names (see :meth:`parse`),
        so the map is ``derive_column_maps`` over the identity
        ``{legacy_attr -> its own header name}`` restricted to columns this
        file produced. ``datetime_kind="datetime"`` because
        :meth:`_post_rename_headers` builds a real datetime from test_time.
        ``cumulate_capacity_within_cycle`` in the configuration marks
        capacities as ``PER_STEP``.
        """
        from cellpycore.units import CellpyUnits

        from cellpy.exceptions import LoaderError
        from cellpy.readers.instruments.config_declarations import derive_column_maps
        from cellpy.readers.instruments.declarations import (
            LoaderDeclarations,
            ResetGranularity,
        )

        if not getattr(self, "_parsed", False):
            raise LoaderError("batmo_bdf.declarations() was called before parse().")

        produced = set(self._parsed_raw.columns)
        renaming = {
            attr: name
            for attr, name in get_headers_normal().items()
            if name in produced
        }
        column_map, passthrough, _ = derive_column_maps(renaming)

        # Hours→seconds and the other decode steps already ran in parse(); the
        # configuration's cumulate flag still states PER_STEP granularity.
        raw_units = {
            key: value
            for key, value in self.get_raw_units().items()
            if hasattr(CellpyUnits(), key)
        }
        granularity = {
            column: ResetGranularity.PER_STEP
            for column in (
                "cumulative_charge_capacity",
                "cumulative_discharge_capacity",
            )
            if column in column_map.values()
        }
        # Protocol / step-type columns are decode inputs, not measurements.
        dropped = tuple(
            column
            for column in ("Protocol Name / 1", "Step Type / 1")
            if column in produced
        )
        # Anything still on the frame under a vendor name (state column is
        # kept through rename as raw text sometimes) — silence if unmapped.
        claimed = set(column_map) | set(passthrough)
        dropped = dropped + tuple(
            column
            for column in produced
            if column not in claimed and column not in dropped
        )

        return LoaderDeclarations(
            column_map=column_map,
            raw_units=CellpyUnits(**raw_units),
            passthrough=passthrough,
            reset_granularity=granularity,
            dropped=dropped,
            datetime_kind="datetime",
        )

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
