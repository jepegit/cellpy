"""SupportsIncrementalLoad is optional and structural (#779).

The full-read InstrumentLoader contract stays unchanged. These tests pin
the split: load_since is a second protocol, not a required method.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from cellpy.readers.instruments.contract import (
    IncrementalChunk,
    InstrumentLoader,
    LoadMarker,
    SupportsIncrementalLoad,
)
from cellpy.readers.instruments.testing import check_loader
from tests.test_loader_contract import GoodLoader


class SinceOnly:
    """Advertises the incremental protocol and nothing else."""

    def load_since(self, source: Path, marker: LoadMarker | None) -> IncrementalChunk:
        return IncrementalChunk(new_raw=pl.DataFrame(), marker=marker or LoadMarker())


class Both(GoodLoader):
    """Full-read loader that also implements load_since."""

    name = "both_loader"

    def load_since(self, source: Path, marker: LoadMarker | None) -> IncrementalChunk:
        raw = self.load(source)[0].raw
        return IncrementalChunk(new_raw=raw, marker=marker or LoadMarker())


@pytest.mark.essential
def test_load_since_alone_matches_only_the_incremental_protocol():
    assert issubclass(SinceOnly, SupportsIncrementalLoad)
    assert isinstance(SinceOnly(), SupportsIncrementalLoad)
    assert not issubclass(SinceOnly, InstrumentLoader)
    assert SupportsIncrementalLoad not in SinceOnly.__mro__


@pytest.mark.essential
def test_full_read_loader_is_not_incremental():
    assert issubclass(GoodLoader, InstrumentLoader)
    assert not issubclass(GoodLoader, SupportsIncrementalLoad)
    assert not isinstance(GoodLoader(), SupportsIncrementalLoad)


@pytest.mark.essential
def test_loader_can_match_both_protocols():
    assert issubclass(Both, InstrumentLoader)
    assert issubclass(Both, SupportsIncrementalLoad)
    assert isinstance(Both(), SupportsIncrementalLoad)


@pytest.mark.essential
def test_marker_and_chunk_are_frozen():
    marker = LoadMarker(last_source_datapoint_num=4, byte_offset=80, row_count=4)
    chunk = IncrementalChunk(new_raw=pl.DataFrame({"datapoint_num": [1]}), marker=marker)
    with pytest.raises(Exception):
        marker.byte_offset = 0
    with pytest.raises(Exception):
        chunk.complete = True
    assert chunk.complete is False


@pytest.mark.essential
def test_conformance_kit_ignores_a_missing_load_since(tmp_path):
    fixture = tmp_path / "sample.good"
    fixture.write_text("dummy", encoding="utf-8")
    check_loader(GoodLoader, fixture)
    assert not issubclass(GoodLoader, SupportsIncrementalLoad)
