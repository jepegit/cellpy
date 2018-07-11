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
