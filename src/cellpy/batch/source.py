"""Build batch journal pages from external metadata-source records (#1107).

A lab database that knows a set of tests (a BatBase tag, a project) can hand
cellpy the journal directly: one `MetaRecord` per test, with the cell
metadata the journal would carry and — when the source records them — the
files to open. Rows whose record has no `FileRef`s go through the same
``filefinder`` search a database-built journal uses; nothing else changes
downstream (`resolve_specs` → runner → store).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Mapping, Sequence

import polars as pl

from cellpy.batch.journal import FILENAME, Journal
from cellpy.parameters.internal_settings import get_headers_journal
from cellpy.readers.metadata_sources import ExternalLink, MetaRecord

hdr_journal = get_headers_journal()

#: ``record.cell`` field → journal column
_CELL_COLUMNS: tuple[tuple[str, str], ...] = (
    ("mass", hdr_journal["mass"]),
    ("area", hdr_journal["area"]),
    ("loading", hdr_journal["loading"]),
    ("nom_cap", hdr_journal["nom_cap"]),
    ("nom_cap_specifics", hdr_journal["nom_cap_specifics"]),
)
#: ``record.test`` field → journal column
_TEST_COLUMNS: tuple[tuple[str, str], ...] = (("cycle_mode", "cycle_mode"),)

#: session key holding ``{label: ExternalLink.to_dict()}``
SESSION_KEY = "external_links"


def record_label(record: MetaRecord, fallback: str) -> str:
    """The journal label for a record: its ``cell_name``, else ``external_id``."""
    name = record.test.get("cell_name") or record.cell.get("cell_name")
    if name:
        return str(name)
    if record.external_id:
        return str(record.external_id)
    return fallback


def default_batch_name(source: str, kind: str, key: str | None) -> str:
    """``batbase_tag_SAL_010`` — a filesystem-safe journal name."""
    parts = [source, kind, key or "all"]
    slug = "_".join(re.sub(r"[^A-Za-z0-9._-]+", "-", str(p)).strip("-") for p in parts)
    return slug or "from_source"


def pages_from_records(
    records: Sequence[MetaRecord],
    *,
    source_name: str,
    file_search: bool = True,
    file_search_kwargs: Mapping[str, Any] | None = None,
) -> tuple[pl.DataFrame, dict[str, dict]]:
    """Turn records into journal pages plus per-label back-links.

    Args:
        records: validated `MetaRecord`s (from `fetch_meta`).
        source_name: registry name of the source (stamped on the links).
        file_search: run ``filefinder`` for rows without file pointers.
            ``False`` leaves their file columns ``None`` (the runner then
            marks those cells FAILED until paths are filled in, #1017).
        file_search_kwargs: forwarded to `_dbengine.find_files`
            (``pre_path``, ``sub_folders``, ``file_list``, ``project`` ...).

    Returns:
        ``(pages, links)`` where ``links`` maps label → ``ExternalLink`` dict
        ready for ``journal.session["external_links"]``.
    """
    labels: list[str] = []
    seen: dict[str, int] = {}
    for i, record in enumerate(records, start=1):
        label = record_label(record, f"cell_{i:03d}")
        if label in seen:
            seen[label] += 1
            label = f"{label}_{seen[label]}"
        else:
            seen[label] = 1
        labels.append(label)

    n = len(records)
    columns: dict[str, list] = {
        FILENAME: labels,
        hdr_journal["label"]: labels,
        hdr_journal["group"]: [1] * n,
        hdr_journal["sub_group"]: list(range(1, n + 1)),
        hdr_journal["selected"]: [True] * n,
    }
    for field_name, column in _CELL_COLUMNS:
        columns[column] = [rec.cell.get(field_name) for rec in records]
    for field_name, column in _TEST_COLUMNS:
        columns[column] = [rec.test.get(field_name) for rec in records]

    raw_names: list[list[str] | None] = []
    cellpy_names: list[str | None] = []
    instruments: list[str | None] = []
    sizes: list[int | None] = []
    mtimes: list[str | None] = []
    links: dict[str, dict] = {}
    needs_search: list[int] = []
    for i, (record, label) in enumerate(zip(records, labels)):
        raws = record.raw_files()
        cellpy_ref = record.cellpy_file()
        uris = [ref.uri for ref in raws]
        raw_names.append(uris or None)
        cellpy_names.append(cellpy_ref.uri if cellpy_ref else None)
        instruments.append(next((ref.loader for ref in raws if ref.loader), None))
        sizes.append(sum(ref.size for ref in raws) if raws and all(ref.size is not None for ref in raws) else None)
        mtimes.append(max((ref.mtime for ref in raws if ref.mtime), default=None))
        used = [*uris, *([cellpy_ref.uri] if cellpy_ref else [])]
        if not used:
            needs_search.append(i)
        link: ExternalLink = record.link(files=used)
        fields = tuple(col for field_name, col in (*_CELL_COLUMNS, *_TEST_COLUMNS) if columns[col][i] is not None)
        from dataclasses import replace

        links[label] = replace(link, source_name=source_name, fields=fields).to_dict()

    columns[hdr_journal["raw_file_names"]] = raw_names
    columns[hdr_journal["cellpy_file_name"]] = cellpy_names
    columns[hdr_journal["instrument"]] = instruments
    if any(s is not None for s in sizes):
        columns["raw_file_size"] = sizes
    if any(m is not None for m in mtimes):
        columns["raw_file_mtime"] = mtimes
    columns["external_id"] = [rec.external_id for rec in records]
    columns["source_uri"] = [rec.source_uri for rec in records]

    if needs_search and file_search:
        _fill_by_search(columns, needs_search, labels, **(file_search_kwargs or {}))
    elif needs_search:
        logging.info(
            "from_source: %d record(s) without file pointers left unsearched " "(file_search=False)",
            len(needs_search),
        )

    pages = pl.DataFrame({col: pl.Series(col, values, strict=False) for col, values in columns.items()})
    return pages, links


def _fill_by_search(columns: dict[str, list], rows: list[int], labels: list[str], **kwargs) -> None:
    """Run the journal-style ``filefinder`` search for the given rows only."""
    import cellpy.config as config
    from cellpy.batch._dbengine import find_files

    default_instrument = getattr(config.instruments, "tester", None)
    info = {
        hdr_journal["filename"]: [labels[i] for i in rows],
        hdr_journal["instrument"]: [columns[hdr_journal["instrument"]][i] or default_instrument for i in rows],
    }
    logging.info("from_source: searching files for %d record(s) without pointers", len(rows))
    found = find_files(info, **kwargs)
    for j, i in enumerate(rows):
        raw = found[hdr_journal["raw_file_names"]][j]
        columns[hdr_journal["raw_file_names"]][i] = list(raw) if raw else None
        columns[hdr_journal["cellpy_file_name"]][i] = found[hdr_journal["cellpy_file_name"]][j] or None


def journal_from_records(
    records: Sequence[MetaRecord],
    *,
    source_name: str,
    name: str,
    project: str,
    file_search: bool = True,
    file_search_kwargs: Mapping[str, Any] | None = None,
) -> Journal:
    """`pages_from_records` wrapped in a `Journal` with the links in ``session``."""
    pages, links = pages_from_records(
        records,
        source_name=source_name,
        file_search=file_search,
        file_search_kwargs=file_search_kwargs,
    )
    journal = Journal(name=name, project=project, pages=pages)
    journal.session[SESSION_KEY] = links
    return journal
