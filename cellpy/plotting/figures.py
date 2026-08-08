"""Loading and saving figures — one implementation.

``load_figure``, ``load_plotly_figure``, ``load_matplotlib_figure``,
``save_matplotlib_figure`` and ``make_matplotlib_manager`` existed as full
copies in both ``utils/plotutils.py`` and ``utils/collectors.py``.

Four of the five pairs were character-identical. The fifth was not, and the
difference mattered: plotutils' ``load_plotly_figure`` checks whether plotly is
installed and returns ``None`` if it is not, while collectors' copy went
straight to ``pio.read_json`` and raised ``NameError``/``ImportError`` on an
install without the ``batch`` extra. The guarded behaviour is the one kept
here, so the degradation is the same wherever you call it from.
"""

from __future__ import annotations

import importlib.util
import logging
import pickle as pkl
from pathlib import Path

import matplotlib.pyplot as plt

plotly_available = importlib.util.find_spec("plotly") is not None

#: Suffix -> backend, for ``load_figure`` when it is not told which to use.
_SUFFIX_BACKEND = {
    ".pkl": "matplotlib",
    ".pickle": "matplotlib",
    ".json": "plotly",
    ".plotly": "plotly",
    ".jsn": "plotly",
}
_DEFAULT_BACKEND = "plotly"


def load_figure(filename, backend=None):
    """Load a figure saved by cellpy.

    Args:
        filename: the file to read.
        backend: ``"plotly"``, ``"matplotlib"`` or ``"seaborn"`` (an alias for
            matplotlib). Inferred from the suffix when not given.

    Returns:
        The figure, or ``None`` if it could not be loaded.
    """
    filename = Path(filename)

    if backend is None:
        backend = _SUFFIX_BACKEND.get(filename.suffix, _DEFAULT_BACKEND)

    if backend == "plotly":
        return load_plotly_figure(filename)
    if backend in ("matplotlib", "seaborn"):
        return load_matplotlib_figure(filename)

    logging.warning(f"backend={backend!r} is not supported at the moment")
    return None


def save_matplotlib_figure(fig, filename):
    """Pickle a matplotlib figure to *filename*."""
    with open(filename, "wb") as handle:
        pkl.dump(fig, handle)


def make_matplotlib_manager(fig):
    """Attach a fresh canvas manager to an unpickled figure.

    An unpickled figure has no manager, so it cannot be shown. Borrowing one
    from a throwaway figure is the standard workaround
    (https://stackoverflow.com/a/54579616/8508004).
    """
    dummy = plt.figure()
    new_manager = dummy.canvas.manager
    new_manager.canvas.figure = fig
    fig.set_canvas(new_manager.canvas)
    return fig


def load_matplotlib_figure(filename, create_new_manager=False):
    """Unpickle a matplotlib figure.

    Args:
        filename: the pickle written by [`save_matplotlib_figure`][cellpy.plotting.figures.save_matplotlib_figure].
        create_new_manager: attach a canvas manager so the figure can be shown.
    """
    with open(filename, "rb") as handle:
        fig = pkl.load(handle)
    if create_new_manager:
        fig = make_matplotlib_manager(fig)
    return fig


def load_plotly_figure(filename):
    """Read a plotly figure from JSON.

    Returns ``None`` — rather than raising — when plotly is not installed or
    the file cannot be read, which is what the plotutils copy always did.
    """
    if not plotly_available:
        logging.warning("plotly is not available; cannot load %s", filename)
        return None

    import plotly.io as pio

    try:
        return pio.read_json(filename)
    except Exception as exc:  # noqa: BLE001 - any read failure is reported the same
        logging.warning("could not load a figure from %s: %s", filename, exc)
        return None


#: Formats accepted by :func:`write_image` / ``Collection.to_image``.
IMAGE_FORMATS = frozenset({"png", "svg", "pdf", "jpg", "jpeg", "webp"})

_IMAGE_MEDIA_TYPES = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def image_media_type(fmt: str) -> str:
    """Return a MIME type for an image format string (e.g. ``\"png\"``)."""
    key = fmt.lstrip(".").lower()
    try:
        return _IMAGE_MEDIA_TYPES[key]
    except KeyError as exc:
        raise ValueError(
            f"unsupported image format {fmt!r}; "
            f"supported: {', '.join(sorted(IMAGE_FORMATS))}"
        ) from exc


def write_image(figure, fmt: str = "png", *, scale: float = 1.0, **kwargs) -> bytes:
    """Export a Plotly figure to static image **bytes** (needs kaleido).

    In-process via ``figure.to_image`` — no temp files, no subprocess wrapper,
    no stdout status. For notebook/disk export see
    :func:`cellpy.utils.plotutils.save_image_files`.

    Args:
        figure: A Plotly figure (must implement ``to_image``).
        fmt: ``png``, ``svg``, ``pdf``, ``jpg``/``jpeg``, or ``webp``.
        scale: Pixel scale factor passed to kaleido (Plotly default 1.0).
        **kwargs: Forwarded to ``figure.to_image`` (e.g. ``width``, ``height``).

    Returns:
        Encoded image bytes.

    Raises:
        OptionalDependencyError: If kaleido is not installed.
        ValueError: If ``fmt`` is not supported.
        TypeError: If ``figure`` has no ``to_image`` method.
    """
    from cellpy.exceptions import OptionalDependencyError

    key = fmt.lstrip(".").lower()
    if key not in IMAGE_FORMATS:
        raise ValueError(
            f"unsupported image format {fmt!r}; "
            f"supported: {', '.join(sorted(IMAGE_FORMATS))}"
        )

    to_image = getattr(figure, "to_image", None)
    if not callable(to_image):
        raise TypeError(
            "write_image expects a Plotly figure with a to_image() method; "
            f"got {type(figure)!r}"
        )

    # Require kaleido only for real Plotly figures. Test stubs (and other
    # callables with to_image) must keep working on essential CI, which does
    # not install the batch extra / kaleido.
    fig_module = getattr(type(figure), "__module__", "") or ""
    if fig_module.startswith("plotly") and importlib.util.find_spec("kaleido") is None:
        raise OptionalDependencyError(
            "write_image needs kaleido for static PNG/SVG/PDF export. "
            "Install the plotting extra with:  pip install cellpy[batch]"
        )

    return to_image(format=key, scale=scale, **kwargs)
