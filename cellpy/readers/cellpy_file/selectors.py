"""Load selector and limits for cellpy-file (HDF5) reads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cellpy.readers.data_structures import Data


@dataclass(frozen=True)
class LoadSelector:
    max_cycle: int | None = None

    @classmethod
    def from_dict(cls, selector: dict | None) -> "LoadSelector":
        if not selector:
            return cls(max_cycle=None)
        return cls(max_cycle=selector.get("max_cycle"))


@dataclass
class LoadLimits:
    limit_loaded_cycles: int | None = None
    limit_data_points: int | None = None


@dataclass
class LoadResult:
    data: "Data"
    file_version: int
    limit_data_points: int | None
    limit_loaded_cycles: int | None

    @classmethod
    def from_limits(
        cls, data: "Data", file_version: int, limits: LoadLimits
    ) -> "LoadResult":
        return cls(
            data=data,
            file_version=file_version,
            limit_data_points=limits.limit_data_points,
            limit_loaded_cycles=limits.limit_loaded_cycles,
        )
