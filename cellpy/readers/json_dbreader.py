import json
import logging
import pathlib
import re
from typing import Optional, Dict, Mapping
from cellpy.readers.core import BaseDbReader, PagesDictBase
from cellpy.readers import core
from cellpy.parameters.internal_settings import get_headers_journal, cellpy_units


hdr_journal = get_headers_journal()


# TODO: use journal headers in stead of this
PagesDict = PagesDictBase


class BaseJSONReader(BaseDbReader):
    def __init__(
        self, json_file: str | None | pathlib.Path = None, store_raw_data: bool = False
    ):
        self.json_file = json_file
        if store_raw_data:
            self.json_data = self._load_raw_data()
        else:
            self.json_data = None
        self.data = self._load_to_pandas_dataframe()

    def _load_raw_data(self):
        with open(self.json_file, "r") as f:
            return json.load(f)

    @property
    def db_file(self) -> str:
        return self.json_file

    @db_file.setter
    def db_file(self, value: str | None | pathlib.Path):
        self.json_file = value

    # TODO: from_batch needs to return a dictionary - maybe using pandas is not the correct approach?

    def _load_to_pandas_dataframe(self):
        import pandas as pd

        return pd.read_json(self.json_file)

    @property
    def raw_pages_dict(self) -> dict:
        return self.data.to_dict(orient="list")


class BatBaseJSONReader(BaseJSONReader):
    """
    The cellpy journal uses the following headers:
        - filename: str = "filename"
        - file_name_indicator: str = "file_name_indicator"
        - mass: str = "mass"
        - total_mass: str = "total_mass"
        - loading: str = "loading"
        - area: str = "area"
        - nom_cap: str = "nom_cap"
        - experiment: str = "experiment"
        - fixed: str = "fixed"
        - label: str = "label"
        - cell_type: str = "cell_type"
        - instrument: str = "instrument"
        - model: str = "model"
        - raw_file_names: str = "raw_file_names"
        - cellpy_file_name: str = "cellpy_file_name"
        - group: str = "group"
        - sub_group: str = "sub_group"
        - group_label: str = "group_label"
        - comment: str = "comment"
        - argument: str = "argument"
        - id_key: str = "id_key"
        - nom_cap_specifics: str = "nom_cap_specifics"
        - selected: str = "selected"
    """

    _version = "1.0.0"
    _key_translator = dict(
        filename="Test Name",
        id_key="ID Key",
        argument=None,
        mass="Mass (mg)",
        total_mass="Total Mass (mg)",
        nom_cap_specifics="Unit",
        file_name_indicator="Test Name",
        loading="Loading (mg/cm2)",
        nom_cap="Nominal Capacity",
        area="Area (cm2)",
        experiment=None,
        fixed=None,
        label=None,
        cell_type="Cell Type",  # TODO: fix in batbase
        instrument="Instrument",
        comment=None,  # TODO: add to batbase
        group="Group",  # TODO: add to batbase
        raw_file_names=None,
        cellpy_file_name=None,
    )

    _property_mapper = dict(
        mass="mass",
        total_mass="mass",
        area="area",
        # loading = "loading",
        nom_cap="nominal_capacity",
        length="length",
        volume="volume",
        temperature="temperature",
        pressure="pressure",
    )

    _nominal_capacity_unit_key = "Unit"
    _nominal_capacity_unit_regex = r"\[([^]]+)\]"

    def _convert_nominal_capacity_unit(self, info: str, value: float) -> float:
        try:
            unit = re.search(self._nominal_capacity_unit_regex, info).group(1)
            unit = self._clean_unit(unit)
            value = core.Q(value, unit).to(cellpy_units["nominal_capacity"]).m
        except Exception as e:
            logging.error(f"Error converting nominal capacity unit: {e}")
            logging.error(f"Using original value: {value}")
        return value

    def _specific_fixer(self, x: str) -> str:
        x = x.lower()
        specific = x.split(" ")[0]
        if specific == "null":
            return None
        if specific == "specific":
            return "gravimetric"
        return specific

    @staticmethod
    def _clean_unit(unit: str) -> str:
        unit = unit.replace("m2", "m**2")
        unit = unit.replace("m3", "m**3")
        return unit

    def _extract_unit_from_header(self, header_name: str) -> Optional[str]:
        """Extract unit from header name like 'Total Mass (mg)' -> 'mg'."""
        if not header_name:
            return None
        # Match pattern: "Header Name (unit)"
        match = re.search(r"\(([^)]+)\)", header_name)
        if match:
            unit = match.group(1).strip()
            unit = self._clean_unit(unit)
            return unit
        return None

    def __init__(
        self,
        json_file: str | None | pathlib.Path = None,
        store_raw_data: bool = False,
        **kwargs,
    ):
        instrument = kwargs.pop("instrument", None)
        super().__init__(json_file, store_raw_data, **kwargs)
        # TODO: add to batbase
        self._value_fixers = dict(
            nom_cap_specifics=self._specific_fixer,
            cell_type=lambda x: "anode" if x == "hci" else "standard",
            loading=lambda x: float(x) if x != "null" else None,
            instrument=lambda x: f"{instrument}" if instrument is not None else x,
        )
        self._pages_dict = {}

    def _get_number_of_cells(self) -> int:
        return len(self.data)

    def _get_unit_for_key(self, cellpy_key: str) -> Optional[str]:
        """Get the unit for a given cellpy_key by extracting it from the corresponding JSON key.

        The cellpy library uses the following units as default:
            - current: str = "A"
            - charge: str = "mAh"
            - voltage: str = "V"
            - time: str = "sec"
            - resistance: str = "ohm"
            - power: str = "W"
            - energy: str = "Wh"
            - frequency: str = "hz"
            - mass: str = "mg"  # for mass
            - nominal_capacity: str = "mAh/g"
            - specific_gravimetric: str = "g"  # g in specific capacity etc
            - specific_areal: str = "cm**2"  # m2 in specific capacity etc
            - specific_volumetric: str = "cm**3"  # m3 in specific capacity etc
            - length: str = "cm"
            - area: str = "cm**2"
            - volume: str = "cm**3"
            - temperature: str = "C"
            - pressure: str = "bar"

        Args:
            cellpy_key: The cellpy key (e.g., 'mass', 'total_mass')

        Returns:
            The unit string (e.g., 'mg') if found, None otherwise.
        """
        json_key = self._key_translator.get(cellpy_key)

        if json_key is None:
            return None
        return self._extract_unit_from_header(json_key)

    @property
    def units_dict(self) -> Dict[str, Optional[str]]:
        """Get units for all cellpy keys, following the same structure as pages_dict.

        Returns:
            Dictionary mapping cellpy_key -> unit string (or None if no unit found).
        """
        _units_dict = {}
        for cellpy_key in self._key_translator.keys():
            _units_dict[cellpy_key] = self._get_unit_for_key(cellpy_key)
        return _units_dict

    def get_conversion_factor(self, value, old_unit, property_name):
        property = self._property_mapper.get(property_name)
        if property is None:
            return 1
        new_unit = cellpy_units[property]
        value = core.Q(1, old_unit)
        value = value.to(new_unit)
        return value.m

    def get_unit_from_header(
        self,
        header: Optional[str] = None,
    ) -> str:
        """Parse units from headers (keys) in the JSON data.

        Headers are expected to be in the format "Header Name (unit)",
        for example "Total Mass (mg)" or "Area (cm2)".
        """
        # exposing internal method for unit extraction
        return self._extract_unit_from_header(header)

    def from_batch(
        self,
        batch_name: str | None = None,
        project_name: str | None = None,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        raise NotImplementedError("This method is not implemented for this reader")

    def _create_pages_dict(self) -> PagesDict:
        _pages_dict = dict()
        _number_of_cells = self._get_number_of_cells()

        # fixing keys:
        for cellpy_key, json_key in self._key_translator.items():
            if json_key is not None:
                _pages_dict[hdr_journal[cellpy_key]] = self.raw_pages_dict[json_key]
                unit = self._extract_unit_from_header(json_key)
            elif cellpy_key in ["raw_file_names", "cellpy_file_name"]:
                _pages_dict[hdr_journal[cellpy_key]] = []
            else:
                _pages_dict[hdr_journal[cellpy_key]] = [None] * _number_of_cells

        # fixing values:
        for key, fixer in self._value_fixers.items():
            if key in _pages_dict:
                _pages_dict[hdr_journal[key]] = [
                    fixer(x) for x in _pages_dict[hdr_journal[key]]
                ]

        # extract nominal capacity unit and convert to cellpy units if available
        if self._nominal_capacity_unit_key is not None:
            info_list = self.raw_pages_dict[self._nominal_capacity_unit_key]
            nom_cap_values = _pages_dict[hdr_journal["nom_cap"]]
            new_nom_cap_values = []
            for info, value in zip(info_list, nom_cap_values):
                new_nom_cap_values.append(
                    self._convert_nominal_capacity_unit(info, value)
                )
            _pages_dict[hdr_journal["nom_cap"]] = new_nom_cap_values

        # fixing general units:
        for cellpy_key, unit in self.units_dict.items():
            if unit is not None:
                conversion_factor = self.get_conversion_factor(1, unit, cellpy_key)
                values = _pages_dict[hdr_journal[cellpy_key]]
                new_values = []
                for value in values:
                    if value is not None:
                        new_value = value * conversion_factor
                    new_values.append(new_value)
                _pages_dict[hdr_journal[cellpy_key]] = new_values
        return _pages_dict

    @property
    def pages_dict(self) -> PagesDict:
        if not self._pages_dict:
            self._pages_dict = self._create_pages_dict()
        return self._pages_dict

    @pages_dict.setter
    def pages_dict(self, value: PagesDict):
        self._pages_dict = value


class CustomJSONReader(BaseJSONReader):
    """JSON reader with configurable column mapping for arbitrary JSON schemas.

    Use this when your JSON has different column names than the cellpy journal.
    Provide a column_map from your JSON key names to cellpy journal key names
    (e.g. {"cell_id": "filename", "mass_mg": "mass"}). Unmapped journal columns
    are filled with None or empty lists (raw_file_names, cellpy_file_name).
    """

    def __init__(
        self,
        json_file: str | None | pathlib.Path = None,
        column_map: Optional[Mapping[str, str]] = None,
        store_raw_data: bool = False,
        **kwargs,
    ):
        """
        Args:
            json_file: Path to the JSON file (pandas-readable, e.g. dict of lists).
            column_map: Map from JSON column name to cellpy journal key name
                (e.g. {"Test ID": "filename", "Mass (mg)": "mass"}).
                Cellpy keys are: filename, file_name_indicator, mass, total_mass,
                loading, area, nom_cap, experiment, fixed, label, cell_type,
                instrument, raw_file_names, cellpy_file_name, group, etc.
            store_raw_data: If True, load and keep raw JSON in memory.
        """
        super().__init__(json_file, store_raw_data, **kwargs)
        self.column_map = dict(column_map) if column_map else {}
        self._pages_dict = {}

    def from_batch(
        self,
        batch_name: str | None = None,
        project_name: str | None = None,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        raise NotImplementedError("This method is not implemented for this reader")

    def _create_pages_dict(self) -> PagesDict:
        raw = self.raw_pages_dict
        n = len(next(iter(raw.values()))) if raw else 0
        inverse_map = {v: k for k, v in self.column_map.items()}

        _pages_dict = {}
        for cellpy_key in [
            "filename",
            "file_name_indicator",
            "mass",
            "total_mass",
            "loading",
            "area",
            "nom_cap",
            "experiment",
            "fixed",
            "label",
            "cell_type",
            "instrument",
            "comment",
            "group",
            "id_key",
            "nom_cap_specifics",
            "argument",
        ]:
            json_key = inverse_map.get(cellpy_key)
            if json_key is not None and json_key in raw:
                val = raw[json_key]
                if not isinstance(val, list):
                    val = [val] * n if n else []
                _pages_dict[hdr_journal[cellpy_key]] = val
            else:
                _pages_dict[hdr_journal[cellpy_key]] = [None] * n

        _pages_dict[hdr_journal["raw_file_names"]] = []
        _pages_dict[hdr_journal["cellpy_file_name"]] = []

        fi = _pages_dict.get(hdr_journal["file_name_indicator"])
        fn = _pages_dict.get(hdr_journal["filename"])
        if fn and (not fi or all(x is None for x in fi)):
            _pages_dict[hdr_journal["file_name_indicator"]] = fn

        return _pages_dict

    @property
    def pages_dict(self) -> PagesDict:
        if not self._pages_dict:
            self._pages_dict = self._create_pages_dict()
        return self._pages_dict

    @pages_dict.setter
    def pages_dict(self, value: PagesDict):
        self._pages_dict = value


if __name__ == "__main__":
    import pandas as pd

    from pprint import pprint

    pd.set_option("display.max_columns", None)
    print(f"pandas version: {pd.__version__}")

    local_dir = pathlib.Path(__file__).parent.parent.parent / "local"
    json_file = local_dir / "cellpy_journal_table.json"
    reader = BatBaseJSONReader(json_file, store_raw_data=True)
    print(80 * "=")
    pprint(reader.pages_dict)
