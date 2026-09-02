"""collect_ica / collect_dva accept cellpy.ica.IcaOptions as the recipe."""

from __future__ import annotations

import warnings

import pytest

from tests.test_batch import (  # noqa: F401
    batch_instance,
    clean_dir,
    populated_batch,
)

from cellpy import ica
from cellpy._deprecation import _WARNED_SITES
from cellpy.collect import IcaOptions as CollectIcaOptions
from cellpy.collect import collect_dva, collect_ica


@pytest.mark.essential
def test_collect_ica_forwards_the_full_recipe(populated_batch, monkeypatch):
    from cellpy.utils import ica as ica_mod

    captured: dict = {}
    original = ica_mod.dqdv

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(ica_mod, "dqdv", spy)
    opts = ica.IcaOptions(
        voltage_resolution=0.005, voltage_fwhm=0.015, pre_smoothing=True
    )
    collect_ica(populated_batch, options=opts, cycles=(1,))

    assert captured["options"] == opts
    assert captured["cycles"] == [1]


@pytest.mark.essential
def test_collect_dva_forwards_the_full_recipe(populated_batch, monkeypatch):
    from cellpy.utils import ica as ica_mod

    captured: dict = {}
    original = ica_mod.dvdq

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(ica_mod, "dvdq", spy)
    opts = ica.DVA_DEFAULTS.replace(capacity_resolution=0.01, post_smoothing=False)
    collect_dva(populated_batch, options=opts, cycles=(1,))

    assert captured["options"] == opts
    assert captured["options"].normalize is False
    assert captured["cycles"] == [1]


@pytest.mark.essential
def test_collect_dva_keeps_dva_defaults_when_no_recipe(populated_batch, monkeypatch):
    from cellpy.utils import ica as ica_mod

    captured: dict = {}
    original = ica_mod.dvdq

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(ica_mod, "dvdq", spy)
    collect_dva(populated_batch, cycles=(1,), capacity_resolution=0.01)

    recipe = captured["options"]
    assert recipe.capacity_resolution == 0.01
    assert recipe.normalize is False
    assert "voltage_resolution" not in captured


@pytest.mark.essential
def test_legacy_collect_ica_options_still_works(populated_batch):
    _WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        col = collect_ica(
            populated_batch,
            options=CollectIcaOptions(cycles=(1,), voltage_resolution=0.01),
        )
    assert col.kind == "ica"
    assert col.data.height > 0
    assert col.meta.options["voltage_resolution"] == 0.01
    messages = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
    assert any("cellpy.collect.IcaOptions" in m for m in messages)


@pytest.mark.essential
def test_legacy_collect_dva_options_still_works(populated_batch):
    _WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        col = collect_dva(
            populated_batch,
            options=CollectIcaOptions(cycles=(1,), capacity_resolution=0.01),
        )
    assert col.kind == "dva"
    assert col.meta.options["capacity_resolution"] == 0.01
    messages = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
    assert any("cellpy.collect.IcaOptions" in m for m in messages)


@pytest.mark.essential
def test_unknown_options_type_raises(populated_batch):
    with pytest.raises(TypeError, match="cellpy.ica.IcaOptions"):
        collect_ica(populated_batch, options=object())
