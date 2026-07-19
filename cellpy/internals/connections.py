"""Connection helpers and the public ``OtherPath`` export."""

from __future__ import annotations

import logging
import os
import pathlib
import time
from typing import Any, Dict, Optional, Union

from cellpy.exceptions import UnderDefined
from cellpy.internals.otherpath import (
    ENV_VAR_CELLPY_KEY_FILENAME,
    ENV_VAR_CELLPY_PASSWORD,
    IMPLEMENTED_PROTOCOLS,
    OtherPath,
    URI_PREFIXES,
    get_otherpath_class,
)

__all__ = [
    "OtherPath",
    "URI_PREFIXES",
    "IMPLEMENTED_PROTOCOLS",
    "ENV_VAR_CELLPY_KEY_FILENAME",
    "ENV_VAR_CELLPY_PASSWORD",
    "check_connection",
    "get_otherpath_class",
]


def check_connection(
    p: Optional[Union[str, pathlib.Path, OtherPath]] = None,
) -> Dict[str, Any]:
    """Probe a remote ``OtherPath`` (or configured ``rawdatadir``).

    Uses UPath/fsspec instead of Fabric. Intended as a user-facing diagnostic.
    """
    logging.debug("checking connection")
    if p is None:
        print("No path given. Checking rawdatadir from prms.")
        import cellpy.config as config

        p = config.paths.rawdatadir

    # Recreate so isinstance checks work even if the object crossed import boundaries.
    p = OtherPath(p)
    logging.debug("p: %s", p)

    print("\nCollecting connection information:")

    if not p.is_external:
        print(f"   - {p} is not external. Returning.")
        return {}

    info: Dict[str, Any] = {
        "is_external": p.is_external,
        "uri_prefix": p.uri_prefix,
        "location": p.location,
        "raw_path": p.raw_path,
        "full_path": p.full_path,
        "host": p.location,
    }

    scheme = p.uri_prefix.replace("//", "")
    info["uri_prefix"] = scheme
    if scheme not in URI_PREFIXES:
        print(f"   - uri_prefix {scheme} not recognized")
    if scheme not in IMPLEMENTED_PROTOCOLS:
        print(f"   - uri_prefix {scheme.replace(':', '')} not implemented yet")

    from cellpy.config import credentials

    password = credentials.get_password()
    info["password"] = "********" if password is not None else None

    key_filename = credentials.get_key_filename()
    if password is None and key_filename is None:
        print(
            f"   - You must define either {ENV_VAR_CELLPY_PASSWORD} "
            f"or {ENV_VAR_CELLPY_KEY_FILENAME} environment variables."
        )
    if key_filename is not None:
        key_path = pathlib.Path(key_filename).expanduser().resolve()
        info["key_filename"] = str(key_path)
        if not key_path.is_file():
            print(f"   - Could not find key file {key_path}")
    else:
        print("   - Using password")

    for key, value in info.items():
        print(f" {key}: {value}")

    print("\nChecking connection:")
    t0 = time.perf_counter()
    try:
        connect_kwargs, host = p.connection_info()
        info["connect_kwargs_keys"] = sorted(connect_kwargs)
        exists = p.exists()
        print(f" exists()       [{time.perf_counter() - t0:.2f} seconds] {'OK' if exists else 'MISSING'}")
        info["exists"] = exists
        if exists and p.is_dir():
            children = list(p.listdir(levels=0))
            n_files = sum(1 for c in children if c.is_file())
            n_dirs = sum(1 for c in children if c.is_dir())
            info["number_of_files"] = n_files
            info["number_of_sub_directories"] = n_dirs
            print(f" listing        [{time.perf_counter() - t0:.2f} seconds] OK")
            print(f" found {n_files} files and {n_dirs} sub directories")
        elif not exists:
            print(f"   - Path does not exist on {host}: {p.raw_path}")
    except UnderDefined as exc:
        print(f"   - UnderDefined: {exc}")
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should surface any failure
        print(f"   - Could not connect to {p.location}")
        print(f"     {exc}")

    return info
