"""Loader discovery and routing via entry points (cellpy 2, issue #210).

Third-party loaders install themselves by declaring an entry point; cellpy
finds them without any registration call and without a shared base class::

    # in the loader package's pyproject.toml
    [project.entry-points."cellpy.loaders"]
    mycycler = "cellpy_mycycler.loader:MyCyclerLoader"

Discovery is **lazy** — the entry-point group is read on first use, not at
import, so ``import cellpy`` neither scans nor imports third-party code.

Failures are contained and loud in the right way: one broken plugin makes that
plugin unavailable with a clear warning, it does not take down cellpy. A
plugin that loads but does not satisfy the contract is rejected at registration
with a message naming what it is missing, rather than failing later inside a
load with something obscure.

Scope note (2026-07-19): the built-in loaders do **not** route through this
registry yet — they still go through the module-globbing
``InstrumentFactory``. Moving them over is part of the loader port (#560),
after they emit ``LoaderResult`` (#559). Until then this registry is the path
for out-of-tree loaders, and the query API below reports both populations.
"""

from __future__ import annotations

import logging
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Iterable

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.contract import InstrumentLoader

ENTRY_POINT_GROUP = "cellpy.loaders"

_REGISTRY: dict[str, type] | None = None

# Attributes the registry routes on; a loader missing any of them cannot be
# registered, because the registry could not place it.
_REQUIRED_CAPABILITIES = ("name", "instrument", "supported_suffixes")


def _validate_capabilities(loader_cls: type, source: str) -> None:
    """Reject a loader the registry could not route, and say why."""
    missing = [
        attribute
        for attribute in _REQUIRED_CAPABILITIES
        if getattr(loader_cls, attribute, None) is None
    ]
    if missing:
        raise LoaderError(
            f"{source}: {loader_cls!r} is missing required loader capability "
            f"metadata {missing}; a loader must declare name, instrument and "
            f"supported_suffixes at class level."
        )

    suffixes = loader_cls.supported_suffixes
    if isinstance(suffixes, str) or not isinstance(suffixes, Iterable):
        raise LoaderError(
            f"{source}: {loader_cls!r}.supported_suffixes must be a tuple of "
            f"suffixes like ('.res',), not {suffixes!r}."
        )
    bad = [s for s in suffixes if not (isinstance(s, str) and s.startswith("."))]
    if bad:
        raise LoaderError(
            f"{source}: {loader_cls!r}.supported_suffixes entries must be "
            f"dotted strings like '.res'; got {bad!r}."
        )

    if not isinstance(loader_cls, type) or not issubclass(loader_cls, InstrumentLoader):
        # runtime_checkable Protocols check methods only, which is exactly the
        # structural check we want here.
        raise LoaderError(
            f"{source}: {loader_cls!r} does not satisfy the InstrumentLoader "
            f"contract; it must provide load() and can_load()."
        )


def _iter_entry_points() -> Iterable[EntryPoint]:
    return entry_points(group=ENTRY_POINT_GROUP)


def _discover() -> dict[str, type]:
    """Load, validate and index every declared loader."""
    found: dict[str, type] = {}
    for entry_point in _iter_entry_points():
        try:
            loader_cls = entry_point.load()
        except Exception as exc:
            # A third-party package we cannot import must not break cellpy for
            # everything else; make it visible and carry on.
            logging.warning(
                "could not load instrument loader %r from %s: %s",
                entry_point.name,
                getattr(entry_point, "value", "?"),
                exc,
            )
            continue

        try:
            _validate_capabilities(loader_cls, f"entry point {entry_point.name!r}")
        except LoaderError as exc:
            logging.warning("%s", exc)
            continue

        key = loader_cls.name
        if key in found:
            logging.warning(
                "instrument loader %r declared more than once; keeping %r",
                key,
                found[key],
            )
            continue
        found[key] = loader_cls
    return found


def get_registry(*, refresh: bool = False) -> dict[str, type]:
    """The registered loaders, keyed by ``name``. Discovers on first use."""
    global _REGISTRY
    if _REGISTRY is None or refresh:
        _REGISTRY = _discover()
    return dict(_REGISTRY)


def clear_registry() -> None:
    """Forget discovery results (tests, and after installing a plugin)."""
    global _REGISTRY
    _REGISTRY = None


def register(loader_cls: type) -> None:
    """Register a loader directly, bypassing entry points.

    For tests and for notebook-defined loaders. Packaged loaders should
    declare an entry point instead so they are found without a call.
    """
    _validate_capabilities(loader_cls, "direct registration")
    get_registry()  # ensure discovery has happened before we add to it
    assert _REGISTRY is not None
    _REGISTRY[loader_cls.name] = loader_cls


def available_loaders() -> dict[str, dict[str, object]]:
    """Describe every registered loader — for ``print_instruments`` and docs."""
    return {
        name: {
            "instrument": loader_cls.instrument,
            "supported_suffixes": tuple(loader_cls.supported_suffixes),
            "module": getattr(loader_cls, "__module__", "?"),
        }
        for name, loader_cls in sorted(get_registry().items())
    }


def find_loader(
    source: Path | None = None,
    *,
    instrument: str | None = None,
) -> type | None:
    """Pick a loader for ``source``, or return None if none applies.

    Routing order (architecture plan §5.3): an explicit ``instrument`` wins;
    otherwise candidates are narrowed by suffix and confirmed with the loader's
    own cheap ``can_load()`` sniff.
    """
    registry = get_registry()

    if instrument is not None:
        by_name = registry.get(instrument)
        if by_name is not None:
            return by_name
        by_family = [
            cls for cls in registry.values() if cls.instrument == instrument
        ]
        if by_family:
            return by_family[0]
        return None

    if source is None:
        return None

    suffix = Path(source).suffix.lower()
    candidates = [
        cls for cls in registry.values() if suffix in tuple(cls.supported_suffixes)
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    for cls in candidates:
        try:
            if cls().can_load(Path(source)):
                return cls
        except Exception as exc:
            # A misbehaving sniff disqualifies its loader, nothing more.
            logging.warning("can_load() failed for %r: %s", cls, exc)
    return None
