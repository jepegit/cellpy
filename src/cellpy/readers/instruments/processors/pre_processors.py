"""Pre-processing methods for instrument loaders.

All methods must implement the following parameters/arguments::

    - filename: Union[str, pathlib.Path]
    - *args and **kwargs: Any additional parameters/arguments should be supported.

All methods should return None (i.e. nothing).

"""

import logging
import pathlib
import tempfile
import uuid
from typing import Union


def remove_empty_lines(
    filename: Union[str, pathlib.Path], *args, **kwargs
) -> pathlib.Path:
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
    logging.debug(f"args: {args}, kwargs: {kwargs}")
    logging.debug(f"filename: {filename}")

    filename = pathlib.Path(filename)

    if not filename.is_file():
        raise IOError(f"Could not find the file ({filename})")
    out_file_name = filename.parent / (str(uuid.uuid4()) + ".txt")

    # Encoding is stated, not left to the platform default. Without it this
    # read used cp1252 on Windows and UTF-8 on Linux, so a Maccor file carrying
    # a stray non-UTF-8 byte — 0xFF in maccor_002.txt's Description line, which
    # is real vendor output — loaded on Windows and raised a bare
    # UnicodeDecodeError on Linux. `errors="replace"` keeps such a file
    # loadable: this pre-processor only strips blank lines, so it has no reason
    # to be the thing that rejects a file over one undecodable byte in a
    # header comment.
    with open(filename, "r", encoding="utf-8", errors="replace") as file:
        with open(out_file_name, "w", encoding="utf-8") as out_file:
            for line in file.readlines():
                if line.strip():
                    out_file.write(f"{line.strip()}\n")

    return out_file_name
