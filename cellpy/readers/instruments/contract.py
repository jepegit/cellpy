"""The instrument-loader contract (cellpy 2, issue #210).

One formal contract every loader satisfies — built-in or third-party — so the
framework can discover, validate and route loaders without knowing anything
about the vendor formats behind them.

The contract is a :class:`typing.Protocol`, **not** a base class. A third-party
loader inherits nothing and imports nothing from cellpy; conformance is
structural. That is what makes an out-of-tree loader a first-class citizen
rather than a special case (architecture plan §5.1.1).

``load()`` **always returns a tuple**, even for a single test
-------------------------------------------------------------
Maintainer decision, 2026-07-19, frozen with the Protocol in 2.0: every caller
writes one unpacking path, and a format that grows multi-test support later
does not silently become a breaking change for its consumers. A loader for a
single-test format returns a 1-tuple.

What a loader fills in, and what it must not
---------------------------------------------
A loader fills only what the *file* actually knows. Provenance — where the file
came from, when it was read, what identity it was given — is stamped by the
framework, because the loader is not in a position to know it. A draft
``TestMeta`` arriving with ``source_uri`` already set is a contract violation,
and the conformance kit rejects it (architecture plan §5.1.3).

See also
--------
``cellpy.readers.instruments.registry`` (discovery and routing) and
``cellpy.readers.instruments.testing`` (the conformance kit).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    import polars as pl
    from cellpycore.metadata.models import CellMeta, TestMeta
    from cellpycore.units import CellpyUnits


@dataclass(frozen=True, slots=True)
class LoaderResult:
    """One test's worth of parsed data, on its way into the framework.

    Attributes:
        raw: the harmonized-raw frame — native ``RawCols`` names,
            ``epoch_time_utc`` as int64 ns UTC, ``datapoint_num`` as a
            *column* (never an index).
        raw_units: a validated ``CellpyUnits``; every label pint-parsable.
            Never an ad-hoc dict and never float scale factors.
        test_meta: a **draft** ``TestMeta`` — only fields the source file
            knows. Provenance fields must be left empty for the framework.
        cell_meta: an optional partial ``CellMeta``, for the rare file that
            carries masses or areas.
        warnings: non-fatal notes the framework surfaces to the user. A
            *fatal* problem is a ``LoaderError``, never a partial result.
    """

    raw: "pl.DataFrame"
    raw_units: "CellpyUnits"
    test_meta: "TestMeta"
    cell_meta: "CellMeta | None" = None
    warnings: tuple[str, ...] = field(default=())


class LoaderCapabilities(Protocol):
    """The class-level metadata the registry routes on.

    Kept in its own Protocol for a language reason: a ``runtime_checkable``
    Protocol carrying **non-method** members cannot be used with
    ``issubclass()``, and the registry must check a loader *class* without
    instantiating it. So the runtime structural check lives on
    :class:`InstrumentLoader` (methods only) and these attributes are validated
    explicitly by the registry, which can also say precisely which one is
    missing. Use this Protocol for static typing.
    """

    #: Loader id, unique within the registry, e.g. ``"arbin_res"``.
    name: ClassVar[str]
    #: The instrument family, e.g. ``"arbin"``. Several loaders may share one.
    instrument: ClassVar[str]
    #: Suffixes this loader can route on, lowercase and dotted, e.g. ``(".res",)``.
    supported_suffixes: ClassVar[tuple[str, ...]]


@runtime_checkable
class InstrumentLoader(Protocol):
    """Structural contract for instrument loaders — the behaviour half.

    Implementations need not import or inherit anything from cellpy. Register
    via the ``cellpy.loaders`` entry-point group; see
    :mod:`cellpy.readers.instruments.registry`.

    A conforming loader also declares the :class:`LoaderCapabilities`
    attributes (``name``, ``instrument``, ``supported_suffixes``); they are not
    members of *this* Protocol only so that ``issubclass()`` keeps working —
    the registry validates them separately and rejects a loader that omits
    them.

    Loaders must be **stateless across calls**: two ``load()`` calls on the
    same source give equal results, and nothing from one call leaks into the
    next. The registry routes on the class-level capability attributes without
    instantiating, so those must not depend on instance state.
    """

    def can_load(self, source: Path) -> bool:
        """Cheap sniff — suffix or magic bytes. Must not fully parse the file.

        The registry calls this while choosing between candidates, so a slow
        implementation makes every load slow. The conformance kit puts a time
        budget on it.
        """
        ...

    def load(
        self,
        source: Path,
        *,
        instrument_config: object | None = None,
        **kwargs: object,
    ) -> tuple[LoaderResult, ...]:
        """Parse one source into one result per test it contains.

        Args:
            source: a **local** path. The framework has already resolved any
                remote/OtherPath source to a local copy — a loader never
                encodes ssh or scheme semantics (architecture plan §5.1.8).
            instrument_config: the typed per-instrument configuration model,
                when the framework has one for this loader.
            **kwargs: loader-specific knobs. Unknown ones must be ignorable,
                so that a caller passing a knob meant for another loader is
                not an error.

        Returns:
            One :class:`LoaderResult` per test in the source — always a tuple,
            length 1 for single-test formats.

        Raises:
            LoaderError: wrapping any vendor parse failure. Never return a
                partial or empty result to signal failure (conventions §1).
        """
        ...
