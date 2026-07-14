"""Annotated types for the cellpy config stack."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer

from cellpy.internals.connections import OtherPath

LimitLoadedCycles = int | tuple[int, int] | list[int] | None


def _coerce_otherpath(value: Any) -> OtherPath:
    if isinstance(value, OtherPath):
        return value
    return OtherPath(value)


def _serialize_otherpath(value: OtherPath) -> str:
    return str(value).replace("\\", "/")


OtherPathField = Annotated[
    OtherPath,
    BeforeValidator(_coerce_otherpath),
    PlainSerializer(_serialize_otherpath, return_type=str),
]


def _coerce_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value
    return Path(value)


def _serialize_path(value: Path) -> str:
    return value.as_posix()


PathField = Annotated[
    Path,
    BeforeValidator(_coerce_path),
    PlainSerializer(_serialize_path, return_type=str),
]
