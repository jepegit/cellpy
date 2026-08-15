"""Path-like objects that can point at local or remote (ssh/sftp) locations.

``OtherPath`` is a thin compatibility wrapper around ``upath.UPath``. Remote
reads use fsspec/Paramiko; callers that need a local file should use
``copy()`` (or the cellpy load seams that call it).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import fnmatch
import logging
import os
import pathlib
import posixpath
import shlex
import shutil
import tempfile
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union

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
        # PosixPath.parts keeps "/" as its own element; joining with "/"
        # would turn "/foo" into "//foo". as_posix() is the correct form.
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
    """Build Paramiko/fsspec ``storage_options`` from cellpy credentials."""
    # Single resolution path (config plan Step 6): session config first, live
    # environment as fallback — see cellpy.config.credentials.
    from cellpy.config import credentials

    password = credentials.get_password()
    key_filename = credentials.get_key_filename()
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
        # Credentialed UPath (and its fs) cached per instance - see
        # _upath_with_credentials (#901).
        self._credentialed_upath: Optional[UPath] = None
        self._credentialed_key: Optional[Tuple[str, bool]] = None

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
        """Credentialed ``UPath`` for this instance (built once, then reused).

        Building it resolves credentials and instantiates the filesystem, and
        the first remote call on a fresh one pays an SSH handshake (~0.5-0.8 s
        measured). ``is_file`` + ``stat`` + ``copy`` on the *same* instance
        therefore share one (#901). The cache is keyed on the URI string, so a
        path that somehow changes identity rebuilds it.
        """
        if not self.is_external:
            return self._upath
        url = str(self._upath)
        cache_key = (url, bool(testing))
        cached = getattr(self, "_credentialed_upath", None)
        if cached is not None and self._credentialed_key == cache_key:
            return cached
        scheme = _scheme_from_uri_prefix(self._uri_prefix)
        if f"{scheme}:" not in IMPLEMENTED_PROTOCOLS:
            raise ValueError(f"uri_prefix {scheme} not implemented yet")
        creds = _credentials_from_env(testing=testing)
        options = {**dict(self._upath.storage_options), **self._extra_storage_options, **creds}
        upath = UPath(url, **options)
        self._credentialed_upath = upath
        self._credentialed_key = cache_key
        return upath

    def __getstate__(self) -> Dict[str, Any]:
        """Never carry a live filesystem/SSH client into a pickle or deepcopy."""
        state = self.__dict__.copy()
        state["_credentialed_upath"] = None
        state["_credentialed_key"] = None
        return state

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
        return self._wrap_remote_path(child_path)

    def _wrap_remote_path(self, child_path: str) -> "OtherPath":
        path = child_path if child_path.startswith("/") else f"/{child_path}"
        return OtherPath(f"{self._uri_prefix}{self._location}{path}")

    @staticmethod
    def _remote_rglob_matches(rel: str, name: str, pattern: str) -> bool:
        """Match like ``pathlib.Path.rglob`` (``**/`` + pattern)."""
        rel = rel.replace("\\", "/")
        candidates = [pattern]
        if not pattern.startswith("**/"):
            candidates.append(f"**/{pattern}")
        return any(
            fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel, candidate)
            for candidate in candidates
        )

    @staticmethod
    def _remote_visit_key_from_info(info: Any, dir_path: str) -> Any:
        """Build a cycle-guard key from ``ls``/``info`` detail when available."""
        if not isinstance(info, dict):
            return ("path", dir_path.rstrip("/") or "/")
        ino = info.get("ino", info.get("inode"))
        if ino is not None:
            return ("ino", ino)
        dest = info.get("destination", info.get("target"))
        if dest:
            return ("path", str(dest).rstrip("/") or "/")
        return ("path", dir_path.rstrip("/") or "/")

    def _remote_find_l_file_paths(self, fs: Any, root: str) -> Optional[List[str]]:
        """Bulk list files via remote ``find -L`` when Paramiko exec is available.

        ``find`` exits 1 when it could not descend into some directory (a
        shared ``rawdatadir`` almost always has an unreadable sibling), but it
        still prints every path it did list. Keep that listing and only fall
        back to the ls-walk when nothing was listed (#897).

        Returns ``None`` on failure so callers fall back to the ls-walk.
        """
        client = getattr(fs, "client", None)
        exec_command = getattr(client, "exec_command", None) if client is not None else None
        if exec_command is None:
            return None
        cmd = f"find -L {shlex.quote(root)} -type f -print"
        try:
            _stdin, stdout, stderr = exec_command(cmd, timeout=300)
            exit_status = stdout.channel.recv_exit_status()
            out = stdout.read()
            err = stderr.read()
        except (OSError, AttributeError, TypeError, ValueError) as exc:
            logging.debug("Remote find -L failed for %s: %s", root, exc)
            return None
        if isinstance(out, (bytes, bytearray)):
            text = out.decode("utf-8", errors="replace")
        else:
            text = str(out)
        paths: List[str] = []
        for line in text.splitlines():
            path = line.strip()
            if path:
                paths.append(path)
        if exit_status not in (0, None):
            logging.debug(
                "Remote find -L exit %s for %s (%s paths listed): %s",
                exit_status,
                root,
                len(paths),
                err[:200] if isinstance(err, (bytes, bytearray)) else err,
            )
            if not paths:
                return None
        return paths

    def _remote_rglob_from_find(
        self,
        glob_str: str,
        *,
        fs: Any,
        root: str,
    ) -> Optional[List["OtherPath"]]:
        """Try bulk ``find -L`` listing; return matches or ``None`` to fall back."""
        bulk = self._remote_find_l_file_paths(fs, root)
        if bulk is None:
            return None
        matches: List["OtherPath"] = []
        for child_path in bulk:
            name = posixpath.basename(child_path.rstrip("/"))
            if child_path.startswith(root + "/"):
                rel = child_path[len(root) + 1 :]
            else:
                rel = name
            if self._remote_rglob_matches(rel, name, glob_str):
                matches.append(self._wrap_remote_path(child_path))
        return matches

    def _remote_rglob_walk(
        self,
        glob_str: str,
        *,
        testing: bool = False,
        files_only: bool = False,
    ) -> Generator["OtherPath", None, None]:
        """Recursive remote listing that follows directory symlinks.

        fsspec SFTP ``rglob`` / ``find`` treat symlink directories as leaves, which
        breaks shared ``rawdatadir`` layouts where project folders are links.
        Walk with ``ls(detail=True)`` and recurse into links that
        resolve to directories, with a visited-set cycle guard.

        When ``files_only`` is True, prefer a single remote ``find -L … -type f``
        and fall back to this walk, filtering with listing ``type``
        so callers do not need a per-path ``is_file()`` STAT.
        """
        upath = self._upath_with_credentials(testing=testing)
        fs = upath.fs
        root = upath.path.rstrip("/") or "/"

        if files_only:
            bulk_matches = self._remote_rglob_from_find(glob_str, fs=fs, root=root)
            if bulk_matches is not None:
                logging.debug(
                    "Remote rglob used find -L fast path (%s paths) under %s",
                    len(bulk_matches),
                    root,
                )
                yield from bulk_matches
                return

        visited: Set[Any] = set()

        def visit_key(dir_path: str, info: Any = None) -> Any:
            """Identity for cycle detection (inode / link target / path)."""
            if info is not None:
                return self._remote_visit_key_from_info(info, dir_path)
            try:
                fetched = fs.info(dir_path)
            except (FileNotFoundError, OSError, AttributeError):
                return ("path", dir_path.rstrip("/") or "/")
            return self._remote_visit_key_from_info(fetched, dir_path)

        def link_is_dir(child_path: str) -> bool:
            """Decide whether a symlink should be recursed into.

            Probe with ``ls`` (one round-trip) instead of a separate ``isdir``
            STAT; cycle keys still prefer ``destination`` from parent ``ls``.
            """
            try:
                fs.ls(child_path, detail=False)
                return True
            except (FileNotFoundError, OSError, PermissionError, NotADirectoryError):
                return False

        def walk(
            dir_path: str,
            dir_info: Any = None,
        ) -> Generator["OtherPath", None, None]:
            key = visit_key(dir_path, dir_info)
            if key in visited:
                return
            visited.add(key)
            try:
                entries = fs.ls(dir_path, detail=True)
            except (FileNotFoundError, OSError, PermissionError) as exc:
                logging.debug("Remote ls failed for %s: %s", dir_path, exc)
                return

            for entry in entries:
                if isinstance(entry, dict):
                    child_path = entry.get("name") or ""
                    etype = entry.get("type")
                    child_info: Any = entry
                else:
                    child_path = str(entry)
                    etype = None
                    child_info = None
                if not child_path:
                    continue
                name = posixpath.basename(child_path.rstrip("/"))
                if name in (".", ".."):
                    continue

                if child_path.rstrip("/") == root:
                    continue
                if child_path.startswith(root + "/"):
                    rel = child_path[len(root) + 1 :]
                else:
                    rel = name

                is_dir = False
                if etype == "directory":
                    is_dir = True
                elif etype == "link":
                    is_dir = link_is_dir(child_path)
                elif etype is None:
                    try:
                        is_dir = bool(fs.isdir(child_path))
                    except (OSError, FileNotFoundError):
                        is_dir = False

                is_file = etype == "file" or (etype == "link" and not is_dir)
                if etype is None and not is_dir:
                    # Unknown listing shape: treat non-dirs as file candidates.
                    is_file = True

                if files_only:
                    if is_file and self._remote_rglob_matches(rel, name, glob_str):
                        yield self._wrap_remote_path(child_path)
                elif self._remote_rglob_matches(rel, name, glob_str):
                    yield self._wrap_remote_path(child_path)

                if is_dir:
                    yield from walk(child_path, child_info)

        yield from walk(root)

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
        files_only = bool(kwargs.pop("files_only", False))
        if self.is_external:
            yield from self._remote_rglob_walk(
                glob_str, testing=testing, files_only=files_only
            )
            return
        for child in pathlib.Path(os.fspath(self)).rglob(glob_str):
            if files_only and not child.is_file():
                continue
            yield OtherPath(child)

    def listdir(self, levels: int = 1, **kwargs: Any) -> Generator["OtherPath", None, None]:
        """List directory contents (shallow by default for remote)."""
        testing = kwargs.pop("testing", False)
        if self.is_external:
            if levels <= 1:
                upath = self._upath_with_credentials(testing=testing)
                for child in upath.glob("*"):
                    yield self._wrap_remote_child(child)
                return
            # Deep listing shares symlink-following walk with rglob (#688).
            yield from self.rglob("*", testing=testing)
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
