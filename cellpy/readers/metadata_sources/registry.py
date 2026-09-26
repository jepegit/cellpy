"""Metadata-source discovery via entry points, and the null-object `fetch_meta`.

A source package declares itself and cellpy finds it — no import of cellpy at
registration time, no base class::

    # in the adapter package's pyproject.toml
    [project.entry-points."cellpy.metadata_sources"]
    batbase = "cellpy_connectors.batbase_source:BatBaseMetadataSource"

The entry point may name a class (instantiated with no arguments) or a
zero-argument factory returning a source. Discovery is lazy: ``import cellpy``
never scans or imports third-party code.

Failure posture mirrors the loader registry: a plugin that cannot be imported
or does not satisfy the contract is skipped with a warning, it does not take
cellpy down. `fetch_meta` adds the cellpy law for external data — an
unreachable or unknown source yields an **empty layer**, never a failed load —
with one deliberate exception: `MetadataSourceAuthError` propagates, because a
refused token is a configuration problem the user needs to see.
"""

from __future__ import annotations

import datetime
import logging
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Callable, Iterable

from cellpy.readers.metadata_sources.contract import (
    MetadataSource,
    MetadataSourceAuthError,
    MetadataSourceError,
    MetaQuery,
    MetaRecord,
    UnknownMetadataSource,
    validate_record,
)

ENTRY_POINT_GROUP = "cellpy.metadata_sources"

#: name -> source class or zero-arg factory
_REGISTRY: dict[str, Callable[[], MetadataSource]] | None = None
#: name -> instantiated source (built on first use)
_INSTANCES: dict[str, MetadataSource] = {}


def _validate_factory(factory: Any, source: str) -> None:
    name = getattr(factory, "name", None)
    if not isinstance(name, str) or not name:
        raise MetadataSourceError(
            f"{source}: {factory!r} must declare a non-empty class-level "
            "``name`` so the registry can route on it."
        )
    # ``issubclass`` is unavailable for Protocols with data members (``name``),
    # so check the one method structurally.
    if isinstance(factory, type) and not callable(getattr(factory, "fetch", None)):
        raise MetadataSourceError(
            f"{source}: {factory!r} does not satisfy the MetadataSource "
            "contract; it must provide fetch(query)."
        )
    if not isinstance(factory, type) and not callable(factory):
        raise MetadataSourceError(f"{source}: {factory!r} is not a class or factory.")


def _iter_entry_points() -> Iterable[EntryPoint]:
    return entry_points(group=ENTRY_POINT_GROUP)


def _discover() -> dict[str, Callable[[], MetadataSource]]:
    found: dict[str, Callable[[], MetadataSource]] = {}
    for entry_point in _iter_entry_points():
        try:
            factory = entry_point.load()
        except Exception as exc:
            logging.warning(
                "could not load metadata source %r from %s: %s",
                entry_point.name,
                getattr(entry_point, "value", "?"),
                exc,
            )
            continue
        try:
            _validate_factory(factory, f"entry point {entry_point.name!r}")
        except MetadataSourceError as exc:
            logging.warning("%s", exc)
            continue
        key = factory.name
        if key in found:
            logging.warning(
                "metadata source %r declared more than once; keeping %r", key, found[key]
            )
            continue
        found[key] = factory
    return found


def get_registry(*, refresh: bool = False) -> dict[str, Callable[[], MetadataSource]]:
    """Registered source factories keyed by ``name``. Discovers on first use."""
    global _REGISTRY
    if _REGISTRY is None or refresh:
        _REGISTRY = _discover()
        _INSTANCES.clear()
    return dict(_REGISTRY)


def clear_registry() -> None:
    """Forget discovery results (tests, and after installing a plugin)."""
    global _REGISTRY
    _REGISTRY = None
    _INSTANCES.clear()


def register(source: Any) -> None:
    """Register a source class, factory or instance directly.

    For tests and notebook-defined sources. Packaged sources should declare
    an entry point instead so they are found without a call. An *instance*
    is registered as-is (useful for a pre-configured client).
    """
    get_registry()
    assert _REGISTRY is not None
    if isinstance(source, type) or not isinstance(source, MetadataSource):
        _validate_factory(source, "direct registration")
        _REGISTRY[source.name] = source
        _INSTANCES.pop(source.name, None)
        return
    name = getattr(source, "name", None)
    if not isinstance(name, str) or not name:
        raise MetadataSourceError("direct registration: instance has no ``name``")
    _REGISTRY[name] = lambda: source
    _INSTANCES[name] = source


def names() -> tuple[str, ...]:
    """Registered source names, sorted."""
    return tuple(sorted(get_registry()))


def get_source(name: str) -> MetadataSource:
    """The source registered as ``name``, instantiated once and cached.

    Raises:
        UnknownMetadataSource: nothing is registered under ``name``.
        MetadataSourceError: the factory failed or returned a non-source.
    """
    registry = get_registry()
    if name not in registry:
        known = ", ".join(names()) or "none"
        raise UnknownMetadataSource(
            f"no metadata source named {name!r} is registered (known: {known}). "
            "Install the adapter package or register() one directly."
        )
    if name not in _INSTANCES:
        try:
            instance = registry[name]()
        except MetadataSourceError:
            raise
        except Exception as exc:
            raise MetadataSourceError(
                f"metadata source {name!r} could not be created: {exc}"
            ) from exc
        if not isinstance(instance, MetadataSource):
            raise MetadataSourceError(
                f"metadata source {name!r} factory returned {instance!r}, "
                "which does not provide fetch(query)."
            )
        _INSTANCES[name] = instance
    return _INSTANCES[name]


def fetch_meta(
    source: str | MetadataSource,
    query: MetaQuery | str,
    *,
    strict: bool = False,
) -> tuple[MetaRecord, ...]:
    """Ask one source for metadata; degrade to ``()`` when it cannot answer.

    Args:
        source: a registered name or a source object.
        query: a `MetaQuery`, or a bare string taken as ``MetaQuery(key)``.
        strict: re-raise every failure instead of returning an empty layer.
            Auth errors are raised regardless.

    Returns:
        Validated records with ``fetched_at`` filled, or ``()``.
    """
    if isinstance(query, str):
        query = MetaQuery(key=query)

    try:
        obj = get_source(source) if isinstance(source, str) else source
        raw_records = obj.fetch(query)
        label = getattr(obj, "name", repr(obj))
    except MetadataSourceAuthError:
        raise
    except Exception as exc:
        if strict:
            if isinstance(exc, MetadataSourceError):
                raise
            raise MetadataSourceError(
                f"metadata source {source!r} failed for {query.describe()}: {exc}"
            ) from exc
        logging.warning(
            "metadata source %r unavailable for %s (%s: %s); continuing without it",
            source if isinstance(source, str) else getattr(source, "name", source),
            query.describe(),
            type(exc).__name__,
            exc,
        )
        return ()

    if raw_records is None:
        raw_records = ()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    records: list[MetaRecord] = []
    for record in raw_records:
        try:
            validate_record(record, source=f"metadata source {label!r}")
        except MetadataSourceError as exc:
            if strict:
                raise
            logging.warning("%s; dropping the record", exc)
            continue
        if record.fetched_at is None:
            from dataclasses import replace

            record = replace(record, fetched_at=now)
        records.append(record)
    logging.debug(
        "metadata source %r answered %s with %d record(s)", label, query.describe(), len(records)
    )
    return tuple(records)
