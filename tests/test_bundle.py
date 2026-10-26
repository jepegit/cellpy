"""Round-trip tests for ``save_bundle`` (jepegit/cellpy#1132)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from cellpy.plotting.bundle import save_bundle


@pytest.mark.essential
def test_importing_cellpy_does_not_import_cellpy_figure():
    code = "import cellpy, sys; raise SystemExit(0 if 'cellpy_figure' not in sys.modules else 1)"
    result = subprocess.run([sys.executable, "-c", code], check=False)
    assert result.returncode == 0


@pytest.mark.essential
def test_save_bundle_cycles_round_trip(cell, tmp_path):
    path = tmp_path / "cycles.cfz"
    save_bundle(cell, kind="cycles", path=path, cycles=[1], interpolated=True)

    from cellpy_figure import open_figure

    figure = open_figure(path)
    panel = figure.panels[0]
    assert "capacity" in figure.data.columns
    assert panel.x.label == "Capacity"
    assert panel.x.unit
    assert panel.y.label == "Voltage"
    assert panel.stroke.scale["charge"] == "solid"
    assert panel.stroke.scale["discharge"] == "dashed"
    assert panel.color.type == "nominal"
    assert figure.provenance.producer == "cellpy"
    assert figure.provenance.producer_version
    assert "interpolated" in figure.provenance.note
    assert figure.extensions["cellpy"]["family"] == "cycles"


@pytest.mark.essential
def test_save_bundle_cycles_colorbar_is_quantitative(cell, tmp_path):
    path = tmp_path / "cycles.cfz"
    save_bundle(cell, kind="cycles", path=path, cycles=[1], force_colorbar=True)

    from cellpy_figure import open_figure

    figure = open_figure(path)
    assert figure.panels[0].color.type == "quantitative"


@pytest.mark.essential
def test_save_bundle_summary_round_trip(cell, tmp_path):
    path = tmp_path / "summary.cfz"
    save_bundle(cell, kind="summary", path=path)

    from cellpy_figure import open_figure

    figure = open_figure(path)
    panel = figure.panels[0]
    assert "value" in figure.data.columns
    assert panel.x.field in figure.data.columns
    assert panel.y.field == "value"
    assert panel.facet is not None
    assert panel.facet.field == "variable"
    assert figure.provenance.producer == "cellpy"
    assert figure.extensions["cellpy"]["family"]


@pytest.mark.essential
def test_save_bundle_ica_round_trip(cell, tmp_path):
    path = tmp_path / "ica.cfz"
    save_bundle(cell, kind="ica", path=path, cycles=[1])

    from cellpy_figure import open_figure

    figure = open_figure(path)
    panel = figure.panels[0]
    assert panel.x.field == "voltage"
    assert panel.y.field == "dqdv"
    assert panel.stroke.scale["charge"] == "solid"
    assert panel.stroke.scale["discharge"] == "dashed"
    assert figure.extensions["cellpy"]["family"] == "ica"


@pytest.mark.essential
def test_save_bundle_dva_round_trip(cell, tmp_path):
    path = tmp_path / "dva.cfz"
    save_bundle(cell, kind="dva", path=path, cycles=[1])

    from cellpy_figure import open_figure

    figure = open_figure(path)
    panel = figure.panels[0]
    assert panel.x.field == "capacity"
    assert panel.y.field == "dvdq"
    assert panel.stroke.scale["discharge"] == "dashed"
    assert figure.extensions["cellpy"]["family"] == "dva"


def test_unknown_kind_is_refused(cell, tmp_path):
    with pytest.raises(ValueError, match="kind"):
        save_bundle(cell, kind="film", path=tmp_path / "nope.cfz")
