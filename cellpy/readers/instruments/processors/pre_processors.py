"""Pre-processing methods for instrument loaders.

All methods must implement the following parameters/arguments:
    filename: Union[str, pathlib.Path], *args: str, **kwargs: str

All methods should return None (i.e. nothing).

"""

import logging
import pathlib
import tempfile
import uuid
from typing import Union


def remove_empty_lines(filename: Union[str, pathlib.Path], *args: str, **kwargs: str) -> pathlib.Path:
    """Remove all the empty lines in the file.

    The method saves to the same name as the original file, so it is recommended to work on a temporary
    copy of the file instead of the original file.

    Args:
        filename: path to the file.
        *args: None supported.
        **kwargs: None supported.

    Returns:
        pathlib.Path of modified file
    """
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug(f"args: {args}, kwargs: {kwargs}")
    logging.debug(f"filename: {filename}")

    filename = pathlib.Path(filename)

    if not filename.is_file():
        raise IOError(f"Could not find the file ({filename})")
    out_file_name = filename.parent / (str(uuid.uuid4()) + ".txt")

    with open(filename, "r+") as file:
        with open(out_file_name, "w") as out_file:
            for line in file.readlines():

                if line.strip():
                    out_file.write(f"{line.strip()}\n")

    return out_file_name
