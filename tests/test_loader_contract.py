"""Loader contract, registry and conformance-kit tests (#210).

The contract is frozen at 2.0, so these tests are as much a specification as a
regression net: they pin the tuple return, the structural (no-base-class)
conformance rule, and the framework-stamps-provenance division of labour.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl
import pytest
from cellpycore.config import default_schema
from cellpycore.metadata.models import TestMeta
from cellpycore.units import CellpyUnits

from cellpy import log
from cellpy.exceptions import LoaderError
from cellpy.readers.instruments import registry
from cellpy.readers.instruments.contract import InstrumentLoader, LoaderResult
from cellpy.readers.instruments.testing import check_loader

log.setup_logging(default_level=logging.DEBUG, testing=True)


# -- a conforming loader that imports no cellpy base class ---------------------


def _sample_frame(rows: int = 4) -> pl.DataFrame:
    schema = default_schema().raw
    return pl.DataFrame(
        {
            schema.datapoint_num: list(range(rows)),
            schema.test_time: [float(i) for i in range(rows)],
            schema.potential: [3.0 + 0.1 * i for i in range(rows)],
            schema.current: [0.001] * rows,
            schema.epoch_time_utc: [1_700_000_000_000_000_000 + i for i in range(rows)],
        }
    )


class GoodLoader:
    """A third-party loader: no cellpy base class, no cellpy imports needed."""

    name = "good_loader"
    instrument = "goodinstrument"
    supported_suffixes = (".good",)

    tests_per_file = 1

    def can_load(self, source: Path) -> bool:
        return Path(source).suffix.lower() in self.supported_suffixes

    def load(self, source, *, instrument_config=None, **kwargs):
        return tuple(
            LoaderResult(
                raw=_sample_frame(),
                raw_units=CellpyUnits(),
                test_meta=TestMeta(),
            )
            for _ in range(self.tests_per_file)
        )


class MultiTestLoader(GoodLoader):
    name = "multi_loader"
    instrument = "multiinstrument"
    supported_suffixes = (".multi",)
    tests_per_file = 3


@pytest.fixture
def fixture_file(tmp_path) -> Path:
    path = tmp_path / "sample.good"
    path.write_text("dummy", encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear_registry()
    yield
    registry.clear_registry()


# -- the contract --------------------------------------------------------------


@pytest.mark.essential
def test_conformance_is_structural_not_inheritance():
    # The whole point of a Protocol: GoodLoader inherits nothing from cellpy
    # and imports no cellpy base class, yet conforms.
    assert InstrumentLoader not in GoodLoader.__mro__
    assert issubclass(GoodLoader, InstrumentLoader)
    assert isinstance(GoodLoader(), InstrumentLoader)


@pytest.mark.essential
def test_issubclass_works_on_the_runtime_protocol():
    # Guards the split in contract.py: a runtime_checkable Protocol carrying
    # data members raises TypeError here, and the registry needs the class
    # check (it must not instantiate a loader just to identify it).
    assert issubclass(GoodLoader, InstrumentLoader) is True


@pytest.mark.essential
def test_load_returns_a_tuple_even_for_a_single_test(fixture_file):
    results = GoodLoader().load(fixture_file)
    assert isinstance(results, tuple)
    assert len(results) == 1


@pytest.mark.essential
def test_load_returns_one_result_per_test(fixture_file):
    results = MultiTestLoader().load(fixture_file)
    assert len(results) == 3


@pytest.mark.essential
def test_loader_result_is_frozen():
    result = LoaderResult(
        raw=_sample_frame(), raw_units=CellpyUnits(), test_meta=TestMeta()
    )
    with pytest.raises(Exception):
        result.raw = _sample_frame()


# -- the conformance kit -------------------------------------------------------


@pytest.mark.essential
def test_check_loader_passes_a_conforming_loader(fixture_file):
    check_loader(GoodLoader, fixture_file)


@pytest.mark.essential
def test_check_loader_rejects_a_non_tuple_return(fixture_file):
    class ReturnsBareResult(GoodLoader):
        name = "bare"

        def load(self, source, *, instrument_config=None, **kwargs):
            return LoaderResult(
                raw=_sample_frame(), raw_units=CellpyUnits(), test_meta=TestMeta()
            )

    with pytest.raises(AssertionError, match="must return a tuple"):
        check_loader(ReturnsBareResult, fixture_file)


@pytest.mark.essential
def test_check_loader_rejects_provenance_in_a_draft(fixture_file):
    class StampsProvenance(GoodLoader):
        name = "stamper"

        def load(self, source, *, instrument_config=None, **kwargs):
            meta = TestMeta()
            meta.source_uri = "/somewhere/on/disk"
            return (
                LoaderResult(
                    raw=_sample_frame(), raw_units=CellpyUnits(), test_meta=meta
                ),
            )

    with pytest.raises(AssertionError, match="provenance"):
        check_loader(StampsProvenance, fixture_file)


@pytest.mark.essential
def test_check_loader_rejects_unknown_raw_columns(fixture_file):
    class EmitsVendorNames(GoodLoader):
        name = "vendor_names"

        def load(self, source, *, instrument_config=None, **kwargs):
            frame = _sample_frame().rename({default_schema().raw.potential: "Volts"})
            return (
                LoaderResult(
                    raw=frame, raw_units=CellpyUnits(), test_meta=TestMeta()
                ),
            )

    with pytest.raises(AssertionError, match="outside the harmonized-raw schema"):
        check_loader(EmitsVendorNames, fixture_file)


@pytest.mark.essential
def test_check_loader_rejects_a_non_deterministic_loader(fixture_file):
    class Stateful(GoodLoader):
        name = "stateful"
        _calls = 0

        def load(self, source, *, instrument_config=None, **kwargs):
            type(self)._calls += 1
            return (
                LoaderResult(
                    raw=_sample_frame(rows=3 + type(self)._calls),
                    raw_units=CellpyUnits(),
                    test_meta=TestMeta(),
                ),
            )

    with pytest.raises(AssertionError, match="deterministic"):
        check_loader(Stateful, fixture_file)


# -- the registry --------------------------------------------------------------


@dataclass
class _FakeEntryPoint:
    name: str
    value: str
    target: object = None
    boom: Exception | None = None

    def load(self):
        if self.boom is not None:
            raise self.boom
        return self.target


def _patch_entry_points(monkeypatch, *eps):
    monkeypatch.setattr(registry, "_iter_entry_points", lambda: list(eps))
    registry.clear_registry()


@pytest.mark.essential
def test_entry_point_loader_is_discovered(monkeypatch):
    _patch_entry_points(
        monkeypatch, _FakeEntryPoint("good", "pkg:GoodLoader", GoodLoader)
    )
    assert "good_loader" in registry.get_registry()
    assert registry.available_loaders()["good_loader"]["instrument"] == "goodinstrument"


@pytest.mark.essential
def test_discovery_is_lazy(monkeypatch):
    calls = []

    def _spy():
        calls.append(1)
        return []

    monkeypatch.setattr(registry, "_iter_entry_points", _spy)
    registry.clear_registry()
    assert not calls, "importing/clearing must not scan entry points"
    registry.get_registry()
    assert len(calls) == 1
    registry.get_registry()
    assert len(calls) == 1, "discovery result should be cached"


@pytest.mark.essential
def test_a_broken_plugin_does_not_break_cellpy(monkeypatch, caplog):
    _patch_entry_points(
        monkeypatch,
        _FakeEntryPoint("broken", "pkg:Nope", boom=ImportError("no such module")),
        _FakeEntryPoint("good", "pkg:GoodLoader", GoodLoader),
    )
    with caplog.at_level(logging.WARNING):
        found = registry.get_registry()
    # the healthy one still registers, the broken one is reported
    assert "good_loader" in found
    assert "broken" in caplog.text


@pytest.mark.essential
def test_a_non_conforming_plugin_is_rejected_at_registration(monkeypatch, caplog):
    class NotALoader:
        name = "impostor"
        instrument = "nothing"
        supported_suffixes = (".x",)
        # no load(), no can_load()

    _patch_entry_points(
        monkeypatch, _FakeEntryPoint("impostor", "pkg:NotALoader", NotALoader)
    )
    with caplog.at_level(logging.WARNING):
        found = registry.get_registry()
    assert "impostor" not in found
    assert "does not satisfy the InstrumentLoader contract" in caplog.text


@pytest.mark.essential
def test_bad_capability_metadata_is_rejected():
    class BadSuffixes(GoodLoader):
        name = "bad_suffixes"
        supported_suffixes = "res"  # a bare string, not a tuple

    with pytest.raises(LoaderError, match="tuple of suffixes"):
        registry.register(BadSuffixes)


@pytest.mark.essential
def test_undotted_suffixes_are_rejected():
    class Undotted(GoodLoader):
        name = "undotted"
        supported_suffixes = ("res",)

    with pytest.raises(LoaderError, match="dotted strings"):
        registry.register(Undotted)


# -- routing -------------------------------------------------------------------


@pytest.mark.essential
def test_routing_by_explicit_instrument_name():
    registry.register(GoodLoader)
    registry.register(MultiTestLoader)
    assert registry.find_loader(instrument="good_loader") is GoodLoader
    # ... and by instrument family, not just loader id
    assert registry.find_loader(instrument="multiinstrument") is MultiTestLoader


@pytest.mark.essential
def test_routing_by_suffix(tmp_path):
    registry.register(GoodLoader)
    registry.register(MultiTestLoader)
    assert registry.find_loader(tmp_path / "x.good") is GoodLoader
    assert registry.find_loader(tmp_path / "x.multi") is MultiTestLoader


@pytest.mark.essential
def test_routing_falls_back_to_can_load_when_suffixes_collide(tmp_path):
    class Sniffer(GoodLoader):
        name = "sniffer"
        supported_suffixes = (".shared",)

        def can_load(self, source: Path) -> bool:
            return Path(source).name.startswith("mine")

    class OtherSniffer(GoodLoader):
        name = "other_sniffer"
        supported_suffixes = (".shared",)

        def can_load(self, source: Path) -> bool:
            return Path(source).name.startswith("theirs")

    registry.register(Sniffer)
    registry.register(OtherSniffer)
    assert registry.find_loader(tmp_path / "mine.shared") is Sniffer
    assert registry.find_loader(tmp_path / "theirs.shared") is OtherSniffer


@pytest.mark.essential
def test_unknown_source_routes_to_nothing(tmp_path):
    registry.register(GoodLoader)
    assert registry.find_loader(tmp_path / "x.unknown") is None
    assert registry.find_loader(instrument="not_installed") is None


@pytest.mark.essential
def test_we_query_the_documented_entry_point_group(monkeypatch):
    """The monkeypatched tests above stub _iter_entry_points, so nothing else
    checks that we ask importlib for the group third-party packages declare."""
    seen = {}

    def _fake_entry_points(*, group):
        seen["group"] = group
        return []

    import cellpy.readers.instruments.registry as reg

    monkeypatch.setattr(reg, "entry_points", _fake_entry_points)
    list(reg._iter_entry_points())
    assert seen["group"] == "cellpy.loaders"
    assert reg.ENTRY_POINT_GROUP == "cellpy.loaders"
