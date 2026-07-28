"""Batch run results.

"Errors are data": a batch run returns a :class:`BatchResult` with a per-cell
outcome, timing and captured exception, instead of the legacy mix of printing,
partial ``errors`` lists and aborting. Printing/raising is the caller's policy
(``result.raise_if_failed()`` for strict mode).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator

import polars as pl

from cellpy.exceptions import CellpyError


class CellOutcome(str, Enum):
    LOADED = "loaded"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchLoadError(CellpyError):
    """Raised by :meth:`BatchResult.raise_if_failed` when cells failed."""


@dataclass
class CellResult:
    """The outcome of loading one cell."""

    label: str
    outcome: CellOutcome
    cell: Any | None = None
    source: str | None = None  # "cellpy" | "raw" | None
    seconds: float = 0.0
    error: BaseException | None = None

    @property
    def ok(self) -> bool:
        return self.outcome == CellOutcome.LOADED


@dataclass
class BatchResult:
    """The outcome of a batch run: one :class:`CellResult` per cell."""

    results: list[CellResult] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self) -> Iterator[CellResult]:
        return iter(self.results)

    def __getitem__(self, label: str) -> CellResult:
        for result in self.results:
            if result.label == label:
                return result
        raise KeyError(label)

    @property
    def loaded(self) -> list[CellResult]:
        return [r for r in self.results if r.outcome == CellOutcome.LOADED]

    @property
    def failed(self) -> list[CellResult]:
        return [r for r in self.results if r.outcome == CellOutcome.FAILED]

    @property
    def skipped(self) -> list[CellResult]:
        return [r for r in self.results if r.outcome == CellOutcome.SKIPPED]

    def cells(self) -> dict[str, Any]:
        """Mapping of label -> loaded cell, successful cells only."""
        return {r.label: r.cell for r in self.loaded}

    def raise_if_failed(self) -> "BatchResult":
        """Strict mode: raise if any cell failed; otherwise return self."""
        if self.failed:
            labels = ", ".join(r.label for r in self.failed)
            raise BatchLoadError(f"{len(self.failed)} cell(s) failed to load: {labels}")
        return self

    def report(self) -> pl.DataFrame:
        """A tidy per-cell outcome frame (the dataframe ``errors`` only hinted at)."""
        return pl.DataFrame(
            {
                "cell": [r.label for r in self.results],
                "outcome": [r.outcome.value for r in self.results],
                "source": [r.source for r in self.results],
                "seconds": [r.seconds for r in self.results],
                "error": [None if r.error is None else str(r.error) for r in self.results],
            }
        )
