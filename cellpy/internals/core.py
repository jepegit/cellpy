"""This module contains div classes etc that are not really connected to cellpy."""

from dataclasses import dataclass
import fnmatch
import logging
import os
import pathlib
import shutil
import stat
import sys
import tempfile
import time
import warnings
from typing import (
    Any,
    Tuple,
    Dict,
    List,
    Union,
    TypeVar,
    Generator,
    Optional,
    Iterable,
    Callable,
    Type,
    cast,
)

# import fabric
from . import externals as externals
from cellpy.exceptions import UnderDefined
from cellpy.internals import otherpath
from cellpy.internals.otherpath import (
    URI_PREFIXES,
    IMPLEMENTED_PROTOCOLS,
    ENV_VAR_CELLPY_KEY_FILENAME,
    ENV_VAR_CELLPY_PASSWORD,
)

OtherPath = otherpath.get_otherpath_class()


def check_connection(
    p=None,
):
    """Check if the connection works.

    This is a helper function for cellpy v1.0 only and should be removed in later versions after
    the OtherPath class has been updated to work with python >= 3.12.

    Args:
        p (str, pathlib.Path or OtherPath, optional): The path to check. Defaults to prms.Paths.rawdatadir.

    """
    # Note: users run this function from helpers.py
    from pprint import pprint

    logging.debug("checking connection")
    if p is None:
        print("No path given. Checking rawdatadir from prms.")

        # need to import prms here to avoid circular imports:
        from cellpy import prms

        p = prms.Paths.rawdatadir

    # recreating the OtherPath object to OtherPath since core is imported in the top __init__.py
    # file resulting in isinstance(p, OtherPath) to be False
    p = OtherPath(p)
    logging.debug(f"p: {p}")

    print("\nCollecting connection information:")

    if not p.is_external:
        print(f"   - {p} is not external. Returning.")
        return {}

    info = {
        "is_external": p.is_external,
        "uri_prefix": p.uri_prefix,
        "location": p.location,
        "raw_path": p.raw_path,
        "full_path": p.full_path,
        "host": p.location,
    }

    uri_prefix = p.uri_prefix.replace("//", "")
    info["uri_prefix"] = uri_prefix
    if uri_prefix not in URI_PREFIXES:
        print(f"   - uri_prefix {uri_prefix} not recognized")
    if uri_prefix not in IMPLEMENTED_PROTOCOLS:
        print(f"   - uri_prefix {uri_prefix.replace(':', '')} not implemented yet")

    password = os.getenv(ENV_VAR_CELLPY_PASSWORD, None)
    info["password"] = "********" if password is not None else None

    key_filename = os.getenv(ENV_VAR_CELLPY_KEY_FILENAME, None)
    if password is None and key_filename is None:
        print(
            f"   - You must define either {ENV_VAR_CELLPY_PASSWORD} "
            f"or {ENV_VAR_CELLPY_KEY_FILENAME} environment variables."
        )
    if key_filename is not None:
        key_filename = pathlib.Path(key_filename).expanduser().resolve()
        info["key_filename"] = str(key_filename)
        if not pathlib.Path(key_filename).is_file():
            print(f"   - Could not find key file {key_filename}")
    else:
        print("   - Using password")

    for k, v in info.items():
        print(f" {k}: {v}")

    print("\nChecking connection:")
    connect_kwargs, host = p.connection_info()

    path_separator = "/"  # only supports unix-like systems
    with externals.fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
        try:
            t1 = time.perf_counter()
            try:
                sftp_conn = conn.sftp()
            except Exception as e:
                print(f"   - Could not connect to {host}")
                print(f"     {e}")
                return info

            print(f" connecting     [{time.perf_counter() - t1:.2f} seconds] OK")
            sftp_conn.chdir(p.raw_path)
            print(f" chdir          [{time.perf_counter() - t1:.2f} seconds] OK")
            files = [
                f"{p.raw_path}{path_separator}{f}"
                for f in sftp_conn.listdir()
                if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)
            ]
            print(f" listing files  [{time.perf_counter() - t1:.2f} seconds] OK")
            sub_dirs = [
                f"{p.raw_path}{path_separator}{f}"
                for f in sftp_conn.listdir()
                if stat.S_ISDIR(sftp_conn.stat(f).st_mode)
            ]
            n_files = len(files)
            n_sub_dirs = len(sub_dirs)
            info["number_of_files"] = n_files
            info["number_of_sub_directories"] = n_sub_dirs
            print(f" found {n_files} files and {n_sub_dirs} sub directories")

        except FileNotFoundError as e:
            print(
                f"   - FileNotFoundError: Could not perform directory listing in {p.raw_path} on {host}." f"\n     {e}"
            )

    return info


def _check():
    print("Testing OtherPath-connection")
    # info = check_connection()
    p0 = "scp://odin/home/jepe@ad.ife.no/projects"
    # info = check_connection(p0)
    p1 = "scp://odin/home/jepe@ad.ife.no/this-folder-does-not-exist"
    # info = check_connection(p1)
    p2 = pathlib.Path(".").resolve()
    info = check_connection(p2)


if __name__ == "__main__":
    print("------------------")
    logging.debug("testing OtherPath")
    _check()
