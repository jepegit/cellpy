"""Path-like objects that can point at local or remote (ssh/sftp) locations.

``OtherPath`` is a thin compatibility wrapper around ``upath.UPath``. Remote
reads use fsspec/Paramiko; callers that need a local file should use
``copy()`` (or the cellpy load seams that call it).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import os
import pathlib
import shutil
import tempfile
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from upath import UPath

from cellpy.exceptions import UnderDefined


def _as_epoch_seconds(value: Any) -> int:
    """Normalize fsspec/paramiko timestamps to int epoch seconds."""
    if value is None:
        return 0
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

URI_PREFIXES = ["ssh:", "sftp:", "scp:", "http:", "https:", "ftp:", "ftps:", "smb:"]
IMPLEMENTED_PROTOCOLS = ["ssh:", "sftp:", "scp:"]
# Map cellpy/product schemes to the fsspec protocol UPath understands.
_UPATH_PROTOCOL_ALIASES = {
    "scp": "sftp",
}
ENV_VAR_CELLPY_KEY_FILENAME = "CELLPY_KEY_FILENAME"
ENV_VAR_CELLPY_PASSWORD = "CELLPY_PASSWORD"


@dataclass
class ExternalStatResult:
    """Minimal ``os.stat_result`` stand-in for remote paths."""

    st_size: int = 0
    st_mtime: int = 0
    st_atime: int = 0
    st_ctime: Optional[int] = None


def _clean_up_original_path_string(path_string: Any) -> str:
    if path_string is None:
        return "."
    if isinstance(path_string, OtherPath):
        return path_string.original
    if isinstance(path_string, UPath):
        return str(path_string)
    if isinstance(path_string, pathlib.Path):
        if isinstance(path_string, pathlib.WindowsPath):
            parts = list(path_string.parts)
            if not parts:
                parts = [""]
            parts[0] = parts[0].replace("\\", "")
            return "/".join(parts)
        if isinstance(path_string, pathlib.PosixPath):
            return "/".join(path_string.parts)
        return path_string.as_posix()
    return str(path_string) if path_string else "."


def _check_external(path_string: str) -> Tuple[str, bool, str, str]:
    """Parse cellpy URI metadata from a path string.

    Returns:
        Tuple of ``(raw_path, is_external, uri_prefix, location)``.
    """
    is_external = False
    location = ""
    uri_prefix = ""
    for prefix in URI_PREFIXES:
        if path_string.startswith(prefix):
            rest = path_string.replace(prefix, "", 1).lstrip("/")
            is_external = True
            uri_prefix = prefix + "//"
            location, *parts = rest.split("/")
            path_string = "/" + "/".join(parts)
            break
    path_string = path_string or "."
    path_string = path_string.replace("\\", "/").replace("//", "/")
    return path_string, is_external, uri_prefix, location


def _scheme_from_uri_prefix(uri_prefix: str) -> str:
    return uri_prefix.replace("://", "").replace(":", "")


def _credentials_from_env(*, testing: bool = False) -> Dict[str, Any]:
    """Build Paramiko/fsspec ``storage_options`` from cellpy env vars."""
    password = os.getenv(ENV_VAR_CELLPY_PASSWORD, None)
    key_filename = os.getenv(ENV_VAR_CELLPY_KEY_FILENAME, None)
    if password is None and key_filename is None:
        raise UnderDefined(
            f"You must define either {ENV_VAR_CELLPY_PASSWORD} "
            f"or {ENV_VAR_CELLPY_KEY_FILENAME} environment variables."
        )
    if key_filename is not None:
        key_path = pathlib.Path(key_filename).expanduser().resolve()
        if not testing and not key_path.is_file():
            raise FileNotFoundError(f"Could not find key file {key_path}")
        return {"key_filename": str(key_path)}
    return {"password": password}


def _upath_url(uri_prefix: str, location: str, raw_path: str) -> str:
    """Build a UPath-compatible URL (``scp`` → ``sftp``)."""
    scheme = _scheme_from_uri_prefix(uri_prefix)
    scheme = _UPATH_PROTOCOL_ALIASES.get(scheme, scheme)
    path = raw_path if raw_path.startswith("/") else f"/{raw_path}"
    return f"{scheme}://{location}{path}"


class OtherPath:
    """Path-like wrapper around ``UPath`` preserving the cellpy remote API."""

    def __init__(self, path: Any = ".", **storage_options: Any):
        if isinstance(path, OtherPath):
            path = path.original
        original = _clean_up_original_path_string(path)
        raw_path, is_external, uri_prefix, location = _check_external(original)

        if is_external:
            scheme = _scheme_from_uri_prefix(uri_prefix)
            protocol_key = f"{scheme}:"
            if protocol_key not in URI_PREFIXES:
                raise ValueError(f"uri_prefix {protocol_key} not recognized")
            if protocol_key not in IMPLEMENTED_PROTOCOLS:
                raise ValueError(
                    f"Remote scheme {scheme!r} is not supported by cellpy. "
                    f"Supported schemes: "
                    f"{', '.join(p.replace(':', '') for p in IMPLEMENTED_PROTOCOLS)}."
                )
            upath_url = _upath_url(uri_prefix, location, raw_path)
            self._upath = UPath(upath_url, **storage_options)
        else:
            # Keep Windows drive letters and relative paths as local paths.
            local = original.replace("\\", "/") if os.name == "nt" else original
            self._upath = UPath(local, **storage_options)

        self._original = original
        self._raw_other_path = raw_path
        self._is_external = is_external
        self._uri_prefix = uri_prefix
        self._location = location
        self._extra_storage_options = dict(storage_options)

    # --- cellpy metadata -------------------------------------------------

    @property
    def original(self) -> str:
        return self._original

    @property
    def raw_path(self) -> str:
        return self._raw_other_path

    @property
    def full_path(self) -> str:
        if self.is_external:
            return f"{self._uri_prefix}{self._location}{self._raw_other_path}"
        return self._original

    @property
    def is_external(self) -> bool:
        return self._is_external

    @property
    def uri_prefix(self) -> str:
        return self._uri_prefix

    @property
    def location(self) -> str:
        return self._location

    @property
    def pathlike_location(self) -> "OtherPath":
        if self.is_external:
            return OtherPath(f"{self._uri_prefix}{self._location}")
        drive = getattr(self._upath, "drive", "") or ""
        return OtherPath(drive)

    # --- pathlib-like surface --------------------------------------------

    def __str__(self) -> str:
        if self.is_external:
            return self._original
        return str(self._upath)

    def __repr__(self) -> str:
        return f"OtherPath('{self._original}')"

    def __fspath__(self) -> str:
        if self.is_external:
            raise TypeError(
                "Remote OtherPath is not a local filesystem path; "
                "call copy() to materialize a local pathlib.Path first."
            )
        return os.fspath(self._upath)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, OtherPath):
            return self.full_path.replace("\\", "/") == other.full_path.replace("\\", "/")
        if isinstance(other, (str, pathlib.Path, UPath)):
            return str(self).replace("\\", "/") == str(other).replace("\\", "/")
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.full_path.replace("\\", "/"))

    def __truediv__(self, other: Union[str, "OtherPath"]) -> "OtherPath":
        other_s = other.original if isinstance(other, OtherPath) else str(other)
        if self.is_external:
            return OtherPath(f"{self._original.rstrip('/')}/{other_s.lstrip('/')}")
        return OtherPath(self._upath / other_s)

    def __div__(self, other: Union[str, "OtherPath"]) -> "OtherPath":
        return self.__truediv__(other)

    def __rtruediv__(self, other: Union[str, "OtherPath"]) -> "OtherPath":
        if self.is_external:
            raise TypeError("Cannot use rtruediv on external paths.")
        other_s = other.original if isinstance(other, OtherPath) else str(other)
        return OtherPath(pathlib.Path(other_s) / pathlib.Path(os.fspath(self)))

    @property
    def name(self) -> str:
        return self._upath.name

    @property
    def suffix(self) -> str:
        return self._upath.suffix

    @property
    def suffixes(self) -> List[str]:
        return list(self._upath.suffixes)

    @property
    def stem(self) -> str:
        return self._upath.stem

    @property
    def parent(self) -> "OtherPath":
        if self.is_external:
            parent = self._original.rsplit("/", 1)[0]
            return OtherPath(parent)
        return OtherPath(self._upath.parent)

    @property
    def parents(self):
        if self.is_external:
            logging.warning("Cannot run `parents` yet for external paths! Returning None.")
            return None
        return self._upath.parents

    def with_suffix(self, suffix: str) -> "OtherPath":
        if self.is_external:
            return OtherPath(self._original.rsplit(".", 1)[0] + suffix)
        return OtherPath(self._upath.with_suffix(suffix))

    def with_name(self, name: str) -> "OtherPath":
        if self.is_external:
            return OtherPath(self._original.rsplit("/", 1)[0] + "/" + name)
        return OtherPath(self._upath.with_name(name))

    def with_stem(self, stem: str) -> "OtherPath":
        if self.is_external:
            parent, _, name = self._original.rpartition("/")
            suffix = pathlib.PurePosixPath(name).suffix
            return OtherPath(f"{parent}/{stem}{suffix}")
        return OtherPath(self._upath.with_stem(stem))

    def resolve(self, *args: Any, **kwargs: Any) -> "OtherPath":
        if self.is_external:
            return OtherPath(self._original)
        return OtherPath(self._upath.resolve(*args, **kwargs))

    def absolute(self) -> "OtherPath":
        if self.is_external:
            return OtherPath(self._original)
        return OtherPath(self._upath.absolute())

    def as_uri(self) -> str:
        if self.is_external:
            return self.full_path
        return self._upath.as_uri()

    def as_posix(self) -> str:
        if self.is_external:
            return self.full_path
        return pathlib.Path(os.fspath(self)).as_posix()

    def samefile(self, other_path: Union[str, pathlib.Path, "OtherPath"]) -> bool:
        if self.is_external:
            other = OtherPath(other_path)
            return self.full_path == other.full_path
        other = other_path
        if isinstance(other, OtherPath):
            other = other._upath
        return self._upath.samefile(other)

    # --- remote / local I/O ----------------------------------------------

    def _upath_with_credentials(self, *, testing: bool = False) -> UPath:
        if not self.is_external:
            return self._upath
        scheme = _scheme_from_uri_prefix(self._uri_prefix)
        if f"{scheme}:" not in IMPLEMENTED_PROTOCOLS:
            raise ValueError(f"uri_prefix {scheme} not implemented yet")
        creds = _credentials_from_env(testing=testing)
        options = {**dict(self._upath.storage_options), **self._extra_storage_options, **creds}
        return UPath(str(self._upath), **options)

    def connection_info(self, testing: bool = False) -> Tuple[Dict[str, Any], str]:
        """Return ``(storage_options, host)`` for remote paths (empty if local)."""
        if not self.is_external:
            return {}, ""
        opts = _credentials_from_env(testing=testing)
        # Preserve Fabric-era shape: host may be ``user@host``.
        return opts, self.location

    def exists(self, *args: Any, **kwargs: Any) -> bool:
        testing = kwargs.pop("testing", False)
        if self.is_external:
            try:
                return bool(self._upath_with_credentials(testing=testing).exists())
            except FileNotFoundError:
                return False
        return bool(self._upath.exists())

    def is_file(self, *args: Any, **kwargs: Any) -> bool:
        testing = kwargs.pop("testing", False)
        if self.is_external:
            try:
                return bool(self._upath_with_credentials(testing=testing).is_file())
            except FileNotFoundError:
                return False
        return bool(self._upath.is_file())

    def is_dir(self, *args: Any, **kwargs: Any) -> bool:
        testing = kwargs.pop("testing", False)
        if self.is_external:
            try:
                return bool(self._upath_with_credentials(testing=testing).is_dir())
            except FileNotFoundError:
                return False
        return bool(self._upath.is_dir())

    def stat(self, *args: Any, **kwargs: Any) -> Any:
        testing = kwargs.pop("testing", False)
        if self.is_external:
            try:
                upath = self._upath_with_credentials(testing=testing)
                info = upath.fs.info(upath.path)
                return ExternalStatResult(
                    st_size=int(info.get("size") or 0),
                    st_mtime=_as_epoch_seconds(info.get("mtime")),
                    st_atime=_as_epoch_seconds(
                        info.get("atime") if info.get("atime") is not None else info.get("mtime")
                    ),
                    st_ctime=None,
                )
            except (UnderDefined, FileNotFoundError, OSError) as exc:
                logging.debug("Remote stat failed (%s); returning zeros.", exc)
                return ExternalStatResult()
        return self._upath.stat()

    def copy(
        self, destination: Optional[pathlib.Path] = None, testing: bool = False
    ) -> pathlib.Path:
        """Copy this file to a local destination directory; return the local path."""
        if destination is None:
            destination = pathlib.Path(tempfile.gettempdir())
        else:
            destination = pathlib.Path(destination)
        path_of_copied_file = destination / self.name

        if not self.is_external:
            shutil.copy2(os.fspath(self), destination)
            return path_of_copied_file

        upath = self._upath_with_credentials(testing=testing)
        try:
            upath.fs.get(upath.path, str(path_of_copied_file))
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Could not find file {self.raw_path} on {self.location}"
            ) from exc
        return path_of_copied_file

    def _wrap_remote_child(self, child: UPath) -> "OtherPath":
        child_path = child.path if child.path.startswith("/") else f"/{child.path}"
        return OtherPath(f"{self._uri_prefix}{self._location}{child_path}")

    def glob(self, glob_str: str, *args: Any, **kwargs: Any) -> Generator["OtherPath", None, None]:
        testing = kwargs.pop("testing", False)
        if self.is_external:
            upath = self._upath_with_credentials(testing=testing)
            for child in upath.glob(glob_str):
                yield self._wrap_remote_child(child)
            return
        for child in pathlib.Path(os.fspath(self)).glob(glob_str):
            yield OtherPath(child)

    def rglob(self, glob_str: str, *args: Any, **kwargs: Any) -> Generator["OtherPath", None, None]:
        testing = kwargs.pop("testing", False)
        if self.is_external:
            upath = self._upath_with_credentials(testing=testing)
            for child in upath.rglob(glob_str):
                yield self._wrap_remote_child(child)
            return
        for child in pathlib.Path(os.fspath(self)).rglob(glob_str):
            yield OtherPath(child)

    def listdir(self, levels: int = 1, **kwargs: Any) -> Generator["OtherPath", None, None]:
        """List directory contents (shallow by default for remote)."""
        testing = kwargs.pop("testing", False)
        if self.is_external:
            upath = self._upath_with_credentials(testing=testing)
            if levels == 0:
                pattern = "*"
            elif levels == 1:
                pattern = "*"
            else:
                pattern = "**/*"
            for child in upath.glob(pattern) if levels <= 1 else upath.rglob("*"):
                yield self._wrap_remote_child(child)
            return
        base = pathlib.Path(os.fspath(self))
        if not base.is_dir():
            return
        if levels == 0:
            for child in base.iterdir():
                yield OtherPath(child)
            return
        if levels < 0:
            for child in base.rglob("*"):
                yield OtherPath(child)
            return
        for child in base.glob("/".join(["*"] * levels) if levels > 1 else "*"):
            yield OtherPath(child)

    def iterdir(self, *args: Any, **kwargs: Any) -> Optional[Generator["OtherPath", None, None]]:
        if self.is_external:
            return self.listdir(levels=0, **kwargs)
        return (OtherPath(p) for p in self._upath.iterdir())

    @classmethod
    def home(cls) -> "OtherPath":
        return cls(pathlib.Path.home())


def get_otherpath_class() -> type:
    """Return the ``OtherPath`` class (compat shim; always the UPath wrapper)."""
    return OtherPath
