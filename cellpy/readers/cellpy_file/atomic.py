"""Atomic staging for cellpy-file writes.

Writers stage into a temp file next to the destination and replace the
destination only once the whole archive is on disk. An interrupted save can then
neither leave a half-written file that still opens (missing zip members) nor
destroy the previously-good file (#845).
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from typing import Callable, Iterator, Optional, Union

_module_logger = logging.getLogger(__name__)

PathLike = Union[str, os.PathLike]


@contextlib.contextmanager
def atomic_write(
    path: PathLike,
    *,
    verify: Optional[Callable[[Path], None]] = None,
) -> Iterator[Path]:
    """Stage a write next to ``path`` and replace ``path`` atomically on success.

    The staged file lives in the destination's own directory so that
    ``os.replace`` stays within one filesystem (a temp directory elsewhere would
    make the final step a copy, and no longer atomic).

    Args:
        path: Final destination. Parent directories are created if missing.
        verify: Optional check run on the staged file before it replaces the
            destination. Raise from it to reject an incomplete write; the staged
            file is then removed and ``path`` is left untouched.

    Yields:
        ``pathlib.Path``: The staged path the caller should write to. The caller
        creates it — nothing is created up front, so writers that want to own
        file creation (``zipfile.ZipFile``, ``pandas.HDFStore``) still can.

    Raises:
        OSError: If the final replace fails (e.g. the destination is open in
            another process on Windows). The staged file is **kept** in that
            case, and its location logged, so the new data is recoverable.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.parent / f"{path.name}.tmp{os.getpid()}"
    _discard(staged)

    try:
        yield staged
        if verify is not None:
            verify(staged)
    except BaseException:
        _discard(staged)
        raise

    try:
        os.replace(staged, path)
    except OSError:
        _module_logger.critical(
            "could not replace %s; it is intact and the new data is kept at %s",
            path,
            staged,
        )
        raise
    _module_logger.debug("atomically replaced %s", path)


def _discard(staged: Path) -> None:
    """Remove a staged file, tolerating a locked or already-gone file."""
    with contextlib.suppress(OSError):
        staged.unlink(missing_ok=True)
