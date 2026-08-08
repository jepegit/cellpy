"""In-memory Plotly image export (#818)."""

from types import SimpleNamespace

import pytest

from cellpy.exceptions import OptionalDependencyError
from cellpy.plotting import image_media_type, write_image
from cellpy.plotting import figures as figures_mod


class _FakeFig:
    def __init__(self, payload=b"PNGDATA"):
        self.payload = payload
        self.calls = []

    def to_image(self, format="png", scale=1.0, **kwargs):
        self.calls.append({"format": format, "scale": scale, **kwargs})
        return self.payload


@pytest.mark.essential
def test_write_image_returns_bytes():
    fig = _FakeFig(b"abc")
    out = write_image(fig, "svg", scale=2.0, width=400)
    assert out == b"abc"
    assert fig.calls == [{"format": "svg", "scale": 2.0, "width": 400}]


@pytest.mark.essential
def test_write_image_rejects_bad_format():
    with pytest.raises(ValueError, match="unsupported image format"):
        write_image(_FakeFig(), "tiff")


@pytest.mark.essential
def test_write_image_missing_kaleido(monkeypatch):
    real_find = figures_mod.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == "kaleido":
            return None
        return real_find(name, *args, **kwargs)

    monkeypatch.setattr(figures_mod.importlib.util, "find_spec", fake_find)
    with pytest.raises(OptionalDependencyError, match="kaleido"):
        write_image(_FakeFig(), "png")


@pytest.mark.essential
def test_image_media_type():
    assert image_media_type("png") == "image/png"
    assert image_media_type(".svg") == "image/svg+xml"
    assert image_media_type("pdf") == "application/pdf"


@pytest.mark.essential
def test_collection_to_image_uses_plot(monkeypatch):
    import polars as pl

    from cellpy.collect.collection import Collection, CollectionMeta

    col = Collection(
        data=pl.DataFrame({"cycle_num": [1], "charge_capacity": [1.0], "cell": ["a"]}),
        kind="summary",
        name="demo",
        meta=CollectionMeta(kind="summary"),
    )
    fig = _FakeFig(b"from-collection")
    monkeypatch.setattr(col, "plot", lambda **kwargs: fig)
    assert col.to_image("pdf") == b"from-collection"
    assert fig.calls[0]["format"] == "pdf"
