"""Expose the installed cellpy version.

The version is derived from package metadata, which is generated from the
git tag at build/install time (see ``uv-dynamic-versioning`` in pyproject.toml).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cellpy")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0"
