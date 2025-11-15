from typing import Any
from cellpy.readers.core import BaseDbReader, PagesDictBase
import json


# TODO: use journal headers in stead of this
PagesDict = PagesDictBase

class BaseJSONReader(BaseDbReader):
    """

    Example:

    list_of_dicts = [
    {'name': 'Alice', 'age': 30, 'city': 'New York'},
    {'name': 'Bob', 'age': 24, 'city': 'London'},
    {'name': 'Charlie', 'age': 35, 'city': 'Paris'}
    ]

    if list_of_dicts: # Ensure the list is not empty
        keys = list_of_dicts[0].keys()
        dict_of_lists = {key: [d[key] for d in list_of_dicts] for key in keys}
        print(dict_of_lists)
    else:
        print({})


    Example:

    import pandas as pd

    list_of_dicts = [
        {'name': 'Alice', 'age': 30, 'city': 'New York'},
        {'name': 'Bob', 'age': 24, 'city': 'London', 'occupation': 'Engineer'},
        {'name': 'Charlie', 'age': 35, 'city': 'Paris'}
    ]

    df = pd.DataFrame(list_of_dicts)
    dict_of_lists = df.to_dict(orient='list')
    print(dict_of_lists)

    """


    def __init__(self, json_file: str, store_raw_data: bool = False):
        self.json_file = json_file
        if store_raw_data:
            self.json_data = self._load_raw_data()
        else:
            self.json_data = None
        self.data = self._load_to_pandas_dataframe()

    def _load_raw_data(self):
        with open(self.json_file, "r") as f:
            return json.load(f)

    # TODO: from_batch needs to return a dictionary - maybe using pandas is not the correct approach?

    def _load_to_pandas_dataframe(self):
        return pd.read_json(self.json_file)

    @property
    def raw_info_dict(self) -> dict:
        return self.data.to_dict(orient='list')


class BattBaseJSONReader(BaseJSONReader):
    _version = "1.0.0"
    _key_translator = dict(
            filename = "Test Name",
            id_key = None,
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
            instrument = "Channel",  # TODO: fix in batbase
            comment = None,  # TODO: add to batbase
            group = None,  # TODO: add to batbase
            raw_file_names = None,
            cellpy_file_name = None,
        )
    def __init__(self, json_file: str, store_raw_data: bool = False):
        super().__init__(json_file, store_raw_data)
        # TODO: add to batbase
        self._instrument_translator = dict(
            Arbin01 = "arbin_res",
            Arbin02 = "arbin_res",
            Arbin03 = "arbin_res",
            Arbin04 = "arbin_res",
            Arbin05 = "arbin_sql_h5",
            Arbin06 = "arbin_sql_h5",
            other = "other",
        )
        self._value_fixers = dict(
            nom_cap_specifics = lambda x: x.lower(),
            cell_type = lambda x: "anode" if x == "hci" else "cathode",
            instrument = self._translate_instrument,
        )

    def _translate_instrument(self, instrument: str) -> str:
        for key, value in self._instrument_translator.items():
            if instrument.startswith(key):
                print(f"translating {instrument} to {value}")
                return value
        return "other"

    def from_batch(
        self,
        batch_name: str | None = None,
        project_name: str | None = None,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        raise NotImplementedError("This method is not implemented for this reader")

    @property
    def info_dict(self) -> PagesDict:  # TODO: rename to pages_dict
        info_dict = dict()

        # fixing keys:
        for cellpy_key, json_key in self._key_translator.items():
            if json_key is not None:
                info_dict[cellpy_key] = self.raw_info_dict[json_key]
            else:
                info_dict[cellpy_key] = []

        # fixing values:
        for key, fixer in self._value_fixers.items():
            if key in info_dict:
                info_dict[key] = [fixer(x) for x in info_dict[key]]
        return info_dict


if __name__ == "__main__":
    from pathlib import Path
    import pandas as pd

    from pprint import pprint

    pd.set_option("display.max_columns", None)
    print(f"pandas version: {pd.__version__}")

    local_dir = Path(__file__).parent.parent.parent / "local"
    json_file = local_dir / "cellpy_journal_table.json"
    print(json_file.exists())
    reader = BattBaseJSONReader(json_file, store_raw_data=True)
    print(80 * "=")
    pprint(reader.json_data)
    print(80 * "=")
    print(reader.data)
    print(80 * "=")
    pprint(reader.info_dict)
    print(80 * "=")



