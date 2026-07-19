"""Conformance kit for instrument loaders (cellpy 2, issue #210).

Ships with cellpy so a third-party loader can prove it satisfies the contract
without reverse-engineering it from cellpy's internals::

    from cellpy.readers.instruments.testing import check_loader

    def test_my_loader_conforms():
        check_loader(MyCyclerLoader, fixture=Path("tests/data/sample.mcx"))

Every check corresponds to a promise in
:mod:`cellpy.readers.instruments.contract`; failures raise
:class:`AssertionError` naming the promise that was broken.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from cellpy.readers.instruments.contract import InstrumentLoader, LoaderResult
from cellpy.readers.instruments.registry import _validate_capabilities

#: ``can_load()`` is called while routing, so it must stay cheap.
CAN_LOAD_BUDGET_SECONDS = 1.0

#: Provenance is the framework's to stamp; a draft carrying it is a violation.
_PROVENANCE_FIELDS = (
    "source_kind",
    "source_type",
    "source_uri",
    "source_uuid",
    "raw_file_names",
    "loaded_datetime",
)


def check_capabilities(loader_cls: type) -> None:
    """The class declares what the registry needs to route it."""
    _validate_capabilities(loader_cls, "check_loader")
    assert isinstance(loader_cls, type), "check_loader takes the class, not an instance"
    assert issubclass(loader_cls, InstrumentLoader), (
        f"{loader_cls!r} does not satisfy the InstrumentLoader contract "
        f"(needs load() and can_load())"
    )


def check_result_types(results: Any) -> tuple[LoaderResult, ...]:
    """``load()`` returns a tuple of ``LoaderResult`` — always a tuple."""
    assert isinstance(results, tuple), (
        f"load() must return a tuple of LoaderResult (a 1-tuple for "
        f"single-test formats), got {type(results).__name__}"
    )
    assert results, "load() returned an empty tuple; raise LoaderError instead"
    for result in results:
        assert isinstance(result, LoaderResult), (
            f"load() must yield LoaderResult objects, got {type(result).__name__}"
        )
    return results


def check_raw_frame(result: LoaderResult) -> None:
    """The frame is polars, in the harmonized-raw shape."""
    import polars as pl

    raw = result.raw
    assert isinstance(raw, pl.DataFrame), (
        f"LoaderResult.raw must be a polars DataFrame, got {type(raw).__name__}"
    )
    assert raw.height, "LoaderResult.raw is empty; raise LoaderError instead"

    from cellpycore.config import default_schema

    known = set(default_schema().raw.ordered_names())
    unknown = [column for column in raw.columns if column not in known]
    assert not unknown, (
        f"raw carries columns outside the harmonized-raw schema: {unknown}. "
        f"Declare vendor->native names in the loader's column_map."
    )

    schema = default_schema().raw
    if schema.datapoint_num in raw.columns:
        series = raw[schema.datapoint_num]
        assert series.is_sorted(), (
            "datapoint_num must be monotone; it is the frame's ordering key"
        )
    if schema.epoch_time_utc in raw.columns:
        dtype = raw[schema.epoch_time_utc].dtype
        assert dtype == pl.Int64, (
            f"epoch_time_utc must be int64 nanoseconds UTC, got {dtype}"
        )


def check_units(result: LoaderResult) -> None:
    """``raw_units`` is a validated ``CellpyUnits``, not an ad-hoc dict."""
    from cellpycore.units import CellpyUnits, validate_units

    assert isinstance(result.raw_units, CellpyUnits), (
        f"LoaderResult.raw_units must be a CellpyUnits, got "
        f"{type(result.raw_units).__name__}"
    )
    validate_units(result.raw_units)


def check_meta_is_a_draft(result: LoaderResult) -> None:
    """The loader fills what the file knows — never provenance."""
    filled = [
        name
        for name in _PROVENANCE_FIELDS
        if getattr(result.test_meta, name, None) not in (None, "", [], ())
    ]
    assert not filled, (
        f"draft TestMeta carries provenance {filled}; those fields are stamped "
        f"by the framework, which alone knows where the file came from"
    )


def check_can_load_is_cheap(loader_cls: type, fixture: Path) -> None:
    """Routing calls ``can_load()``; a slow sniff makes every load slow."""
    loader = loader_cls()
    started = time.perf_counter()
    verdict = loader.can_load(fixture)
    elapsed = time.perf_counter() - started
    assert isinstance(verdict, bool), "can_load() must return a bool"
    assert elapsed < CAN_LOAD_BUDGET_SECONDS, (
        f"can_load() took {elapsed:.2f}s (budget {CAN_LOAD_BUDGET_SECONDS}s); "
        f"it must sniff, not parse"
    )


def check_determinism(loader_cls: type, fixture: Path, **kwargs: Any) -> None:
    """Loaders are stateless across calls."""
    first = loader_cls().load(fixture, **kwargs)
    second = loader_cls().load(fixture, **kwargs)
    assert len(first) == len(second), "load() is not deterministic (different lengths)"
    for a, b in zip(first, second):
        assert a.raw.equals(b.raw), "load() is not deterministic (raw frames differ)"


def check_loader(loader_cls: type, fixture: Path, **kwargs: Any) -> None:
    """Run the whole conformance suite for one loader against one fixture.

    Args:
        loader_cls: the loader **class** (the registry routes on class-level
            capability metadata, so that is what is checked).
        fixture: a small committed sample file the loader can parse.
        **kwargs: forwarded to ``load()``.

    Raises:
        AssertionError: naming the contract promise that was broken.
    """
    fixture = Path(fixture)
    assert fixture.is_file(), f"fixture {fixture} does not exist"

    check_capabilities(loader_cls)
    check_can_load_is_cheap(loader_cls, fixture)

    results = check_result_types(loader_cls().load(fixture, **kwargs))
    for result in results:
        check_raw_frame(result)
        check_units(result)
        check_meta_is_a_draft(result)

    check_determinism(loader_cls, fixture, **kwargs)


# The reset-granularity property check (architecture plan §5.5 check 7 — the
# one that catches silent capacity corruption) needs the harmonize() framework
# to normalize against, so it lands with #559 and is added here then.
