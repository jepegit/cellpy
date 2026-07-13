"""Load selector and limits for cellpy-file (HDF5) reads."""

from __future__ import annotations

from dataclasses import dataclass


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
