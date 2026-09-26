"""Conformance kit for metadata sources.

Ships with cellpy so an adapter can prove it keeps the contract without
reverse-engineering cellpy's internals::

    from cellpy.readers.metadata_sources.testing import check_metadata_source

    def test_batbase_source_conforms(fake_batbase):
        check_metadata_source(
            BatBaseMetadataSource(client=fake_batbase),
            known=MetaQuery(key="SAL_010", kind="tag"),
            unknown=MetaQuery(key="does-not-exist", kind="tag"),
        )

Every check corresponds to a promise in `contract`; failures raise
`AssertionError` naming the broken promise. Run it against an in-process fake
of the store, not the live one — the kit checks the adapter, not the network.
"""

from __future__ import annotations

from typing import Any

from cellpy.readers.metadata_sources.contract import (
    MetadataSource,
    MetadataSourceError,
    MetaQuery,
    MetaRecord,
    validate_record,
)
from cellpy.readers.metadata_sources.registry import _validate_factory


def check_capabilities(source: Any) -> None:
    """The source declares a ``name`` and provides ``fetch``."""
    try:
        _validate_factory(type(source) if not isinstance(source, type) else source, "conformance")
    except MetadataSourceError as exc:
        raise AssertionError(str(exc)) from exc
    assert callable(getattr(source, "fetch", None)), (
        f"{source!r} does not satisfy MetadataSource (needs fetch(query))"
    )
    if not isinstance(source, type):
        assert isinstance(source, MetadataSource), f"{source!r} is not a MetadataSource"


def check_unknown_key_is_empty(source: MetadataSource, unknown: MetaQuery) -> None:
    """An unknown key returns ``()`` — it never raises."""
    try:
        result = source.fetch(unknown)
    except Exception as exc:  # noqa: BLE001 - the point is to report it
        raise AssertionError(
            f"fetch() raised {type(exc).__name__} for an unknown key "
            f"({unknown.describe()}); the contract says return ()"
        ) from exc
    assert isinstance(result, tuple), f"fetch() must return a tuple, got {type(result)!r}"
    assert result == (), f"unknown key {unknown.describe()} returned {len(result)} record(s)"


def check_known_key_records(source: MetadataSource, known: MetaQuery) -> tuple[MetaRecord, ...]:
    """A known key returns ≥1 well-formed records that only use real fields."""
    result = source.fetch(known)
    assert isinstance(result, tuple), f"fetch() must return a tuple, got {type(result)!r}"
    assert result, f"known key {known.describe()} returned no records"
    for record in result:
        try:
            validate_record(record, source="conformance")
        except MetadataSourceError as exc:
            raise AssertionError(str(exc)) from exc
        assert record.source_name == source.name, (
            f"record.source_name {record.source_name!r} != source.name {source.name!r}"
        )
        assert not record.is_empty(), "a returned record carries no metadata at all"
    return result


def check_deterministic(source: MetadataSource, known: MetaQuery) -> None:
    """Two fetches of the same key agree (ignoring fetched_at / raw)."""

    def strip(records: tuple[MetaRecord, ...]) -> list[tuple[Any, ...]]:
        return [
            (r.source_name, r.external_id, r.source_uri, sorted(r.cell.items()), sorted(r.test.items()))
            for r in records
        ]

    first, second = source.fetch(known), source.fetch(known)
    assert strip(first) == strip(second), "fetch() is not deterministic for the same query"


def check_metadata_source(
    source: MetadataSource,
    *,
    known: MetaQuery,
    unknown: MetaQuery,
) -> tuple[MetaRecord, ...]:
    """Run every conformance check. Returns the records for ``known``."""
    check_capabilities(source)
    check_unknown_key_is_empty(source, unknown)
    records = check_known_key_records(source, known)
    check_deterministic(source, known)
    return records


class DictMetadataSource:
    """A source backed by a dict — for tests, notebooks and adapter fixtures.

    ``rows`` maps ``(kind, key)`` or just ``key`` to a ``MetaRecord`` (or a
    tuple of them). Anything else → ``()``.
    """

    name = "dict"

    def __init__(self, rows: dict[Any, MetaRecord | tuple[MetaRecord, ...]], name: str = "dict") -> None:
        self.rows = rows
        self.name = name
        self.queries: list[MetaQuery] = []

    def fetch(self, query: MetaQuery) -> tuple[MetaRecord, ...]:
        self.queries.append(query)
        hit = self.rows.get((query.kind, query.key), self.rows.get(query.key))
        if hit is None:
            return ()
        return tuple(hit) if isinstance(hit, tuple) else (hit,)
