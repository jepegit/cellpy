from typing import Any
from cellpy.readers.core import BaseDbReader
import json


class BaseJSONReader(BaseDbReader):
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.data = self.load_data()

    def _load_raw_data(self):
        with open(self.json_file, "r") as f:
            return json.load(f)

    def load_data(self):
        return pd.read_json(self.json_file)


class BattBaseJSONReader(BaseJSONReader):
    _version = "1.0.0"

    def from_batch(
        self,
        batch_name: str | None = None,
        project_name: str | None = None,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        raise NotImplementedError("This method is not implemented for this reader")


if __name__ == "__main__":
    from pathlib import Path
    import pandas as pd

    pd.set_option("display.max_columns", None)

    local_dir = Path(__file__).parent.parent.parent / "local"
    json_file = local_dir / "cellpy_journal_table.json"
    print(json_file.exists())
    reader = BattBaseJSONReader(json_file)
    print(reader.from_batch())
