"""The Collection product (collectors redesign, #705).

A collection is a *product, not a side effect*: a tidy frame plus provenance
(what was collected, from which batch, with which options, by which cellpy
version, when). It can be saved, re-loaded and re-plotted without
re-collecting -- ``meta.json`` next to the data makes collections reproducible
artifacts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import polars as pl


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cellpy_version() -> str:
    try:
        import cellpy

        return getattr(cellpy, "__version__", "unknown")
    except Exception:  # noqa: BLE001
        return "unknown"


@dataclass
class CollectionMeta:
    """Provenance for a :class:`Collection`."""

    kind: str
    batch_name: str | None = None
    options: dict = field(default_factory=dict)
    cellpy_version: str = field(default_factory=_cellpy_version)
    created_utc: str = field(default_factory=_now_utc)
    cells_included: list[str] = field(default_factory=list)
    cells_skipped: list[str] = field(default_factory=list)


@dataclass
class Collection:
    """A tidy collected frame plus its provenance."""

    data: pl.DataFrame
    kind: str  # "summary" | "cycles" | "ica" | custom
    name: str
    meta: CollectionMeta

    def to_wide(
        self, values: str, index: str = "cycle_num", columns: str = "cell"
    ) -> pl.DataFrame:
        """Explicit, tested pivot to wide layout (replaces the try/except pivots)."""
        return self.data.pivot(values=values, index=index, on=columns)

    def save(
        self,
        directory: Path | str | None = None,
        formats: tuple[str, ...] = ("parquet", "csv"),
    ) -> list[Path]:
        """Save the frame (+ ``meta.json``). No cwd fallback -- ``directory`` is explicit."""
        if directory is None:
            raise ValueError("save() needs an explicit directory (no cwd fallback)")
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []
        for fmt in formats:
            path = directory / f"{self.name}.{fmt}"
            if fmt == "parquet":
                self.data.write_parquet(path)
            elif fmt == "csv":
                self.data.write_csv(path)
            else:
                raise ValueError(f"unsupported collection format {fmt!r}")
            written.append(path)

        meta_path = directory / f"{self.name}.meta.json"
        meta_path.write_text(json.dumps(asdict(self.meta), indent=2), encoding="utf-8")
        written.append(meta_path)
        return written


def load_collection(path: Path | str) -> Collection:
    """Load a saved collection (parquet/csv frame + ``meta.json`` if present)."""
    path = Path(path)
    if path.suffix == ".parquet":
        data = pl.read_parquet(path)
    elif path.suffix == ".csv":
        data = pl.read_csv(path)
    else:
        raise ValueError(f"cannot load collection from {path.suffix!r}")

    meta_path = path.with_suffix("").with_suffix(".meta.json")
    if meta_path.is_file():
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        meta = CollectionMeta(**raw)
    else:
        meta = CollectionMeta(kind="unknown")
    return Collection(data=data, kind=meta.kind, name=path.stem, meta=meta)
