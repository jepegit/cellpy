"""Exceptions defined within cellpy."""

from cellpycore.exceptions import CellpyError, NoDataFound


class Error(Exception):
    """Base class for other exceptions (legacy; prefer :class:`CellpyError`)."""

    pass


class ConfigFileNotWritten(Error):
    """Raised when the configuration file cannot be written"""

    pass


class ConfigFileNotRead(Error):
    """Raised when the configuration file cannot be read"""

    pass


class FileNotFound(Error):
    """Raised when the given file is not found"""

    pass


class SearchError(Error):
    """Raised when the search function fails"""

    pass


class WrongFileVersion(Error):
    """Raised when the file version is wrong"""

    pass


class CorruptCellpyFile(IOError, CellpyError):
    """Raised when a cellpy file is structurally corrupt."""

    pass


class OptionalDependencyError(ImportError, CellpyError):
    """A feature needs an optional dependency that is not installed.

    The message names the extra to install (e.g. ``pip install
    cellpy[legacy-files]``), so the fix travels with the error.
    """

    pass


class ConfigurationError(CellpyError):
    """Raised when configuration validation fails."""

    pass


class UnitsError(ValueError, CellpyError):
    """Raised when unit labels or scales are invalid."""

    pass


class LoaderError(CellpyError):
    """Raised when instrument ingestion fails."""

    pass


class MixedCycleModesError(CellpyError):
    """Raised when engine compute is requested on a multi-test object whose
    tests carry different ``cycle_mode`` values (per-test engine polarity is
    not implemented yet; see issues #506/#507)."""

    pass


class DeprecatedFeature(Error):
    """Raised when the feature is recently deprecated"""

    pass


class ExportFailed(Error):
    """Raised when exporting data failed"""

    pass


class IOError(Error):
    """Raised when exporting data failed"""

    pass


class NullData(Error):
    """Raised when required data is missing (e.g. voltage = None or summary_frames are missing)"""

    pass


class UnderDefined(Error):
    """Raised when trying something that requires you to set
    a missing prm on environment variable first"""

    pass


__all__ = [
    "CellpyError",
    "NoDataFound",
    "Error",
    "ConfigFileNotWritten",
    "ConfigFileNotRead",
    "FileNotFound",
    "SearchError",
    "WrongFileVersion",
    "CorruptCellpyFile",
    "ConfigurationError",
    "UnitsError",
    "LoaderError",
    "MixedCycleModesError",
    "DeprecatedFeature",
    "ExportFailed",
    "IOError",
    "NullData",
    "UnderDefined",
]
