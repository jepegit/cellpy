"""HDF5 store key validation for cellpy-files."""

from __future__ import annotations

import logging


def check_keys_in_cellpy_file(meta_dir, parent_level, raw_dir, store, summary_dir):
    required_keys = [raw_dir, summary_dir, meta_dir]
    required_keys = ["/" + parent_level + _ for _ in required_keys]

    for key in required_keys:
        if key not in store.keys():
            logging.info(
                f"This cellpy-file is not good enough - "
                f"at least one key is missing: {key}"
            )
            raise Exception(
                f"OH MY GOD! At least one crucial key is missing {key}!"
            )
    logging.debug(f"Keys in current cellpy-file: {store.keys()}")
