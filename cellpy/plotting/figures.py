"""Loading and saving figures — one implementation (#567).

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
