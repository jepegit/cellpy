"""The opt-in harmonized-raw flip (Phase B / #560).

``prms.Reader.use_harmonized_raw`` routes single-file raw loading through the
two-stage ``harmonize(parse())`` pipeline instead of the legacy
``loader()+to_native`` rename. It ships **off** — the flip still drops aux
columns and renumbers ``data_point`` on some loaders, so it is not yet a safe
default (see the loader plan) — but the mechanism is wired and reversible, and
this module keeps it covered so it does not rot before it is hardened.

biologics_mpr is used because its flip is clean end-to-end (no aux columns, no
data_point renumbering divergence); the fixture is in-repo.
"""

from __future__ import annotations

import warnings

import pytest

import cellpy
import cellpy.config as config

SOURCE = "testdata/data/biol.mpr"


def _get():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return cellpy.get(SOURCE, instrument="biologics_mpr", mass=1.0, testing=True)


@pytest.fixture
def harmonized_raw_on():
    previous = getattr(config.reader, "use_harmonized_raw", False)
    config.reader.use_harmonized_raw = True
    try:
        yield
    finally:
        config.reader.use_harmonized_raw = previous


@pytest.mark.essential
def test_default_is_off_so_raw_has_no_epoch_time_utc():
    """The legacy loader()+to_native path carries date_time, not epoch_time_utc."""
    assert getattr(config.reader, "use_harmonized_raw", False) is False
    c = _get()
    assert "epoch_time_utc" not in c.data.raw.columns


@pytest.mark.essential
def test_flip_on_produces_the_harmonized_native_raw(harmonized_raw_on):
    """With the flip on, raw comes from harmonize(parse()) and carries the
    native epoch_time_utc/mask columns the rename path omits."""
    c = _get()
    assert "epoch_time_utc" in c.data.raw.columns
    assert "mask" in c.data.raw.columns
    # and it is still a usable cell: the summary builds.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c.make_summary()
    assert len(c.data.summary) >= 1
