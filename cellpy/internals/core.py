"""This module contains div classes etc that are not really connected to cellpy."""

from dataclasses import dataclass
import fnmatch
import logging
import os
import pathlib
import shutil
import stat
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

import fabric

from cellpy.exceptions import UnderDefined


S = TypeVar("S", bound="OtherPath")
URI_PREFIXES = ["ssh:", "sftp:", "scp:", "http:", "https:", "ftp:", "ftps:", "smb:"]
IMPLEMENTED_PROTOCOLS = ["ssh:", "sftp:", "scp:"]
# name of environment variable that holds the key file and password:
ENV_VAR_CELLPY_KEY_FILENAME = "CELLPY_KEY_FILENAME"
ENV_VAR_CELLPY_PASSWORD = "CELLPY_PASSWORD"


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
    with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
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
                f"   - FileNotFoundError: Could not perform directory listing in {p.raw_path} on {host}."
                f"\n     {e}"
            )

    return info


@dataclass
class ExternalStatResult:
    """Mock of os.stat_result."""

    # st_mode: int = 0
    # st_ino: int = 0
    # st_dev: int = 0
    # st_nlink: int = 0
    # st_uid: int = 0
    # st_gid: int = 0
    st_size: int = 0
    st_mtime: int = 0
    st_atime: int = 0
    st_ctime: Optional[int] = None


# TODO: This must be cleaned up. Now also python 3.11 crashes when running this code.
def _clean_up_original_path_string(path_string):
    if not isinstance(path_string, str):
        if isinstance(path_string, OtherPath):
            logging.debug(f"path is an OtherPath object")
            if hasattr(path_string, "original"):
                logging.debug(f"path has an original attribute")
                path_string = path_string.original
            else:
                logging.debug(f"path does not have an original attribute")
                path_string = str(path_string)

        elif isinstance(path_string, pathlib.PosixPath):
            path_string = "/".join(path_string.parts)
        elif isinstance(path_string, pathlib.WindowsPath):
            parts = list(path_string.parts)
            if not parts:
                parts = [""]
            parts[0] = parts[0].replace("\\", "")
            path_string = "/".join(parts)
        else:
            logging.debug(f"unknown path type: {type(path_string)}")
            path_string = str(path_string)
    return path_string


def _check_external(path_string: str) -> Tuple[str, bool, str, str]:
    # t = time.perf_counter()
    # path_sep = "\\" if os.name == "nt" else "/"
    _is_external = False
    _location = ""
    _uri_prefix = ""
    for prefix in URI_PREFIXES:
        if path_string.startswith(prefix):
            path_string = path_string.replace(prefix, "")
            path_string = path_string.lstrip("/")
            _is_external = True
            _uri_prefix = prefix + "//"
            _location, *rest = path_string.split("/")
            path_string = "/" + "/".join(rest)
            break
    path_string = path_string or "."
    # fix for windows paths:
    path_string = path_string.replace("\\", "/")
    # fix for posix paths:
    path_string = path_string.replace("//", "/")
    # print(f"check external took {(time.perf_counter()-t)/1_000_000} nanoseconds")
    return path_string, _is_external, _uri_prefix, _location


class OtherPath(pathlib.Path):
    """A pathlib.Path subclass that can handle external paths.

    Attributes:
        is_external (bool): is True if the path is external.
        location (str): the location of the external path (e.g. a server name).
        uri_prefix (str): the prefix of the external path (e.g. scp:// or sftp://).
        raw_path (str): the path without any uri_prefix or location.
        original (str): the original path string.
        full_path (str): the full path (including uri_prefix and location).

    Methods:
        copy (method): a method for copying the file to a local path.
        glob (method): a method for globbing external paths if ``is_external`` is True.
        rglob (method): a method for 'recursive' globbing external paths (max one extra level deep) if ``is_external`` is True.
    """

    # TODO: This crashes now in python 3.11. Need to find a way to fix this.
    _flavour = (
        pathlib._windows_flavour if os.name == "nt" else pathlib._posix_flavour
    )  # noqa

    def __new__(cls, *args, **kwargs):
        cls._created = time.time()
        if args:
            path, *args = args
        else:
            path = "."
            logging.debug("initiating OtherPath without any arguments")
        if not path:
            logging.debug("initiating OtherPath with empty path")
            path = "."
        if isinstance(path, OtherPath) and hasattr(path, "_original"):
            logging.debug(f"path is OtherPath")
            path = path._original
        logging.debug(f"checked if path is OtherPath")

        path = _clean_up_original_path_string(path)
        assert isinstance(path, str), "path must be a string"
        cls.__original = path
        cls._pathlib_doc = super().__doc__
        path = _check_external(path)[0]
        return super().__new__(cls, path, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        logging.debug("Running __init__ for OtherPath")
        _path_string, *args = args
        if not _path_string:
            path_string = "."
        else:
            path_string = self.__original
        self._original = self.__original
        self._check_external(path_string)
        # pathlib.PurePath and Path for Python 3.12 seems to have an __init__ method
        # where it sets self._raw_path from the input argument, but this is not the case
        # for Python 3.11, 10, and 9. Those do not have their own __init__ method (and
        # does not have a self._raw_path attribute).
        # Instead of running e.g. super().__init__(self._raw_other_path) we do this
        # instead (which is what the __init__ method does in Python 3.12):
        self._raw_path = self._raw_other_path
        self.__doc__ += f"\nOriginal documentation:\n\n{self._pathlib_doc}"
        self._wrap_methods()  # dynamically wrapping methods - should gradually be replaced by hard-coded methods.

    def _wrap_methods(self):
        logging.debug("Running _wrap_methods for OtherPath")
        existing_methods = self.__class__.__dict__.keys()
        parent_methods_that_works_also_on_external_paths = []  # "parents", "parts"
        parent_methods_that_returns_other_paths = []

        for m in sorted(dir(pathlib.Path)):
            if m.startswith("_"):
                continue
            if (
                m in existing_methods
                or m in parent_methods_that_works_also_on_external_paths
            ):
                continue
            method = getattr(pathlib.Path, m)
            if m in parent_methods_that_returns_other_paths:
                setattr(self.__class__, m, self._wrap_and_morph_method(method))
            if callable(method):
                setattr(self.__class__, m, self._wrap_callable_method(method))
            else:
                setattr(self.__class__, m, self._wrap_non_callable(method))

    def _wrap_and_morph_method(self, method):
        if self.is_external:
            return lambda *args, **kwargs: self
        else:
            return lambda *args, **kwargs: OtherPath(*args, **kwargs)

    def _wrap_callable_method(self, method, default_return_value=True):
        if self.is_external:
            return lambda *args, **kwargs: default_return_value
        else:
            return method

    def _wrap_non_callable(self, attr, default_return_value=None):
        if self.is_external:
            return default_return_value
        else:
            return attr

    def _check_external(self, path_string):
        logging.debug("Running _check_external for OtherPath")
        (
            path_string,
            self._is_external,
            self._uri_prefix,
            self._location,
        ) = _check_external(path_string)
        self._raw_other_path = path_string

    def __div__(self, other: Union[str, S]) -> S:
        if self.is_external:
            path = f"{self._original}/{other}"
            return OtherPath(path)
        path = pathlib.Path(self._original).__truediv__(other)
        return OtherPath(path)

    def __truediv__(self, other: Union[str, S]) -> S:
        if self.is_external:
            path = f"{self._original}/{other}"
            return OtherPath(path)
        path = pathlib.Path(self._original).__truediv__(other)
        return OtherPath(path)

    def __rtruediv__(self: S, key: Union[str, S]) -> S:
        if self.is_external:
            raise TypeError(f"Cannot use rtruediv on external paths.")
        path = pathlib.Path(self._original).__rtruediv__(key)
        return OtherPath(path)

    def __str__(self: S) -> str:
        if hasattr(self, "_original") and self.is_external:
            logging.debug("external path, returning _original")
            return self._original
        return super().__str__()

    def __repr__(self: S) -> str:
        if hasattr(self, "_original"):
            if self.is_external:
                logging.debug("external path, returning _original")
            return f"OtherPath('{self._original}')"
        else:
            return super().__repr__()

    def _glob(self, glob_str: str, **kwargs) -> Generator:
        testing = kwargs.pop("testing", False)
        search_in_sub_dirs = kwargs.pop("search_in_sub_dirs", False)
        if self.is_external:
            connect_kwargs, host = self._get_connection_info(testing)
            paths = self._glob_with_fabric(
                host, connect_kwargs, glob_str, search_in_sub_dirs=search_in_sub_dirs
            )
            return (OtherPath(f"{self._original.rstrip('/')}/{p}") for p in paths)
        paths = pathlib.Path(self._original).glob(glob_str)
        return (OtherPath(p) for p in paths)

    def glob(self, glob_str: str, *args, **kwargs) -> Generator:
        return self._glob(glob_str, search_in_sub_dirs=False, **kwargs)

    def rglob(self, glob_str: str, *args, **kwargs) -> Generator:
        return self._glob(glob_str, search_in_sub_dirs=True, **kwargs)

    def _listdir(self, levels: int, **kwargs) -> Generator:
        if self.is_external:
            testing = kwargs.pop("testing", False)
            connect_kwargs, host = self._get_connection_info(testing)
            paths = self._listdir_with_fabric(host, connect_kwargs, levels)
            return (OtherPath(p) for p in paths)

        if self.is_dir():
            return (
                OtherPath(f"{self.full_path}/{p}") for p in os.listdir(self._original)
            )

    def listdir(self: S, levels: int = 1, **kwargs) -> Generator:
        """List the contents of the directory.

        Args:
            levels (int, optional): How many sublevels to list:

                - If you want to list all sublevels, use ``listdir(levels=-1)``.
                - If you want to list only the current level (no subdirectories),
                  use ``listdir(levels=0)``.

        Returns:
            Generator: Generator of ``OtherPath`` objects.

        """
        return self._listdir(levels, **kwargs)

    def resolve(self: S, *args, **kwargs) -> S:
        """Resolve the path."""
        if self.is_external:
            logging.debug(f"Cannot resolve external paths. Returning self. ({self})")
            return OtherPath(self._original)
        resolved_path = pathlib.Path(self._original).resolve(*args, **kwargs)
        return OtherPath(resolved_path)

    def is_dir(self: S, *args, **kwargs) -> bool:
        """Check if path is a directory."""
        if self.is_external:
            logging.warning(
                f"Cannot check if dir exists for external paths! Assuming it exists."
            )
            return True
        return super().is_dir()

    def is_file(self: S, *args, **kwargs) -> bool:
        """Check if path is a file."""
        if self.is_external:
            logging.warning(
                f"Cannot check if file exists for external paths! Assuming it exists."
            )
            return True
        return super().is_file()

    def exists(self: S, *args, **kwargs) -> bool:
        """Check if path exists."""
        if self.is_external:
            logging.warning(
                f"Cannot check if path exists for external paths! Assuming it exists."
            )
            return True
        return super().exists()

    @property
    def parent(self: S) -> S:
        """Return the parent directory of the path."""
        if self.is_external:
            return OtherPath(self._original.rsplit("/", 1)[0])
        return OtherPath(super().parent)

    @property
    def name(self: S):
        """Return the parent directory of the path."""
        return super().name

    @property
    def suffix(self) -> str:
        """Return the suffix of the path."""
        return super().suffix

    @property
    def suffixes(self) -> List[str]:
        """Return the suffixes of the path."""
        return super().suffixes

    @property
    def stem(self) -> str:
        """Return the stem of the path."""
        return super().stem

    def with_suffix(self: S, suffix: str) -> S:
        """Return a new path with the suffix changed."""
        if self.is_external:
            logging.warning(
                "This is method (`with_suffix`) not tested for external paths!"
            )
            return OtherPath(self._original.rsplit(".", 1)[0] + suffix)
        return OtherPath(super().with_suffix(suffix))

    def with_name(self: S, name: str) -> S:
        """Return a new path with the name changed."""
        if self.is_external:
            logging.warning(
                "This method (`with_name`) is not tested for external paths!"
            )
            return OtherPath(self._original.rsplit("/", 1)[0] + "/" + name)
        return OtherPath(super().with_name(name))

    def with_stem(self: S, stem: str) -> S:
        """Return a new path with the stem changed."""
        if self.is_external:
            logging.warning(
                "This method (`with_stem`) is not tested for external paths!"
            )
            return OtherPath(self._original.rsplit("/", 1)[0] + "/" + stem)
        return OtherPath(super().with_stem(stem))

    def absolute(self: S) -> S:
        if self.is_external:
            logging.warning(
                "This method (`absolute`) is not implemented yet for external paths! Returning self."
            )
            return OtherPath(self._original)
        return OtherPath(super().absolute())

    def samefile(self: S, other_path: Union[str, pathlib.Path, S]) -> bool:
        if self.is_external:
            logging.warning(
                "This method (`absolute`) is not implemented yet for external paths! Returning True."
            )
            return True
        return super().samefile(other_path)

    def iterdir(self, *args, **kwargs):
        if self.is_external:
            logging.warning(
                f"Cannot run `iterdir` yet for external paths! Returning None."
            )
            return
        else:
            return (OtherPath(p) for p in super().iterdir())

    @property
    def parents(self, *args, **kwargs):
        if self.is_external:
            logging.warning(
                f"Cannot run `parents` yet for external paths! Returning None."
            )
            return
        return super().parents

    def stat(self, *args, **kwargs):
        testing = kwargs.pop("testing", False)
        if self.is_external:
            # logging.warning(f"Cannot run `stat` for external paths! Returning stat_result object with only zeros.")
            try:
                connect_kwargs, host = self._get_connection_info(testing)
            except UnderDefined as e:
                logging.debug(f"UnderDefined error: {e}")
                logging.debug("Returning stat_result object with only zeros.")
                return ExternalStatResult()
            try:
                return self._stat_with_fabric(host, connect_kwargs)
            except FileNotFoundError:
                logging.debug(
                    "File not found! Returning stat_result object with only zeros."
                )
                return ExternalStatResult()

        return super().stat()

    def joinpath(self, *args, **kwargs):
        logging.warning(f"Cannot run 'joinpath' for OtherPath!")
        return OtherPath(self._original)

    def readlink(self, *args, **kwargs):
        logging.warning(f"Cannot run 'readlink' for OtherPath!")
        return

    def match(self, *args, **kwargs):
        logging.warning(f"Cannot run 'match' for OtherPath!")
        return

    def cwd(self):
        logging.warning(f"Cannot run 'match' for OtherPath!")
        return

    def group(self):
        logging.warning(f"Cannot run 'group' for OtherPath!")
        return

    @property
    def owner(self, *args, **kwargs):
        logging.warning(f"Cannot get 'owner' for OtherPath!")
        return

    def lchmod(self, *args, **kwargs):
        logging.warning(f"Cannot run 'lchmod' for OtherPath!")
        return OtherPath(self._original)

    @property
    def original(self: S) -> str:
        return self._original

    @property
    def raw_path(self: S) -> str:
        # this will return a leading slash for some edge cases
        return self._raw_other_path

    @property
    def full_path(self: S) -> str:
        if self.is_external:
            return f"{self._uri_prefix}{self._location}{self._raw_other_path}"
        return self._original

    @property
    def pathlike_location(self: S) -> S:
        """Return the location of the external path as a pathlike object."""

        if self.is_external:
            return OtherPath(f"{self._uri_prefix}{self._location}")
        return OtherPath(super().drive)

    @property
    def is_external(self: S) -> bool:
        if not hasattr(self, "_is_external"):
            logging.warning("OBS! OtherPath object missing _is_external attribute!")
            logging.warning("This should not happen. Please report this bug!")
            logging.warning(
                "(most likely means that pathlib.Path has changed and that it now has "
                "another attribute or method that returns a new pathlib.Path object or "
                "that you have used a method that is not supported yet)"
            )
            # return False
        return self._is_external

    @property
    def uri_prefix(self) -> str:
        """Return the uri prefix for the external path (e.g ``ssh://``)."""
        return self._uri_prefix

    @property
    def location(self) -> str:
        """Return the location of the external path (e.g ``user@server.com``)."""
        return self._location

    def as_uri(self) -> str:
        """Return the path as a uri (e.g. ``scp://user@server.com/home/data/my_file.txt``)."""
        if self._is_external:
            return f"{self._uri_prefix}{self._location}/{'/'.join(list(super().parts)[1:])}"
        return super().as_uri()

    def copy(
        self, destination: Optional[pathlib.Path] = None, testing=False
    ) -> pathlib.Path:
        """Copy the file to a destination."""
        if destination is None:
            destination = pathlib.Path(tempfile.gettempdir())
        else:
            destination = pathlib.Path(destination)
        path_of_copied_file = destination / self.name

        if not self.is_external:
            shutil.copy2(self, destination)
        else:
            connect_kwargs, host = self._get_connection_info(testing)
            self._copy_with_fabric(host, connect_kwargs, destination)

        return path_of_copied_file

    def connection_info(self, testing: bool = False) -> Tuple[Dict, str]:
        """Return a dictionary with connection information."""
        if self.is_external:
            return self._get_connection_info(testing)
        logging.debug(f"not external path! returning empty dict and empty string")
        return {}, ""

    def _get_connection_info(self, testing: bool = False) -> Tuple[Dict, str]:
        host = self.location
        uri_prefix = self.uri_prefix.replace("//", "")
        if uri_prefix not in URI_PREFIXES:
            raise ValueError(f"uri_prefix {uri_prefix} not recognized")
        if uri_prefix not in IMPLEMENTED_PROTOCOLS:
            raise ValueError(
                f"uri_prefix {uri_prefix.replace(':', '')} not implemented yet"
            )
        password = os.getenv(ENV_VAR_CELLPY_PASSWORD, None)
        key_filename = os.getenv(ENV_VAR_CELLPY_KEY_FILENAME, None)
        if password is None and key_filename is None:
            raise UnderDefined(
                f"You must define either {ENV_VAR_CELLPY_PASSWORD} "
                f"or {ENV_VAR_CELLPY_KEY_FILENAME} environment variables."
            )
        if key_filename is not None:
            key_filename = pathlib.Path(key_filename).expanduser().resolve()
            connect_kwargs = {"key_filename": str(key_filename)}
            logging.debug(f"got key_filename")
            if not testing:
                if not pathlib.Path(key_filename).is_file():
                    raise FileNotFoundError(f"Could not find key file {key_filename}")
        else:
            connect_kwargs = {"password": password}
        return connect_kwargs, host

    def _copy_with_fabric(
        self, host: str, connect_kwargs: dict, destination: Union[str, S, pathlib.Path]
    ):
        with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
            try:
                t1 = time.time()
                conn.get(self.raw_path, str(destination / self.name))
                logging.debug(f"copying took {time.time() - t1:.2f} seconds")
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Could not find file {self.raw_path} on {host}"
                ) from e

    def _stat_with_fabric(self, host: str, connect_kwargs: dict) -> ExternalStatResult:
        with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
            try:
                t1 = time.time()
                sftp_conn = conn.sftp()
                stat_result = sftp_conn.stat(self.raw_path)
                logging.debug(f"stat took {time.time() - t1:.2f} seconds")
                return ExternalStatResult(
                    st_size=stat_result.st_size,
                    st_atime=stat_result.st_atime,
                    st_mtime=stat_result.st_mtime,
                )
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Could not find file {self.raw_path} on {host}"
                ) from e

    def _listdir_with_fabric(
        self: S,
        host: str,
        connect_kwargs: dict,
        levels: int = 1,
    ) -> List[str]:
        """List the contents of a directory through sftp."""

        path_separator = "/"  # only supports unix-like systems
        t1 = time.time()
        with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
            try:
                t1 = time.time()
                sftp_conn = conn.sftp()
                sftp_conn.chdir(self.raw_path)
                sub_dirs = [
                    f"{self.raw_path}{path_separator}{f}"
                    for f in sftp_conn.listdir()
                    if stat.S_ISDIR(sftp_conn.stat(f).st_mode)
                ]
                files = [
                    f"{self.raw_path}{path_separator}{f}"
                    for f in sftp_conn.listdir()
                    if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)
                ]
                while levels != 0:
                    new_sub_dirs = []
                    for sub_dir in sub_dirs:
                        try:
                            sftp_conn.chdir(sub_dir)
                            _new_sub_dirs = [
                                f"{sub_dir}{path_separator}{f}"
                                for f in sftp_conn.listdir()
                                if stat.S_ISDIR(sftp_conn.stat(f).st_mode)
                            ]
                            new_files = [
                                f"{sub_dir}{path_separator}{f}"
                                for f in sftp_conn.listdir()
                                if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)
                            ]
                            files += new_files
                            new_sub_dirs += _new_sub_dirs
                            sftp_conn.chdir(self.raw_path)
                        except FileNotFoundError:
                            logging.debug(
                                f"Could not look in {sub_dir}: FileNotFoundError"
                            )
                        pass
                    sub_dirs = new_sub_dirs
                    if len(sub_dirs) == 0:
                        break
                    levels -= 1

                logging.debug(f"globbing took {time.time() - t1:.2f} seconds")
                return files
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Could not perform directory listing in {self.raw_path} on {host}.\n{e}"
                ) from e

    def _glob_with_fabric(
        self: S,
        host: str,
        connect_kwargs: dict,
        glob_str: str,
        search_in_sub_dirs: bool = False,
    ) -> List[str]:
        # TODO: update this so that it works faster (need some linux magic)
        # TODO: update OtherPath with a find method (maybe call it match or search)
        #  that takes a list of glob strings and returns a list of list of OtherPath objects
        path_separator = "/"
        logging.info(f"glob_str: {glob_str}")
        logging.info("using fabric to glob")
        with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
            try:
                t1 = time.time()
                sftp_conn = conn.sftp()
                sftp_conn.chdir(self.raw_path)
                logging.info(f"raw-path: {self.raw_path}")
                logging.info(f"search in sub dirs: {search_in_sub_dirs}")

                # checking if the glob string contains a parent directory
                # if it does, we need to change to that directory
                # and then glob
                parent = str(pathlib.Path(glob_str).parent)
                logging.debug(f"parent: {parent}")
                if parent:
                    logging.debug(f"changing to {parent}")
                    glob_str = str(pathlib.Path(glob_str).name)
                    logging.debug(f"updated glob_str: {glob_str}")
                    sftp_conn.chdir(parent)

                if search_in_sub_dirs:  # recursive globbing one level down
                    sub_dirs = [
                        f
                        for f in sftp_conn.listdir()
                        if stat.S_ISDIR(sftp_conn.stat(f).st_mode)
                    ]
                    files = [
                        f
                        for f in sftp_conn.listdir()
                        if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)
                    ]
                    filtered_files = fnmatch.filter(files, glob_str)
                    glob_str = f"*{path_separator}{glob_str}"
                    if len(sub_dirs) > 3:
                        logging.warning(
                            f"WARNING! Searching in {len(sub_dirs)} sub directories - this might take a while"
                        )
                    for sub_dir in sub_dirs:
                        try:
                            logging.debug(f"looking in {sub_dir}")
                            files += [
                                f"{sub_dir}{path_separator}{f}"
                                for f in sftp_conn.listdir(sub_dir)
                                if not stat.S_ISDIR(
                                    sftp_conn.stat(
                                        f"{sub_dir}{path_separator}{f}"
                                    ).st_mode
                                )
                            ]
                        except FileNotFoundError:
                            logging.debug(
                                f"Could not look in {sub_dir}: FileNotFoundError"
                            )
                            pass
                    filtered_files += fnmatch.filter(files, glob_str)
                else:
                    logging.debug("**** NOT SEARCHING IN SUB DIRS ****")
                    files = sftp_conn.listdir()
                    logging.debug(f"files: {files}")
                    filtered_files = fnmatch.filter(files, glob_str)
                logging.debug(f"globbing took {time.time() - t1:.2f} seconds")
                return filtered_files
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Could not find file {self.raw_path} on {host}"
                ) from e


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
    logging.debug("testing OtherPath")
    _check()
