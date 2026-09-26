"""Pluggable external metadata sources (#784).

Public surface::

    from cellpy.readers.metadata_sources import (
        MetadataSource, SupportsMetadataPush,   # the Protocols
        MetaQuery, MetaRecord, ExternalLink,    # the data shapes
        fetch_meta, get_source, register, names,
        MetadataSourceError, MetadataSourceAuthError, UnknownMetadataSource,
    )

See `cellpy.readers.metadata_sources.contract` for the promises,
`cellpy.readers.metadata_sources.registry` for discovery and the null-object
`fetch_meta`, and `cellpy.readers.metadata_sources.testing` for the
conformance kit adapters run.
"""

from cellpy.readers.metadata_sources.contract import (
    PROVENANCE_FIELDS,
    ExternalLink,
    MetadataSource,
    MetadataSourceAuthError,
    MetadataSourceError,
    MetaQuery,
    MetaRecord,
    SupportsMetadataPush,
    UnknownMetadataSource,
    validate_record,
)
from cellpy.readers.metadata_sources.registry import (
    ENTRY_POINT_GROUP,
    clear_registry,
    fetch_meta,
    get_registry,
    get_source,
    names,
    register,
)

__all__ = [
    "ENTRY_POINT_GROUP",
    "PROVENANCE_FIELDS",
    "ExternalLink",
    "MetaQuery",
    "MetaRecord",
    "MetadataSource",
    "MetadataSourceAuthError",
    "MetadataSourceError",
    "SupportsMetadataPush",
    "UnknownMetadataSource",
    "clear_registry",
    "fetch_meta",
    "get_registry",
    "get_source",
    "names",
    "register",
    "validate_record",
]
