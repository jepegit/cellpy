"""Batch folder layout (batch v3, #698).

Pure path computation, separated from filesystem side effects. In the legacy
``LabJournal`` code, exporting a batch created directories as a side effect of
``paginate()`` (dumpers.py:22 obtained output folders by *calling* it). Here the
two concerns are split: :class:`BatchPaths` only *computes* paths; the single
:func:`ensure_dirs` function is the only thing that touches the filesystem.

The layout mirrors the modern ``paginate`` default (batch_journals.py): the
project directory is the current working directory, the batch dump directory is
``<project_dir>/dump`` and raw exports live under ``<batch_dir>/raw_data``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: Name of the per-project dump directory (kept identical to the legacy
#: ``DEFAULT_OUTPUT_DIR_NAME`` so existing project folders keep working).
DEFAULT_OUTPUT_DIR_NAME = "dump"

#: Sub-directory of the dump directory that holds exported raw data.
RAW_SUBDIR = "raw_data"


@dataclass(frozen=True)
class BatchPaths:
    """Computed, immutable folder layout for one batch.

    Nothing here creates directories -- constructing a ``BatchPaths`` and
    reading its properties is free of side effects. Call :func:`ensure_dirs`
    to materialise the folders.
    """

    name: str
    project: str
    project_dir: Path

    @classmethod
    def create(
        cls, name: str, project: str, project_dir: Path | str | None = None
    ) -> "BatchPaths":
        """Build a layout; ``project_dir`` defaults to the current directory."""
        base = Path(project_dir) if project_dir is not None else Path.cwd()
        return cls(name=name, project=project, project_dir=base)

    @property
    def batch_dir(self) -> Path:
        """The dump directory for this batch (``<project_dir>/dump``)."""
        return self.project_dir / DEFAULT_OUTPUT_DIR_NAME

    @property
    def raw_dir(self) -> Path:
        """Where exported raw data lives (``<batch_dir>/raw_data``)."""
        return self.batch_dir / RAW_SUBDIR

    def journal_file(self, suffix: str = ".json") -> Path:
        """Path to the journal file for this batch (not created here)."""
        return self.project_dir / f"cellpy_batch_{self.name}{suffix}"

    def all_dirs(self) -> tuple[Path, ...]:
        """Every directory this layout owns, parents first."""
        return (self.project_dir, self.batch_dir, self.raw_dir)


def ensure_dirs(paths: BatchPaths) -> tuple[Path, ...]:
    """Create every directory in ``paths`` (idempotent). The *only* mkdir.

    Returns the directories that were ensured (parents first).
    """
    for directory in paths.all_dirs():
        directory.mkdir(parents=True, exist_ok=True)
    return paths.all_dirs()
