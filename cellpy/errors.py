"""custom errors"""


class Error(Exception):
    """Base class for other exceptions"""
    pass


class WrongFileVersion(Error):
    """Raised when the file version is wrong"""
    pass
