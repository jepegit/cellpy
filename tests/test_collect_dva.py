"""collect_dva: DVA collection mirrors collect_ica (#863).

Same shape as the ``test_collectors.py`` ICA tests -- the ``populated_batch``
fixture, the specced-frame assertion, and the collector convenience wrapper --
plus regression guards for the two things that are easy to get wrong when
mirroring ``collect_ica``: the resolution knob (``capacity_resolution``, not
``voltage_resolution``) and the ``Collection`` -> ``collected_plot`` family
wiring (``kind="dva"`` must not fall back to the ``cycles`` family).
"""

from __future__ import annotations

import pytest

# Reuse the batch fixtures (clean_dir -> batch_instance -> populated_batch).
from tests.test_batch import (  # noqa: F401  (imported for fixture resolution)
    batch_instance,
    clean_dir,
    populated_batch,
)

plotly = pytest.importorskip("plotly", reason="plotting extras (batch) not installed")

from cellpy.collect import IcaOptions, collect_dva, dva_collector  # noqa: E402


def _assert_rendered(collector):
    assert collector.data is not None, "collector produced no data"
    assert collector.data.height > 0, "collector data is empty"
    figure = collector.plot()
    assert figure is not None, "collector did not build a figure"
    assert len(figure.data) > 0, "figure has no traces"


@pytest.mark.essential
def test_dva_collector_uses_the_specced_frame(populated_batch):
    """The DVA frame is the specced frame: cycle/direction/capacity/voltage/dvdq."""
    collector = dva_collector(populated_batch, cycles=(1, 2))
    _assert_rendered(collector)
    cols = set(collector.data.columns)
    assert {"cycle", "direction", "capacity", "voltage", "dvdq"} <= cols, cols
    directions = set(collector.data["direction"].unique().to_list())
    assert directions <= {"charge", "discharge"}, directions


@pytest.mark.essential
def test_collect_dva_returns_a_dva_collection(populated_batch):
    col = collect_dva(populated_batch, cycles=(1, 2))
    assert col.kind == "dva"
    assert col.data.height > 0
    assert "dvdq" in col.data.columns


@pytest.mark.essential
def test_collect_dva_forwards_capacity_resolution_not_voltage_resolution(
    populated_batch, monkeypatch
):
    """dvdq differentiates along capacity: capacity_resolution must reach it,
    not voltage_resolution (the dqdv knob) -- guards the resolution-knob
    mixup between collect_ica and collect_dva."""
    from cellpy.utils import ica as ica_mod

    captured: dict = {}
    original = ica_mod.dvdq

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(ica_mod, "dvdq", spy)
    col = collect_dva(
        populated_batch, options=IcaOptions(cycles=(1,), capacity_resolution=0.01)
    )

    assert captured.get("capacity_resolution") == 0.01
    assert "voltage_resolution" not in captured
    assert col.meta.options["capacity_resolution"] == 0.01


@pytest.mark.essential
def test_dva_collection_plot_uses_the_dva_family_not_cycles(populated_batch):
    """Collection._FAMILY / render_collected wiring: a 'dva' kind must not
    silently fall back to the 'cycles' family (wrong x/y columns)."""
    col = collect_dva(populated_batch, cycles=(1, 2))
    figure = col.plot()
    assert figure is not None
    assert len(figure.data) > 0


@pytest.mark.essential
def test_dva_collector_fig_pr_cycle(populated_batch):
    collector = dva_collector(populated_batch, cycles=(1, 2))
    figure = collector.plot(method="fig_pr_cycle")
    assert figure is not None
