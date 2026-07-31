"""The Collection product.

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
    #: True only when group-averaging actually ran (a group had >= 2 cells and
    #: emitted the long ``mean``/``std`` frame). ``group_it=True`` that fell back
    #: to a wide, non-averaged frame stays False.
    grouped: bool = False


@dataclass
class Collection:
    """A tidy collected frame plus its provenance."""

    data: pl.DataFrame
    kind: str  # "summary" | "cycles" | "ica" | custom
    name: str
    meta: CollectionMeta

    #: collection kind -> ``collected_plot`` family (#657).
    _FAMILY = {"summary": "summary", "cycles": "cycles", "ica": "ica"}

    @property
    def is_grouped(self) -> bool:
        """True when group-averaging actually happened (long ``mean``/``std``
        frame). ``group_it=True`` that fell back to wide (a group with < 2 cells)
        stays False -- so callers can adapt labels/plotting without sniffing for
        a ``mean`` column."""
        return self.meta.grouped

    def to_wide(
        self, values: str, index: str = "cycle_num", columns: str = "cell"
    ) -> pl.DataFrame:
        """Explicit, tested pivot to wide layout (replaces the try/except pivots)."""
        return self.data.pivot(values=values, index=index, on=columns)

    def plot(self, *, family_kind: str | None = None, **kwargs):
        """Draw the collection via :func:`cellpy.plotting.collected_plot`.

        The drawing lives in ``cellpy.plotting``; a collection just hands
        it the tidy frame and the family. The only reconciliation needed is the
        summary family's cycle column, which the summary plotter spells
        ``cycle`` (capacity/ICA curves keep ``cycle_num`` / ``cycle``).

        For summary collections (Plotly), pass ``share_y`` / ``match_axes`` and
        optional ``y_ranges={variable: [lo, hi], ...}`` for per-facet y-limits
        (see :func:`cellpy.plotting.collected.summary_plotter`). App chrome:
        ``plotly_template``, ``layout_updates``, ``y_label_mapper``,
        ``height`` / ``height_per_panel``.
        """
        from cellpy.plotting import collected_plot

        family = family_kind or self._FAMILY.get(self.kind, "cycles")
        frame = self.data.to_pandas()
        if family == "summary" and "cycle_num" in frame.columns:
            frame = frame.rename(columns={"cycle_num": "cycle"})
        return collected_plot(frame, family_kind=family, **kwargs)

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
            elif fmt == "json":
                self.data.write_json(path)
            elif fmt == "xlsx":
                self._write_xlsx(path)
            else:
                raise ValueError(
                    f"unsupported collection format {fmt!r} "
                    "(supported: parquet, csv, json, xlsx)"
                )
            written.append(path)

        meta_path = directory / f"{self.name}.meta.json"
        meta_path.write_text(json.dumps(asdict(self.meta), indent=2), encoding="utf-8")
        written.append(meta_path)
        return written

    def _write_xlsx(self, path: Path) -> None:
        """Write the frame as xlsx via polars (xlsxwriter), falling back to
        pandas (openpyxl); raise a clear error if no Excel engine is installed."""
        try:
            self.data.write_excel(path)
        except (ModuleNotFoundError, ImportError):
            try:
                self.data.to_pandas().to_excel(path, index=False)
            except (ModuleNotFoundError, ImportError) as exc:
                raise RuntimeError(
                    "saving a collection as xlsx needs an Excel writer -- install "
                    "'xlsxwriter' or 'openpyxl'"
                ) from exc


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
