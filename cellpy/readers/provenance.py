"""Provenance stamping — the framework's half of metadata (#562).

A loader knows what the file *says*. Only the framework knows where the file
came from, when it was read and what identity the resulting cell was given, so
those fields are stamped here and a draft that arrives carrying them is a
contract violation (architecture plan §5.1.3, enforced by the conformance kit).

Two identifiers, deliberately different:

``source_uuid``
    A stable hash of *file identity*. The same file yields the same value on
    every load and on every machine, so "have I already loaded this?" and "is
    this the same raw file the cellpy file was built from?" are answerable.

``uuid``
    Identity of *this cell object*, minted once at first load and then
    preserved through save, load and merge. Two loads of the same file are two
    cells and get different values.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import uuid as uuid_module
from pathlib import Path
from typing import Any

#: Read in chunks: raw files run to hundreds of MB and hashing should not
#: require holding one in memory.
_CHUNK = 1024 * 1024

#: How much of the file identifies it. Hashing a whole multi-GB file to answer
#: "same file?" is not worth the wall time; the head plus the size is a strong
#: enough discriminator for provenance, and it is stable across machines.
_IDENTITY_BYTES = 1024 * 1024


def file_identity_hash(source: Path | str) -> str | None:
    """A stable identity hash for a raw file, or None if unreadable.

    Deliberately *not* a full-content checksum — see ``_IDENTITY_BYTES``. Two
    different files sharing both a 1 MB head and an exact byte size would
    collide; that is acceptable for provenance, and it is not used as a
    security or integrity control.
    """
    path = Path(source)
    try:
        size = path.stat().st_size
        digest = hashlib.sha256()
        digest.update(str(size).encode("utf-8"))
        with path.open("rb") as handle:
            remaining = _IDENTITY_BYTES
            while remaining > 0:
                chunk = handle.read(min(_CHUNK, remaining))
                if not chunk:
                    break
                digest.update(chunk)
                remaining -= len(chunk)
        return digest.hexdigest()
    except OSError as exc:
        # A missing or unreadable source should not fail a load that otherwise
        # succeeded (e.g. loading from a cellpy file whose raw has moved).
        logging.debug("could not hash %s for provenance: %s", path, exc)
        return None


def stamp_provenance(
    test_meta: Any,
    *,
    source: Path | str,
    source_type: str,
    source_kind: str = "file",
    raw_file_names: list[str] | None = None,
    loaded_datetime: datetime.datetime | None = None,
) -> Any:
    """Fill the provenance fields on a draft ``TestMeta``.

    Args:
        test_meta: the loader's draft, mutated in place.
        source: the raw file this test came from.
        source_type: the instrument/loader name (``"maccor_txt"``).
        source_kind: ``"file"`` or ``"db"``.
        raw_file_names: override for multi-file loads; defaults to ``source``.
        loaded_datetime: override for reproducible tests; defaults to now, UTC.

    Returns:
        The same object, for chaining.
    """
    path = Path(source)
    stamps = {
        "source_kind": source_kind,
        "source_type": source_type,
        "source_uri": str(path),
        "source_uuid": file_identity_hash(path),
        "raw_file_names": raw_file_names or [path.name],
        "loaded_datetime": loaded_datetime
        or datetime.datetime.now(datetime.timezone.utc),
    }

    for name, value in stamps.items():
        if value is not None and hasattr(test_meta, name):
            setattr(test_meta, name, value)
    return test_meta


def new_cell_uuid() -> str:
    """Mint the identity for a freshly loaded cell.

    Preserved through save/load/merge — see ``preserve_cell_uuid``.
    """
    return str(uuid_module.uuid4())


def preserve_cell_uuid(target: Any, *sources: Any) -> str | None:
    """Carry an existing cell uuid onto ``target``, or mint one.

    Merging keeps the *first* uuid it finds rather than minting a new one: the
    merged object is a continuation of that cell, and a fresh identity would
    break the link back to files already saved from it.
    """
    for source in sources:
        existing = getattr(source, "uuid", None) if source is not None else None
        if existing:
            if hasattr(target, "uuid"):
                target.uuid = existing
            return existing

    minted = new_cell_uuid()
    if hasattr(target, "uuid"):
        target.uuid = minted
    return minted
