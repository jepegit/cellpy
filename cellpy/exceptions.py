"""Exceptions defined within cellpy"""


class Error(Exception):
    """Base class for other exceptions"""
    pass


class ConfigFileNotWritten(Error):
    """Raised when the configuration file cannot be written"""
    pass


class ConfigFileNotRead(Error):
    """Raised when the configuration file cannot be read"""
    pass


class WrongFileVersion(Error):
    """Raised when the file version is wrong"""
    pass


class DeprecatedFeature(Error):
    """Raised when the feature is recentlhy deprecated"""
    pass

