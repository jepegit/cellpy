"""The external metadata-source contract (#784, metadata plan Step 7).

A lab's system of record — a database, a LIMS, an HTTP API such as BatBase —
knows things about a cell that the cycler file never will: its mass, loading,
project, who built it. cellpy pulls that in through one small contract, so any
store can plug in the same way and cellpy never depends on one lab's API.

The contract mirrors the loader contract
(`cellpy.readers.instruments.contract`): a `typing.Protocol` third parties
satisfy structurally (no cellpy base class), a `MetaRecord` that is exactly the
mapping shape `MetaResolver` already ingests, and an entry-point registry
(`cellpy.readers.metadata_sources.registry`) that finds sources without a
registration call.

Rules a source must keep (`testing.check_metadata_source` enforces them):

- ``fetch`` is **read-only** and returns ``()`` for "not found". It never
  raises on an unknown key. Connectivity and auth problems *may* raise;
  `fetch_meta` turns the former into an empty layer (null object) and lets
  the latter through, because a wrong token is the user's to fix.
- Records carry only fields the source really knows. ``None`` is not "unset"
  here; leave the key out.
- Records never pre-fill cellpy provenance (`uuid`, `source_kind`, ...); that
  is the framework's to stamp.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping, Protocol, runtime_checkable

from cellpy.exceptions import Error

#: Provenance a source may never fill; the framework stamps these.
PROVENANCE_FIELDS: frozenset[str] = frozenset(
    {
        "uuid",
        "source_kind",
        "source_type",
        "source_uri",
        "source_uuid",
        "raw_file_names",
        "loaded_datetime",
    }
)


class MetadataSourceError(Error):
    """A metadata source could not answer (unreachable, malformed reply, ...)."""


class MetadataSourceAuthError(MetadataSourceError):
    """The source refused the credentials. Not swallowed by the null object."""


class UnknownMetadataSource(MetadataSourceError):
    """No registered source has that name."""


@dataclass(frozen=True)
class MetaQuery:
    """What to look up.

    Args:
        key: the lookup value — a cell name, a BatBase tag, a serial, an
            external id — as the source understands it.
        kind: what ``key`` is. ``"cell_name"`` (default), ``"tag"``,
            ``"serial"``, ``"external_id"``, ``"uuid"``; sources document
            which kinds they accept and return ``()`` for kinds they do not.
        project: optional project scope.
        extra: source-specific filters, passed through untouched.
    """

    key: str | None = None
    kind: str = "cell_name"
    project: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra or {}))

    def describe(self) -> str:
        parts = [f"{self.kind}={self.key!r}"]
        if self.project:
            parts.append(f"project={self.project!r}")
        parts.extend(f"{k}={v!r}" for k, v in sorted(self.extra.items()))
        return ", ".join(parts)


@dataclass(frozen=True)
class MetaRecord:
    """One answer from a source: draft metadata plus the back-link to it.

    ``cell`` and ``test`` are plain ``{field: value}`` mappings over
    ``CellMeta`` / ``TestMeta`` field names — the shape `MetaResolver`
    ingests as its journal/db layer. Only fields the source knows appear.

    Args:
        source_name: the registered source name (``"batbase"``).
        external_id: the source's own id for the matched entity, if any.
        source_uri: where the record can be re-fetched or inspected.
        cell: ``CellMeta`` draft mapping.
        test: ``TestMeta`` draft mapping.
        fetched_at: ISO-8601 timestamp; `fetch_meta` fills it when left None.
        raw: the source's original payload, for debugging. Not persisted.
    """

    source_name: str
    external_id: str | None = None
    source_uri: str | None = None
    cell: Mapping[str, Any] = field(default_factory=dict)
    test: Mapping[str, Any] = field(default_factory=dict)
    fetched_at: str | None = None
    raw: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "cell", dict(self.cell or {}))
        object.__setattr__(self, "test", dict(self.test or {}))

    @property
    def fields(self) -> tuple[str, ...]:
        """Every metadata field this record has a value for."""
        return tuple(sorted(set(self.cell) | set(self.test)))

    def is_empty(self) -> bool:
        return not self.cell and not self.test

    def link(self) -> "ExternalLink":
        return ExternalLink(
            source_name=self.source_name,
            external_id=self.external_id,
            source_uri=self.source_uri,
            fetched_at=self.fetched_at,
            fields=self.fields,
        )


@dataclass(frozen=True)
class ExternalLink:
    """The persisted back-link from a cellpy cell to a source record.

    Stored per source on the cell (``Data.external_links``) and in the v9
    ``meta.json`` under ``"external_links"``, so a re-fetch is deterministic
    and "where did this mass come from?" has an answer after reload.
    """

    source_name: str
    external_id: str | None = None
    source_uri: str | None = None
    fetched_at: str | None = None
    #: metadata fields this source supplied when it was applied
    fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "external_id": self.external_id,
            "source_uri": self.source_uri,
            "fetched_at": self.fetched_at,
            "fields": list(self.fields),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExternalLink":
        return cls(
            source_name=str(payload.get("source_name", "")),
            external_id=payload.get("external_id"),
            source_uri=payload.get("source_uri"),
            fetched_at=payload.get("fetched_at"),
            fields=tuple(payload.get("fields") or ()),
        )


@runtime_checkable
class MetadataSource(Protocol):
    """What a metadata source must provide. Structural; no base class.

    Attributes:
        name: the registry key (``"batbase"``). Class level.
    """

    name: ClassVar[str]

    def fetch(self, query: MetaQuery) -> tuple[MetaRecord, ...]:
        """Look up metadata. Read-only.

        Returns every record matching ``query``; ``()`` when nothing matched.
        Never raise for "unknown key". May raise `MetadataSourceError`
        (connectivity) or `MetadataSourceAuthError` (credentials).
        """
        ...


@runtime_checkable
class SupportsMetadataPush(Protocol):
    """Optional: a source that can take a record back. Explicit opt-in only.

    Declared here so the shape is pinned; nothing in cellpy calls it yet
    (Epic M stage M3). A push is side-effecting and must only ever happen on
    an explicit user call, never as part of a load.
    """

    def register(self, record: MetaRecord) -> str:
        """Push ``record`` to the source and return the source's id for it."""
        ...


def validate_record(
    record: Any,
    *,
    cell_fields: Mapping[str, Any] | frozenset[str] | tuple[str, ...] | None = None,
    test_fields: Mapping[str, Any] | frozenset[str] | tuple[str, ...] | None = None,
    source: str = "metadata source",
) -> MetaRecord:
    """Check that ``record`` keeps the contract, and return it.

    Raises `MetadataSourceError` naming the broken promise. Unknown field
    names are an error rather than silently dropped: a typo in an adapter's
    field map should fail its conformance test, not lose a lab's mass.
    """
    if not isinstance(record, MetaRecord):
        raise MetadataSourceError(
            f"{source}: fetch() must return MetaRecord instances, got {type(record)!r}"
        )
    if not record.source_name:
        raise MetadataSourceError(f"{source}: MetaRecord.source_name is empty")

    if cell_fields is None or test_fields is None:
        known_cell, known_test = _known_meta_fields()
        cell_fields = cell_fields if cell_fields is not None else known_cell
        test_fields = test_fields if test_fields is not None else known_test

    unknown_cell = sorted(set(record.cell) - set(cell_fields))
    unknown_test = sorted(set(record.test) - set(test_fields))
    if unknown_cell or unknown_test:
        raise MetadataSourceError(
            f"{source}: MetaRecord uses field names that are not metadata fields: "
            f"cell={unknown_cell} test={unknown_test}"
        )
    stamped = sorted((set(record.cell) | set(record.test)) & PROVENANCE_FIELDS)
    if stamped:
        raise MetadataSourceError(
            f"{source}: MetaRecord pre-fills provenance {stamped}; "
            "that is the framework's to stamp."
        )
    nones = sorted(k for k, v in {**record.cell, **record.test}.items() if v is None)
    if nones:
        raise MetadataSourceError(
            f"{source}: MetaRecord carries None for {nones}; leave unknown fields out."
        )
    return record


def _known_meta_fields() -> tuple[frozenset[str], frozenset[str]]:
    from dataclasses import fields as dc_fields

    from cellpycore.metadata.models import CellMeta, TestMeta

    return (
        frozenset(f.name for f in dc_fields(CellMeta)),
        frozenset(f.name for f in dc_fields(TestMeta)) - {"cell"},
    )
