"""PEC csv-type data files."""

import csv
import logging
import pathlib
import re
import warnings

import pandas as pd
from dateutil.parser import parse

from cellpy.parameters.internal_settings import (
    base_columns_float,
    base_columns_int,
    get_headers_normal,
)
from cellpy.readers.data_structures import Data
from cellpy.readers.instruments.base import BaseLoader


def inspect_pec_csv_metadata(file_name):
    """Inspect PEC CSV preamble metadata without loading the full dataset."""

    loader = DataLoader()
    loader.name = pathlib.Path(file_name)
    loader.copy_to_temporary()
    loader.number_of_header_lines = loader._find_header_length()
    metadata = loader._parse_metadata()
    metadata["file_name"] = pathlib.Path(file_name)
    metadata["test_number"] = _extract_test_number_from_pec_path(file_name)
    return metadata


def group_pec_csv_files_by_lot(file_names):
    """Group PEC CSV files by LotID and sort each group by numeric test id."""

    grouped = {}
    for file_name in file_names:
        metadata = inspect_pec_csv_metadata(file_name)
        lot_id = metadata.get("lot_id") or "<missing>"
        grouped.setdefault(lot_id, []).append(metadata)

    grouped_files = {}
    for lot_id, entries in grouped.items():
        ordered_entries = sorted(
            entries,
            key=lambda entry: (
                entry["test_number"] is None,
                (
                    entry["test_number"]
                    if entry["test_number"] is not None
                    else float("inf")
                ),
                pathlib.Path(entry["file_name"]).name,
            ),
        )
        grouped_files[lot_id] = [entry["file_name"] for entry in ordered_entries]
    return grouped_files


def load_pec_csv_groups_by_lot(file_names, **kwargs):
    """Load PEC CSV files into one CellpyCell per LotID."""

    from cellpy.readers.cellreader import CellpyCell

    cells = {}
    grouped_files = group_pec_csv_files_by_lot(file_names)
    for lot_id, files in grouped_files.items():
        cell = CellpyCell()
        cell.from_raw(files, instrument="pec_csv", **kwargs)
        _update_pec_group_metadata(cell, lot_id, files)
        cells[lot_id] = cell
    return cells


def _extract_test_number_from_pec_path(file_name):
    match = re.search(r"Test(\d+)\.csv$", pathlib.Path(file_name).name)
    if match is None:
        return None
    return int(match.group(1))


def _update_pec_group_metadata(cell, lot_id, files):
    metadata_entries = [inspect_pec_csv_metadata(file_name) for file_name in files]

    if cell.data.custom_info is None:
        cell.data.custom_info = {}

    pec_metadata = dict(cell.data.custom_info.get("pec_metadata", {}))
    pec_metadata["lot_id"] = None if lot_id == "<missing>" else lot_id

    group_metadata = {
        "grouped_by": "lot_id",
        "lot_ids": sorted(
            {
                entry["lot_id"]
                for entry in metadata_entries
                if entry.get("lot_id") not in [None, ""]
            }
        ),
        "source_test_ids": [
            entry["test_number"]
            for entry in metadata_entries
            if entry["test_number"] is not None
        ],
        "source_files": [pathlib.Path(file_name) for file_name in files],
    }

    cell.data.custom_info["pec_metadata"] = pec_metadata
    cell.data.custom_info["pec_group_metadata"] = group_metadata


class DataLoader(BaseLoader):
    """Class for loading exported data from PEC."""

    instrument_name = "pec_csv"
    raw_ext = "csv"

    _HEADER_ALIASES = {
        "test": {"test"},
        "step": {"step"},
        "cycle": {"cycle"},
        "test_time": {
            "totaltimeseconds",
            "totaltimeminutes",
            "totaltimedecimalhours",
            "totaltimehoursinhhmmssxxx",
        },
        "step_time": {
            "steptimeseconds",
            "steptimeminutes",
            "steptimedecimalhours",
            "steptimehoursinhhmmssxxx",
        },
        "date_time": {"realtime"},
        "voltage": {"voltagev", "voltagemv", "voltageuv", "voltageµv"},
        "current": {"currenta", "currentma", "currentua", "currentµa"},
        "charge_capacity": {"chargecapacityah", "chargecapacitymah"},
        "discharge_capacity": {"dischargecapacityah", "dischargecapacitymah"},
        "charge_energy": {"chargeenergymwh", "chargeenergywh", "chargecapacitymwh"},
        "discharge_energy": {
            "dischargeenergymwh",
            "dischargeenergywh",
            "dischargecapacitymwh",
        },
        "internal_resistance": {
            "internalresistance1mohm",
            "internalresistance1ohm",
        },
    }
    _REQUIRED_HEADER_FIELDS = {
        "test",
        "step",
        "cycle",
        "date_time",
        "voltage",
        "current",
    }
    _MIN_HEADER_MATCHES = 8
    _TIME_FACTORS = {
        "seconds": 1.0,
        "minutes": 60.0,
        "decimalhours": 3600.0,
    }
    _UNIT_FACTORS = {
        "voltage": {"v": 1.0, "mv": 1e-3, "uv": 1e-6, "µv": 1e-6},
        "current": {"a": 1.0, "ma": 1e-3, "ua": 1e-6, "µa": 1e-6},
        "charge_capacity": {"ah": 1.0, "mah": 1e-3},
        "discharge_capacity": {"ah": 1.0, "mah": 1e-3},
        "charge_energy": {"wh": 1.0, "mwh": 1e-3},
        "discharge_energy": {"wh": 1.0, "mwh": 1e-3},
        "internal_resistance": {"ohm": 1.0, "mohm": 1e-3},
    }
    _COLUMN_KEY_TO_CELLPY_HEADER = {
        "test": "test_id_txt",
        "step": "step_index_txt",
        "cycle": "cycle_index_txt",
        "test_time": "test_time_txt",
        "step_time": "step_time_txt",
        "date_time": "datetime_txt",
        "voltage": "voltage_txt",
        "current": "current_txt",
        "charge_capacity": "charge_capacity_txt",
        "discharge_capacity": "discharge_capacity_txt",
        "charge_energy": "charge_energy_txt",
        "discharge_energy": "discharge_energy_txt",
        "internal_resistance": "internal_resistance_txt",
    }
    _MUST_HAVE_RAW_COLUMNS = [
        "test_time_txt",
        "step_time_txt",
        "current_txt",
        "voltage_txt",
        "step_index_txt",
        "cycle_index_txt",
        "charge_capacity_txt",
        "discharge_capacity_txt",
    ]

    def __init__(self, *args, **kwargs):
        self.headers_normal = get_headers_normal()
        self.cellpy_headers = self.headers_normal
        self.current_chunk = 0
        self.pec_settings = {}
        self.pec_file_delimiter = ","
        self.number_of_header_lines = None

    @staticmethod
    def _normalize_header_token(token):
        return "".join(ch for ch in token.lower() if ch.isalnum())

    @staticmethod
    def _sanitize_column_name(token):
        token = token.strip()
        token = token.replace("%", "pct")
        token = token.replace("°", "deg")
        token = re.sub(r"[()/\-]+", " ", token)
        token = re.sub(r"\s+", "_", token.strip())
        return token.lower()

    def _header_matches(self, cells):
        normalized_cells = {
            self._normalize_header_token(cell) for cell in cells if cell.strip()
        }
        matched = set()
        for semantic_name, aliases in self._HEADER_ALIASES.items():
            if normalized_cells.intersection(aliases):
                matched.add(semantic_name)
        return matched

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = "A"
        raw_units["charge"] = "Ah"
        raw_units["mass"] = "mg"
        raw_units["voltage"] = "V"
        raw_units["energy"] = "Wh"
        raw_units["time"] = "s"
        raw_units["capacity"] = "Ah"
        raw_units["resistance"] = "ohm"
        return raw_units

    def get_raw_limits(self):
        warnings.warn("raw limits have not been subject for testing yet")
        raw_limits = dict()
        raw_limits["current_hard"] = 0.1
        raw_limits["current_soft"] = 1.0
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 2.0
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    def loader(self, file_name, bad_steps=None, **kwargs):
        if bad_steps is not None:
            warnings.warn("bad_steps is not implemented yet for this instrument")

        self.number_of_header_lines = self._find_header_length()
        raw = self._load_pec_data()
        metadata = self._parse_metadata()
        cell_id = None
        if "cell_id" in raw.columns and not raw["cell_id"].empty:
            if raw["cell_id"].notna().any():
                cell_id = raw["cell_id"].dropna().iloc[0]

        data = Data()
        self.generate_fid()
        data.raw_data_files.append(self.fid)
        data.loaded_from = self.name
        data.channel_index = None
        data.creator = None
        data.schedule_file_name = None
        data.test_ID = metadata.get("test_id")
        data.test_name = metadata.get("test_regime_name")
        data.start_datetime = metadata.get("start_time")
        data.custom_info = {
            "pec_metadata": {
                "test_id": metadata.get("test_id"),
                "test_regime_name": metadata.get("test_regime_name"),
                "start_time": metadata.get("start_time"),
                "end_time": metadata.get("end_time"),
                "lot_id": metadata.get("lot_id"),
                "cell_id": cell_id,
            }
        }
        data.raw = raw
        data.raw_data_files_length.append(len(raw))
        data.summary = pd.DataFrame()

        data = self.identify_last_data_point(data)
        return self.validate(data)

    def validate(self, data):
        missing_must_have_columns = []

        for col in base_columns_float:
            if col in data.raw.columns:
                data.raw[col] = pd.to_numeric(data.raw[col], errors="coerce")
            elif col in [self.headers_normal[k] for k in self._MUST_HAVE_RAW_COLUMNS]:
                missing_must_have_columns.append(col)

        for col in base_columns_int:
            if col in data.raw.columns:
                # fillna before int cast — numpy int64 has no NaN representation
                data.raw[col] = pd.to_numeric(data.raw[col], errors="coerce").fillna(0).astype("int64")
            elif col in [self.headers_normal[k] for k in self._MUST_HAVE_RAW_COLUMNS]:
                missing_must_have_columns.append(col)

        if missing_must_have_columns:
            raise IOError(
                f"Missing needed columns: {missing_must_have_columns}\nAborting!"
            )

        # Drop rows where essential columns are NaN — unparseable rows (empty
        # trailing rows, footer lines) would otherwise cause RuntimeWarning from
        # numpy cumsum in make_summary/make_step_table.
        must_have_cols = [
            self.headers_normal[k]
            for k in self._MUST_HAVE_RAW_COLUMNS
            if self.headers_normal[k] in data.raw.columns
        ]
        n_before = len(data.raw)
        data.raw = data.raw.dropna(subset=must_have_cols).reset_index(drop=True)
        n_dropped = n_before - len(data.raw)
        if n_dropped:
            logging.warning(
                "pec_csv: dropped %d row(s) with NaN in essential columns", n_dropped
            )

        return data

    def _load_pec_data(self):
        df = pd.read_csv(
            self.temp_file_path,
            skiprows=self.number_of_header_lines,
            encoding="utf-8-sig",
        )
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        pec_columns = self._find_pec_columns(df.columns)
        self._rename_pec_columns(df, pec_columns)
        self._sanitize_non_cellpy_columns(df)
        self._convert_units(df, pec_columns)
        self._add_missing_columns(df)

        cycle_header = self.headers_normal.cycle_index_txt
        if cycle_header in df.columns and df[cycle_header].min() == 0:
            df[cycle_header] = df[cycle_header] + 1

        return df

    def _find_pec_columns(self, columns):
        matches = {}
        for column in columns:
            normalized = self._normalize_header_token(column)
            for semantic_name, aliases in self._HEADER_ALIASES.items():
                if normalized in aliases:
                    matches[semantic_name] = column
        return matches

    def _rename_pec_columns(self, df, pec_columns):
        renaming = {}
        for semantic_name, column in pec_columns.items():
            header_key = self._COLUMN_KEY_TO_CELLPY_HEADER.get(semantic_name)
            if header_key is None:
                continue
            renaming[column] = self.headers_normal[header_key]
        if renaming:
            df.rename(columns=renaming, inplace=True)

    def _sanitize_non_cellpy_columns(self, df):
        protected_columns = set(self._COLUMN_KEY_TO_CELLPY_HEADER.values())
        protected_columns = {self.headers_normal[key] for key in protected_columns}
        renaming = {}
        for column in df.columns:
            if column in protected_columns:
                continue
            sanitized = self._sanitize_column_name(column)
            if sanitized and sanitized != column:
                renaming[column] = sanitized
        if renaming:
            df.rename(columns=renaming, inplace=True)

    def _add_missing_columns(self, df):
        if self.headers_normal.data_point_txt not in df.columns:
            df.insert(0, self.headers_normal.data_point_txt, range(1, len(df) + 1))

        if self.headers_normal.sub_step_index_txt not in df.columns:
            df[self.headers_normal.sub_step_index_txt] = 0

        if self.headers_normal.sub_step_time_txt not in df.columns:
            df[self.headers_normal.sub_step_time_txt] = 0.0

    def _convert_units(self, df, pec_columns):
        datetime_header = self.headers_normal.datetime_txt
        if datetime_header in df.columns:
            df[datetime_header] = pd.to_datetime(df[datetime_header], errors="coerce")

        if "position_start_time" in df.columns:
            df["position_start_time"] = pd.to_datetime(
                df["position_start_time"], errors="coerce"
            )

        for semantic_name, original_header in pec_columns.items():
            header_key = self._COLUMN_KEY_TO_CELLPY_HEADER.get(semantic_name)
            if header_key is None:
                continue
            cellpy_header = self.headers_normal[header_key]
            if cellpy_header not in df.columns:
                continue

            if semantic_name in {"test_time", "step_time"}:
                df[cellpy_header] = self._convert_time_column(
                    df[cellpy_header], original_header
                )
                continue

            if semantic_name == "date_time":
                continue

            df[cellpy_header] = pd.to_numeric(df[cellpy_header], errors="coerce")
            factor = self._get_unit_factor(semantic_name, original_header)
            if factor != 1.0:
                df[cellpy_header] = df[cellpy_header] * factor

    def _convert_time_column(self, series, original_header):
        unit = self._extract_unit_label(original_header)
        normalized = self._normalize_header_token(unit)
        if normalized in self._TIME_FACTORS:
            values = pd.to_numeric(series, errors="coerce")
            return values * self._TIME_FACTORS[normalized]
        if normalized == "hoursinhhmmssxxx":
            return series.apply(self.timestamp_to_seconds)
        return pd.to_numeric(series, errors="coerce")

    def _get_unit_factor(self, semantic_name, header):
        unit = self._normalize_header_token(self._extract_unit_label(header))
        if not unit:
            return 1.0
        quantity_units = self._UNIT_FACTORS.get(semantic_name, {})
        return quantity_units.get(unit, 1.0)

    @staticmethod
    def _extract_unit_label(header):
        match = re.search(r"\((.*?)\)", header)
        if match is None:
            return ""
        return match.group(1).strip()

    def _parse_metadata(self):
        with open(
            self.temp_file_path, "r", encoding="utf-8-sig", errors="replace"
        ) as handle:
            header_lines = [next(handle) for _ in range(self.number_of_header_lines)]

        metadata = {}
        inside_comment_block = False
        for line in header_lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                inside_comment_block = not inside_comment_block
                continue

            if inside_comment_block or "," not in line:
                continue

            key, value = line.split(",", 1)
            key = self._sanitize_column_name(key.strip(": "))
            value = value.strip().strip(",")
            metadata[key] = value or None

        self.pec_settings = metadata

        parsed_metadata = {
            "test_id": metadata.get("test"),
            "test_regime_name": metadata.get("testregime_name"),
            "start_time": self._parse_datetime_or_none(metadata.get("start_time")),
            "end_time": self._parse_datetime_or_none(metadata.get("end_time")),
            "lot_id": metadata.get("lotid"),
        }
        return parsed_metadata

    @staticmethod
    def _parse_datetime_or_none(value):
        if not value:
            return None
        try:
            return parse(value)
        except (TypeError, ValueError):
            logging.debug("could not parse datetime metadata: %s", value)
            return None

    def _find_header_length(self):
        with open(
            self.temp_file_path, "r", encoding="utf-8-sig", errors="replace", newline=""
        ) as handle:
            for line_number, line in enumerate(handle, 1):
                cells = next(csv.reader([line], delimiter=self.pec_file_delimiter))
                matched = self._header_matches(cells)
                if len(matched) >= self._MIN_HEADER_MATCHES and (
                    self._REQUIRED_HEADER_FIELDS <= matched
                ):
                    return line_number - 1

        raise IOError(
            f"Could not detect PEC header row in {self.temp_file_path}. "
            "Expected a CSV table header containing the core PEC columns."
        )

    @staticmethod
    def timestamp_to_seconds(timestamp):
        """Convert `hh:mm:ss.xxx` values to seconds.

        PEC can export elapsed time in clock-format, and the hour field can exceed 24
        (or even 99, which breaks strptime's %H directive).
        """

        if pd.isna(timestamp):
            return pd.NA

        h, m, s = str(timestamp).split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)


if __name__ == "__main__":
    pass
