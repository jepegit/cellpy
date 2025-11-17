import json
import pathlib
from cellpy.readers.core import BaseDbReader, PagesDictBase
from cellpy.parameters.internal_settings import get_headers_journal


hdr_journal = get_headers_journal()


# TODO: use journal headers in stead of this
PagesDict = PagesDictBase

class BaseJSONReader(BaseDbReader):
    
    def __init__(self, json_file: str | None | pathlib.Path = None, store_raw_data: bool = False):
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
        return self.data.to_dict(orient='list')


class BatBaseJSONReader(BaseJSONReader):
    _version = "1.0.0"
    _key_translator = dict(
            filename = "Test Name",
            id_key = "ID Key",
            argument= None,
            mass= "Mass (mg)",
            total_mass = "Total Mass (mg)",
            nom_cap_specifics = "Unit",
            file_name_indicator = "Test Name",
            loading = "Loading (mg/cm2)",
            nom_cap = "Nominal Capacity",
            area = "Area (cm2)",
            experiment = None,
            fixed = None,
            label = None,
            cell_type = "Cell Type",  # TODO: fix in batbase
            instrument = "Instrument",
            comment = None,  # TODO: add to batbase
            group = "Group",  # TODO: add to batbase
            raw_file_names = None,
            cellpy_file_name = None,
        )

    def _specific_fixer(self, x: str) -> str:
        x = x.lower()
        specific = x.split(" ")[0]
        if specific == "null": 
            return None
        if specific == "specific": 
            return "gravimetric"
        return specific

    def __init__(self, json_file: str|None|pathlib.Path = None, store_raw_data: bool = False, **kwargs):
        super().__init__(json_file, store_raw_data, **kwargs)
        # TODO: add to batbase
        self._value_fixers = dict(
            nom_cap_specifics = self._specific_fixer,
            cell_type = lambda x: "anode" if x == "hci" else "standard",
            loading = lambda x: float(x) if x != "null" else None,
        )


    def _get_number_of_cells(self) -> int:
        return len(self.data)

    def from_batch(
        self,
        batch_name: str | None = None,
        project_name: str | None = None,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        raise NotImplementedError("This method is not implemented for this reader")

    @property
    def pages_dict(self) -> PagesDict:  # TODO: rename to pages_dict
        _pages_dict = dict()
        _number_of_cells = self._get_number_of_cells()

        # fixing keys:
        for cellpy_key, json_key in self._key_translator.items():
            if json_key is not None:
                _pages_dict[cellpy_key] = self.raw_pages_dict[json_key]
            elif cellpy_key in [hdr_journal["raw_file_names"], hdr_journal["cellpy_file_name"]]:
                _pages_dict[cellpy_key] = []
            else:
                print(f"cellpy_key: {cellpy_key}")
                _pages_dict[cellpy_key] = [None] * _number_of_cells

        # fixing values:
        for key, fixer in self._value_fixers.items():
            if key in _pages_dict:
                _pages_dict[key] = [fixer(x) for x in _pages_dict[key]]
        return _pages_dict


if __name__ == "__main__":
    import pandas as pd

    from pprint import pprint

    pd.set_option("display.max_columns", None)
    print(f"pandas version: {pd.__version__}")

    local_dir = pathlib.Path(__file__).parent.parent.parent / "local"
    json_file = local_dir / "cellpy_journal_table.json"
    print(json_file.exists())
    reader = BatBaseJSONReader(json_file, store_raw_data=True)
    print(80 * "=")
    pprint(reader.json_data)
    print(80 * "=")
    print(reader.data)
    print(80 * "=")
    pprint(reader.raw_pages_dict)
    print(80 * "=")
    pprint(reader.pages_dict)
    print(80 * "=")



