"""Incremental capacity analysis (dQ/dV) and differential voltage analysis (dV/dQ).

Two public verbs over one pure core:

```python
from cellpy import ica

frame = ica.dqdv(c)                       # cycle, direction, voltage, capacity, dqdv
frame = ica.dvdq(c, direction="charge")   # cycle, direction, capacity, voltage, dvdq
```

The recipe is unchanged from cellpy 1.x — interpolate V(q), optionally smooth,
invert to q(V), differentiate, optionally smooth again, optionally normalize —
but it now lives in stateless functions ([`transform_half_cycle`][]) configured
by a single frozen [`IcaOptions`][] object rather than ~20 keyword arguments
tunnelled through four entry points.

**What changed in 2.0** (see `DEPRECATIONS.md` and the migration guide):

- The output frame is *specced*: always long format, always the same columns,
  with `direction` spelled `"charge"`/`"discharge"` instead of the old ±1 code
  whose meaning depended on `cycle_mode`.
- The incremental-capacity column is named `dqdv`. The old name `dq` is kept as
  a duplicate column for one release.
- `dvdq()` is new. cellpy could not compute differential voltage analysis at
  all before, even though the pipeline already built the smoothed V(q)
  representation it needs.
- Half-cycles that fail are reported, not silently replaced by empty arrays.
- `Converter`, `dqdv_cycle`, `dqdv_cycles`, `dqdv_np`, `dqdv(split=True)` and
  `dqdv(tidy=False)` are deprecated shims over the new core. They reproduce the
  1.x numbers bit-for-bit (`tests/data/goldens/ica_dqdv_*`) and go away in 2.1.

scipy stays on this side of the cellpy/cellpycore boundary: cellpycore is
scipy-free, and the ICA math is interpolation and filtering, not frame algebra.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Literal

import numpy as np
import pandas as pd
from scipy.integrate import simpson
from scipy.interpolate import interp1d

# scipy.ndimage.filters is a deprecated alias that already warns on scipy 1.18.
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

from cellpycore.config import CurveCols

from cellpy._deprecation import warn_once
from cellpy.exceptions import NullData

__all__ = [
    "BOTH",
    "CHARGE",
    "Converter",
    "DISCHARGE",
    "DVA_DEFAULTS",
    "GaussianOptions",
    "HalfCycleResult",
    "ICA_COLS",
    "IcaCols",
    "IcaOptions",
    "dqdv",
    "dqdv_cycle",
    "dqdv_cycles",
    "dqdv_np",
    "dvdq",
    "index_bounds",
    "to_wide",
    "transform_half_cycle",
    "value_bounds",
]

#: Curve frames from ``get_cap`` use native cellpycore names (#540).
_CCOLS = CurveCols()

#: ``get_cap(categorical_column=True)`` labels the *first* half-cycle -1 and the
#: *last* +1. Which physical direction that is depends on ``cycle_mode``: an
#: anode cell is discharged first, everything else is charged first. The old
#: output frame exposed the raw code and left the reader to work this out.
_DIRECTION_BY_CYCLE_MODE = {
    "anode": {-1: "discharge", 1: "charge"},
    "cathode": {-1: "charge", 1: "discharge"},
    "full-cell": {-1: "charge", 1: "discharge"},
}
_DEFAULT_CYCLE_MODE = "anode"

CHARGE = "charge"
DISCHARGE = "discharge"
BOTH = "both"


# ---------------------------------------------------------------------------
# options
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GaussianOptions:
    """Parameters passed straight through to ``scipy.ndimage.gaussian_filter1d``."""

    order: int = 0
    mode: str = "reflect"
    cval: float = 0.0
    truncate: float = 4.0


@dataclass(frozen=True)
class IcaOptions:
    """The complete recipe for one dQ/dV or dV/dQ transform.

    One definition, one docstring. In 1.x these ~20 parameters could arrive as
    ``Converter`` constructor arguments, as ``**kwargs`` tunnelled through any
    of four entry points, or as ``dqdv_np``'s 17 explicit parameters — with the
    same option spelled `smoothing` in one place and `diff_smoothing` in
    another. Now there is one object.

    Attributes:
        voltage_resolution: Voltage step for the q(V) interpolation, e.g.
            ``0.005``. ``None`` keeps the point count of the input.
        capacity_resolution: Capacity step for the V(q) interpolation. Ignored
            when ``max_points`` is set.
        max_points: Cap on the V(q) interpolation grid. Takes precedence over
            ``capacity_resolution``.
        interpolation_method: Any ``kind`` accepted by ``scipy.interpolate.interp1d``.
        pre_smoothing: Savitzky-Golay smoothing of V(q) before inversion.
        diff_smoothing: Savitzky-Golay smoothing of q(V) before differentiating.
            (1.x called this ``smoothing`` on ``Converter`` and
            ``diff_smoothing`` on ``dqdv_np``.)
        post_smoothing: Gaussian smoothing of the finished derivative.
        savgol_window_divisor: Window length divisor for both Savitzky-Golay
            passes; the window is clamped to at least 3 points and forced odd.
        savgol_order: Polynomial order for both Savitzky-Golay passes.
        voltage_fwhm: Full width at half maximum, in volts, of the gaussian
            post-smoothing — used when differentiating **along voltage**
            (dQ/dV).
        capacity_fwhm: The dV/dQ analogue, in capacity units. ``None`` derives
            it as 1% of the capacity span of the half-cycle, which is the same
            fraction the default ``voltage_fwhm`` of 0.01 V represents on a
            typical ~1 V window.
        gaussian: Remaining ``gaussian_filter1d`` parameters.
        normalize: ``"area"`` scales the curve so its integral equals the
            normalizing factor; ``False`` leaves it in physical units. 1.x
            spelled ``"area"`` as ``True``, which is still accepted.
        normalizing_factor: Target for ``normalize="area"``. ``None`` uses the
            half-cycle's own end capacity.
        normalizing_roof: Rescales the normalizing factor by
            ``end_capacity / normalizing_roof`` — the hook for normalizing a
            whole series to one nominal capacity.
        increment_method: Only ``"diff"``. The half-finished ``"hist"`` binning
            method from 1.x is reachable through the deprecated
            [`Converter`][cellpy.ica.Converter] only; see cellpy#566.
    """

    # interpolation
    voltage_resolution: float | None = None
    capacity_resolution: float | None = None
    max_points: int | None = None
    interpolation_method: str = "linear"
    # smoothing
    pre_smoothing: bool = False
    diff_smoothing: bool = False
    post_smoothing: bool = True
    savgol_window_divisor: int = 50
    savgol_order: int = 3
    voltage_fwhm: float = 0.01
    capacity_fwhm: float | None = None
    gaussian: GaussianOptions = field(default_factory=GaussianOptions)
    # normalization
    normalize: Literal["area"] | bool = "area"
    normalizing_factor: float | None = None
    normalizing_roof: float | None = None
    # differentiation
    increment_method: Literal["diff"] = "diff"

    def __post_init__(self) -> None:
        # 1.x spelled normalize as a bool; True meant "normalize to area".
        if self.normalize is True:
            object.__setattr__(self, "normalize", "area")
        if self.normalize not in ("area", False):
            raise ValueError(
                f"normalize must be 'area' or False, got {self.normalize!r}"
            )
        if self.increment_method != "diff":
            raise ValueError(
                f"increment_method must be 'diff', got {self.increment_method!r}. "
                "The 'hist' binning method was never finished; it is reachable "
                "through the deprecated Converter class only (see cellpy#566)."
            )
        if self.savgol_order < 1:
            raise ValueError(f"savgol_order must be >= 1, got {self.savgol_order}")
        if self.savgol_window_divisor <= 0:
            raise ValueError(
                f"savgol_window_divisor must be > 0, got {self.savgol_window_divisor}"
            )
        if self.normalizing_roof == 0:
            raise ValueError("normalizing_roof must not be zero")
        if self.max_points is not None and self.max_points < 2:
            raise ValueError(f"max_points must be >= 2, got {self.max_points}")

    def replace(self, **overrides: Any) -> "IcaOptions":
        """Return a copy with *overrides* applied (validated)."""
        unknown = set(overrides) - {f for f in self.__dataclass_fields__}
        if unknown:
            raise TypeError(
                f"unknown IcaOptions field(s): {', '.join(sorted(unknown))}. "
                f"Valid fields: {', '.join(sorted(self.__dataclass_fields__))}"
            )
        return replace(self, **overrides)


#: Sensible defaults for differential voltage analysis. DVA is conventionally
#: read off the raw curve — the information is in *where* the peaks sit on the
#: capacity axis, and area-normalizing would rescale the y-axis for nothing.
DVA_DEFAULTS = IcaOptions(normalize=False)


@dataclass(frozen=True)
class IcaCols:
    """Column names of the specced ICA/DVA output frames.

    This is a data contract: users index the returned frame by these names, so
    it is versioned with the package rather than left to each entry point.
    """

    cycle: str = "cycle"
    direction: str = "direction"
    voltage: str = "voltage"
    capacity: str = "capacity"
    dqdv: str = "dqdv"
    dvdq: str = "dvdq"
    #: Deprecated duplicate of ``dqdv``, kept for one release (removed in 2.1).
    legacy_dqdv: str = "dq"

    def ordered_names(self, derivative: str = "dqdv") -> list[str]:
        """Column order for the given derivative."""
        if derivative == "dqdv":
            return [
                self.cycle,
                self.direction,
                self.voltage,
                self.capacity,
                self.dqdv,
            ]
        return [self.cycle, self.direction, self.capacity, self.voltage, self.dvdq]


ICA_COLS = IcaCols()


# ---------------------------------------------------------------------------
# small helpers (public since 1.x)
# ---------------------------------------------------------------------------


def value_bounds(x) -> tuple[float, float]:
    """Return ``(min, max)`` of *x*."""
    x = np.asarray(x)
    return np.amin(x), np.amax(x)


def index_bounds(x) -> tuple[float, float]:
    """Return ``(first, last)`` item of *x*."""
    if isinstance(x, (pd.DataFrame, pd.Series)):
        return x.iloc[0], x.iloc[-1]
    return x[0], x[-1]


def _savgol_window(n_points: int, divisor: int) -> int:
    """Odd Savitzky-Golay window of at least 3 points.

    Extracted from the two copies in 1.x's ``pre_process_data`` and
    ``increment_data``, which computed it identically.
    """
    effective_divisor = np.amin((divisor, n_points / 5))
    window = int(n_points / effective_divisor)
    if window % 2 == 0:
        window -= 1
    return int(np.amax([3, window]))


# ---------------------------------------------------------------------------
# the pure core
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HalfCycleResult:
    """Output of one half-cycle transform.

    Attributes:
        x: The abscissa — voltage for ``dqdv``, capacity for ``dvdq``.
        y: The derivative itself.
        partner: The other coordinate at the same points, so ICA and DVA curves
            can be cross-plotted. Capacity for ``dqdv``, voltage for ``dvdq``.
        derivative: ``"dqdv"`` or ``"dvdq"``.
        normalizing_factor: The factor actually used. In 1.x this was written
            back onto the ``Converter``, so a reused converter silently carried
            one cycle's normalization into the next; it is returned here
            instead.
        post_smoothing_applied: Whether gaussian post-smoothing survived — it is
            dropped when it raises (see ``notes``).
        notes: Human-readable record of anything the transform had to work
            around.
    """

    x: np.ndarray
    y: np.ndarray
    partner: np.ndarray
    derivative: str
    normalizing_factor: float
    post_smoothing_applied: bool
    notes: tuple[str, ...] = ()


def _resolve_normalizing_factor(capacity, options: IcaOptions) -> float:
    """Derive the normalizing factor from the data, without mutating options."""
    _, end_capacity = index_bounds(capacity)
    factor = (
        end_capacity if options.normalizing_factor is None else options.normalizing_factor
    )
    if options.normalizing_roof is not None:
        factor = factor * end_capacity / options.normalizing_roof
    return factor


def _interpolate_vq(capacity, voltage, options: IcaOptions):
    """Interpolate V(q) onto a uniform capacity grid, optionally pre-smoothed."""
    c1, c2 = index_bounds(capacity)
    n_input = len(capacity)

    if options.max_points is not None:
        n_grid = min(options.max_points, n_input)
    elif options.capacity_resolution is not None:
        n_grid = int(round(abs(c2 - c1) / options.capacity_resolution, 0))
    else:
        n_grid = n_input

    f = interp1d(capacity, voltage, kind=options.interpolation_method)
    capacity_grid = np.linspace(c1, c2, n_grid)
    voltage_grid = f(capacity_grid)

    if options.pre_smoothing:
        voltage_grid = savgol_filter(
            voltage_grid,
            _savgol_window(n_grid, options.savgol_window_divisor),
            options.savgol_order,
        )

    return capacity_grid, voltage_grid


def _invert_qv(capacity_grid, voltage_grid, options: IcaOptions):
    """Invert to q(V) on a uniform voltage grid, optionally smoothed."""
    v1, v2 = value_bounds(voltage_grid)
    if options.voltage_resolution is not None:
        n_grid = int(round(abs(v2 - v1) / options.voltage_resolution, 0))
    else:
        n_grid = int(len(voltage_grid))

    f = interp1d(voltage_grid, capacity_grid, kind=options.interpolation_method)
    voltage_inverted = np.linspace(v1, v2, n_grid)
    step = (v2 - v1) / (n_grid - 1)
    capacity_inverted = f(voltage_inverted)

    if options.diff_smoothing:
        capacity_inverted = savgol_filter(
            capacity_inverted,
            _savgol_window(n_grid, options.savgol_window_divisor),
            options.savgol_order,
        )

    return voltage_inverted, capacity_inverted, step


def _differentiate(ordinate, step):
    """Central-placed finite difference: returns the derivative on midpoints."""
    return np.ediff1d(ordinate) / step


def _midpoints(values, step):
    """The abscissa the finite difference actually belongs to."""
    return values[1:] - 0.5 * step


def _gaussian_smooth(values, fwhm, step, options: IcaOptions):
    """Gaussian post-smoothing with a width expressed in abscissa units.

    ``abs(step)`` because a dV/dQ half-cycle can run down the capacity axis;
    for dQ/dV the step is derived from ``value_bounds`` and is always positive,
    so this matches 1.x exactly there.
    """
    step = abs(step)
    if step != 0 and not np.isinf(fwhm):
        points_fwhm = int(fwhm / step)
    else:
        points_fwhm = 0
    sigma = np.amax([1, points_fwhm / 2])
    return gaussian_filter1d(
        values,
        sigma=sigma,
        order=options.gaussian.order,
        mode=options.gaussian.mode,
        cval=options.gaussian.cval,
        truncate=options.gaussian.truncate,
    )


def _normalize_to_area(values, abscissa, normalizing_factor):
    if len(abscissa) == 0:
        raise NullData("abscissa is empty")
    if len(values) == 0:
        raise NullData("derivative is empty")
    area = simpson(values, x=abscissa)
    return values * normalizing_factor / abs(area)


def _post_process(y, x, step, fwhm, options: IcaOptions, normalizing_factor):
    """Gaussian smoothing then area normalization, with the 1.x retry.

    1.x wrapped the whole post-processing step in a ValueError handler that
    retried once with post-smoothing disabled — copy-pasted for the first and
    last half-cycle. The retry is kept (it rescues short half-cycles) but lives
    in one place and records what it did instead of only logging it.
    """

    def run(with_smoothing: bool):
        out = y
        if with_smoothing:
            out = _gaussian_smooth(out, fwhm, step, options)
        if options.normalize == "area":
            out = _normalize_to_area(out, x, normalizing_factor)
        return out

    if not options.post_smoothing:
        return run(False), False, ()

    try:
        return run(True), True, ()
    except ValueError as exc:
        logging.warning(
            "post-processing failed (%s) - retrying without gaussian smoothing", exc
        )
        return run(False), False, (f"post-smoothing skipped: {exc}",)


def transform_half_cycle(
    voltage,
    capacity,
    options: IcaOptions | None = None,
    *,
    derivative: str = "dqdv",
) -> HalfCycleResult:
    """Transform one half-cycle into dQ/dV or dV/dQ.

    This is the pure core: same inputs, same outputs, no shared state. It is
    public because it is the honest replacement for 1.x's ``dqdv_np`` — the
    "I already have two arrays" case.

    Args:
        voltage: Voltage samples.
        capacity: Capacity samples, monotonic and the same length as *voltage*.
        options: The recipe. Defaults to [`IcaOptions`][cellpy.ica.IcaOptions]
            for ``dqdv`` and to ``DVA_DEFAULTS`` (no normalization) for ``dvdq``.
        derivative: ``"dqdv"`` or ``"dvdq"``.

    Returns:
        A [`HalfCycleResult`][cellpy.ica.HalfCycleResult].

    Raises:
        NullData: If either array is missing, or has one point or fewer.
        ValueError: If *derivative* is not a known mode.

    Example:
        >>> capacity, voltage = c.get_ccap(5, as_frame=False)
        >>> result = transform_half_cycle(voltage, capacity)
        >>> result.x, result.y   # voltage, dQ/dV
    """
    if derivative not in ("dqdv", "dvdq"):
        raise ValueError(
            f"derivative must be 'dqdv' or 'dvdq', got {derivative!r}"
        )
    if options is None:
        options = IcaOptions() if derivative == "dqdv" else DVA_DEFAULTS

    if capacity is None or voltage is None:
        raise NullData("capacity and voltage are both required")
    if len(capacity) <= 1 or len(voltage) <= 1:
        raise NullData("need more than one point to differentiate")
    if len(capacity) != len(voltage):
        raise ValueError(
            f"capacity ({len(capacity)}) and voltage ({len(voltage)}) "
            "must be the same length"
        )

    notes: list[str] = []
    normalizing_factor = _resolve_normalizing_factor(capacity, options)

    capacity_grid, voltage_grid = _interpolate_vq(capacity, voltage, options)

    if derivative == "dqdv":
        voltage_inverted, capacity_inverted, step = _invert_qv(
            capacity_grid, voltage_grid, options
        )
        y = _differentiate(capacity_inverted, step)
        x = _midpoints(voltage_inverted, step)
        partner = 0.5 * (capacity_inverted[1:] + capacity_inverted[:-1])
        fwhm = options.voltage_fwhm
    else:
        # dV/dQ needs no inversion — it is the derivative of the smoothed V(q)
        # representation the pipeline has already built, which makes DVA
        # numerically *simpler* than ICA rather than harder.
        step = (
            (capacity_grid[-1] - capacity_grid[0]) / (len(capacity_grid) - 1)
            if len(capacity_grid) > 1
            else 0.0
        )
        y = _differentiate(voltage_grid, step)
        x = _midpoints(capacity_grid, step)
        partner = 0.5 * (voltage_grid[1:] + voltage_grid[:-1])
        fwhm = options.capacity_fwhm
        if fwhm is None:
            # Match the fraction of the axis that the default voltage_fwhm of
            # 0.01 V covers on a typical ~1 V window: one percent of the span.
            span = abs(capacity_grid[-1] - capacity_grid[0])
            fwhm = span / 100.0 if span else 0.0

    y, post_smoothing_applied, post_notes = _post_process(
        y, x, step, fwhm, options, normalizing_factor
    )
    notes.extend(post_notes)

    return HalfCycleResult(
        x=np.asarray(x),
        y=np.asarray(y),
        partner=np.asarray(partner),
        derivative=derivative,
        normalizing_factor=float(normalizing_factor),
        post_smoothing_applied=post_smoothing_applied,
        notes=tuple(notes),
    )


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _HalfCycle:
    """One half-cycle pulled out of whatever the caller passed in."""

    cycle: int
    direction: str
    voltage: np.ndarray
    capacity: np.ndarray


def _direction_labels(cycle_mode: str | None) -> dict[int, str]:
    mode = (cycle_mode or _DEFAULT_CYCLE_MODE).lower()
    if mode not in _DIRECTION_BY_CYCLE_MODE:
        logging.debug(
            "unknown cycle_mode %r - labelling directions as for %r",
            cycle_mode,
            _DEFAULT_CYCLE_MODE,
        )
        mode = _DEFAULT_CYCLE_MODE
    return _DIRECTION_BY_CYCLE_MODE[mode]


def _is_cell(source: Any) -> bool:
    return hasattr(source, "get_cap") and hasattr(source, "get_cycle_numbers")


def _curves_from_cell(source, cycles, number_of_points) -> pd.DataFrame:
    """The single extraction route (design principle 5).

    1.x had two: the combined path used ``get_cap(method="forth-and-forth")``
    while the split path went through ``collect_capacity_curves`` in the
    *readers* package with its own options. Same public function, different
    extraction semantics depending on ``split=``.
    """
    return source.get_cap(
        cycle=cycles,
        method="forth-and-forth",
        categorical_column=True,
        label_cycle_number=True,
        insert_nan=False,
        number_of_points=number_of_points,
    )


def _half_cycles_from_frame(
    frame: pd.DataFrame, cycle_mode: str | None, direction: str
) -> Iterable[_HalfCycle]:
    labels = _direction_labels(cycle_mode)
    required = {_CCOLS.potential, _CCOLS.capacity, _CCOLS.direction}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            f"curve frame is missing column(s): {', '.join(sorted(missing))}. "
            "Pass a frame from get_cap(categorical_column=True, "
            "label_cycle_number=True)."
        )

    if _CCOLS.cycle_num in frame.columns:
        groups: Any = frame.groupby(_CCOLS.cycle_num)
    else:
        groups = [(0, frame)]

    for cycle_number, cycle_frame in groups:
        cycle_frame = cycle_frame.dropna()
        for code, label in sorted(labels.items()):
            if direction not in (BOTH, label):
                continue
            part = cycle_frame.loc[cycle_frame[_CCOLS.direction] == code]
            if part.empty:
                continue
            yield _HalfCycle(
                cycle=int(cycle_number),
                direction=label,
                voltage=part[_CCOLS.potential].to_numpy(),
                capacity=part[_CCOLS.capacity].to_numpy(),
            )


def _half_cycles_from_arrays(voltage, capacity, direction: str) -> list[_HalfCycle]:
    label = direction if direction in (CHARGE, DISCHARGE) else CHARGE
    return [
        _HalfCycle(
            cycle=0,
            direction=label,
            voltage=np.asarray(voltage),
            capacity=np.asarray(capacity),
        )
    ]


def _resolve_source(
    source, cycles, direction, cycle_mode, number_of_points
) -> tuple[list[_HalfCycle], str | None]:
    """Turn any accepted source into a list of half-cycles."""
    if _is_cell(source):
        mode = cycle_mode or getattr(source, "cycle_mode", None)
        frame = _curves_from_cell(source, cycles, number_of_points)
        if frame is None or len(frame) == 0:
            return [], mode
        return list(_half_cycles_from_frame(frame, mode, direction)), mode

    if isinstance(source, pd.DataFrame):
        return list(_half_cycles_from_frame(source, cycle_mode, direction)), cycle_mode

    if isinstance(source, (tuple, list)) and len(source) == 2:
        voltage, capacity = source
        return _half_cycles_from_arrays(voltage, capacity, direction), cycle_mode

    raise TypeError(
        f"cannot read curves from {type(source)!r}. Pass a CellpyCell, a curve "
        "frame from get_cap, or a (voltage, capacity) pair."
    )


# ---------------------------------------------------------------------------
# the public verbs
# ---------------------------------------------------------------------------


def _empty_frame(derivative: str) -> pd.DataFrame:
    cols = ICA_COLS.ordered_names(derivative)
    if derivative == "dqdv":
        cols = cols + [ICA_COLS.legacy_dqdv]
    return pd.DataFrame({name: pd.Series(dtype="float64") for name in cols})


def _transform_all(
    source,
    derivative: str,
    cycles,
    direction: str,
    options: IcaOptions | None,
    strict: bool,
    cycle_mode: str | None,
    number_of_points: int | None,
    overrides: dict[str, Any],
) -> pd.DataFrame:
    if direction not in (CHARGE, DISCHARGE, BOTH):
        raise ValueError(
            f"direction must be {CHARGE!r}, {DISCHARGE!r} or {BOTH!r}, "
            f"got {direction!r}"
        )

    for legacy_only in ("trim_taper_steps", "steps_to_skip"):
        if legacy_only in overrides:
            raise TypeError(
                f"{legacy_only} is not available on the unified curve-extraction "
                "path yet - it lives on the deprecated dqdv(split=True) route "
                "(see cellpy#566)."
            )

    if options is None:
        options = IcaOptions() if derivative == "dqdv" else DVA_DEFAULTS
    if overrides:
        options = options.replace(**overrides)

    half_cycles, resolved_mode = _resolve_source(
        source, cycles, direction, cycle_mode, number_of_points
    )

    x_name, y_name = (
        (ICA_COLS.voltage, ICA_COLS.dqdv)
        if derivative == "dqdv"
        else (ICA_COLS.capacity, ICA_COLS.dvdq)
    )
    partner_name = ICA_COLS.capacity if derivative == "dqdv" else ICA_COLS.voltage

    pieces: list[pd.DataFrame] = []
    failures: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []

    for half_cycle in half_cycles:
        try:
            result = transform_half_cycle(
                half_cycle.voltage,
                half_cycle.capacity,
                options,
                derivative=derivative,
            )
        except Exception as exc:  # noqa: BLE001 - collected and reported below
            # 1.x substituted empty arrays here and logged at warning level, so
            # a cycle could lose an entire branch with no sign but a missing
            # line on a plot (design principle 6).
            failures.append(
                {
                    "cycle": half_cycle.cycle,
                    "direction": half_cycle.direction,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        if result.notes:
            notes.append(
                {
                    "cycle": half_cycle.cycle,
                    "direction": half_cycle.direction,
                    "notes": list(result.notes),
                }
            )

        pieces.append(
            pd.DataFrame(
                {
                    ICA_COLS.cycle: half_cycle.cycle,
                    ICA_COLS.direction: half_cycle.direction,
                    x_name: result.x,
                    partner_name: result.partner,
                    y_name: result.y,
                }
            )
        )

    if failures:
        summary = ", ".join(
            f"cycle {item['cycle']} {item['direction']}" for item in failures
        )
        message = f"{derivative} failed for {len(failures)} half-cycle(s): {summary}"
        if strict:
            raise ValueError(message)
        warnings.warn(message, RuntimeWarning, stacklevel=3)

    if pieces:
        frame = pd.concat(pieces, ignore_index=True)
        frame = frame[ICA_COLS.ordered_names(derivative)]
    else:
        frame = _empty_frame(derivative)

    if derivative == "dqdv":
        # One release of overlap: `dq` was the 1.x name for this column.
        frame[ICA_COLS.legacy_dqdv] = frame[ICA_COLS.dqdv]

    frame.attrs["derivative"] = derivative
    frame.attrs["options"] = options
    frame.attrs["cycle_mode"] = resolved_mode
    frame.attrs["failures"] = failures
    frame.attrs["notes"] = notes
    frame.attrs["normalized"] = options.normalize
    return frame


def dqdv(
    source,
    cycles=None,
    direction: str = BOTH,
    options: IcaOptions | None = None,
    *,
    strict: bool = False,
    cycle_mode: str | None = None,
    number_of_points: int | None = None,
    **overrides,
) -> pd.DataFrame:
    """Incremental capacity analysis: dQ/dV against voltage.

    Args:
        source: A ``CellpyCell``, a curve frame from
            ``get_cap(categorical_column=True, label_cycle_number=True)``, or a
            ``(voltage, capacity)`` pair of arrays.
        cycles: Cycle number or list of cycle numbers. ``None`` processes all.
        direction: ``"charge"``, ``"discharge"`` or ``"both"``. Replaces 1.x's
            ``split=True``, which returned two frames of a different shape.
        options: An [`IcaOptions`][cellpy.ica.IcaOptions]. Defaults to
            ``IcaOptions()``.
        strict: Raise instead of warning when a half-cycle fails.
        cycle_mode: Overrides the cell's own ``cycle_mode``, which decides
            whether the first half-cycle of each cycle is a charge or a
            discharge.
        number_of_points: Passed to the curve extraction.
        **overrides: Individual [`IcaOptions`][cellpy.ica.IcaOptions] fields,
            for the common case of changing one thing.

    Returns:
        A long frame with columns ``cycle``, ``direction``, ``voltage``,
        ``capacity``, ``dqdv`` - plus a deprecated duplicate ``dq`` column that
        goes away in 2.1. ``frame.attrs`` carries the options used, the
        resolved cycle mode, and any per-half-cycle failures.

    Example:
        >>> frame = dqdv(c, cycles=[1, 2], voltage_resolution=0.005)
        >>> charge = frame[frame.direction == "charge"]
    """
    legacy = _pop_legacy_dqdv_kwargs(overrides)
    if legacy is not None:
        return _legacy_dqdv(source, cycles, legacy, overrides, number_of_points)

    return _transform_all(
        source,
        "dqdv",
        cycles,
        direction,
        options,
        strict,
        cycle_mode,
        number_of_points,
        overrides,
    )


def dvdq(
    source,
    cycles=None,
    direction: str = BOTH,
    options: IcaOptions | None = None,
    *,
    strict: bool = False,
    cycle_mode: str | None = None,
    number_of_points: int | None = None,
    **overrides,
) -> pd.DataFrame:
    """Differential voltage analysis (DVA): dV/dQ against capacity.

    New in cellpy 2.0. DVA is the standard technique for electrode balancing
    and degradation-mode analysis, and cellpy could not compute it - some
    loaders *ingested* a ``dv_dq`` column when the cycler happened to export
    one, but there was no way to derive it from the curves.

    It rides the same pipeline as [`dqdv`][cellpy.ica.dqdv] and is in fact the
    simpler of the two: dQ/dV needs the V(q) curve inverted to q(V) before
    differentiating, while dV/dQ differentiates the smoothed V(q) curve the
    pipeline has already built.

    Args and Returns as [`dqdv`][cellpy.ica.dqdv], except that the frame's
    columns are ``cycle``, ``direction``, ``capacity``, ``voltage``, ``dvdq``,
    and that normalization defaults to ``False``: DVA is read from the peak
    *positions* on the capacity axis, so rescaling the ordinate would only
    obscure the comparison between cycles.

    Example:
        >>> frame = dvdq(c, cycles=1, direction="charge")
        >>> frame.plot(x="capacity", y="dvdq")
    """
    return _transform_all(
        source,
        "dvdq",
        cycles,
        direction,
        options,
        strict,
        cycle_mode,
        number_of_points,
        overrides,
    )


def to_wide(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert a specced long frame to the wide, cycle-per-column layout.

    Wide format is an explicit conversion, not an entry-point mode: in 1.x
    whether you got long or wide depended on ``tidy=`` *and* ``split=``, whose
    defaults disagreed between functions.

    Args:
        frame: A frame from [`dqdv`][cellpy.ica.dqdv] or
            [`dvdq`][cellpy.ica.dvdq].

    Returns:
        A frame whose columns are a ``(cycle, value)`` MultiIndex. When the
        input holds both directions the top level is ``"<cycle> <direction>"``,
        so the two do not collide.
    """
    derivative = frame.attrs.get("derivative", "dqdv")
    x_name, y_name = (
        (ICA_COLS.voltage, ICA_COLS.dqdv)
        if derivative == "dqdv"
        else (ICA_COLS.capacity, ICA_COLS.dvdq)
    )
    if frame.empty:
        return pd.DataFrame()

    both = frame[ICA_COLS.direction].nunique() > 1

    blocks: dict[Any, pd.DataFrame] = {}
    for (cycle, direction_label), group in frame.groupby(
        [ICA_COLS.cycle, ICA_COLS.direction], sort=True
    ):
        key = f"{cycle} {direction_label}" if both else cycle
        blocks[key] = group[[x_name, y_name]].reset_index(drop=True)

    wide = pd.concat(blocks.values(), axis=1, keys=list(blocks))
    wide.columns.names = ["cycle", "value"]
    return wide


# ---------------------------------------------------------------------------
# the deprecated 1.x surface
# ---------------------------------------------------------------------------
#
# Everything below is scheduled for removal in 2.1. It is reimplemented on the
# pure core above rather than kept as a second copy of the math, which is what
# makes tests/data/goldens/ica_dqdv_* meaningful: those oracles were recorded
# against the 1.x code and are reproduced bit-for-bit by these shims.


def _options_from_converter(converter: "Converter") -> IcaOptions:
    """Snapshot a Converter's mutable attributes as an immutable recipe.

    ``normalizing_roof`` is deliberately dropped: ``Converter.inspect_data``
    has already folded it into ``normalizing_factor``, and applying it a second
    time in the core would square it.
    """
    return IcaOptions(
        voltage_resolution=converter.voltage_resolution,
        capacity_resolution=converter.capacity_resolution,
        max_points=converter.max_points,
        interpolation_method=converter.interpolation_method,
        pre_smoothing=converter.pre_smoothing,
        diff_smoothing=converter.smoothing,
        post_smoothing=converter.post_smoothing,
        savgol_window_divisor=converter.savgol_filter_window_divisor_default,
        savgol_order=converter.savgol_filter_window_order,
        voltage_fwhm=converter.voltage_fwhm,
        gaussian=GaussianOptions(
            order=converter.gaussian_order,
            mode=converter.gaussian_mode,
            cval=converter.gaussian_cval,
            truncate=converter.gaussian_truncate,
        ),
        normalize="area" if converter.normalize else False,
        normalizing_factor=converter.normalizing_factor,
        normalizing_roof=None,
    )


class Converter:
    """Deprecated staged dQ/dV converter.

    Use [`transform_half_cycle`][cellpy.ica.transform_half_cycle] instead: it
    takes the same recipe as an [`IcaOptions`][cellpy.ica.IcaOptions] and
    returns its derived quantities rather than writing them back onto itself.

    The five stages (set → inspect → pre-process → increment → post-process)
    are kept because they are how the 1.x characterization tests drive the
    pipeline, but each now delegates to the pure functions above.

    !!! warning "Hidden state"
        ``inspect_data`` overwrites ``normalizing_factor`` from the data, so a
        converter reused across half-cycles carries the previous one's
        normalization into the next. That behaviour is preserved here for
        compatibility; the new core returns the factor instead.
    """

    def __init__(
        self,
        capacity=None,
        voltage=None,
        points_pr_split=10,
        max_points=None,
        voltage_resolution=None,
        capacity_resolution=None,
        minimum_splits=3,
        interpolation_method="linear",
        increment_method="diff",
        pre_smoothing=False,
        smoothing=False,
        post_smoothing=True,
        normalize=True,
        normalizing_factor=None,
        normalizing_roof=None,
        savgol_filter_window_divisor_default=50,
        savgol_filter_window_order=3,
        voltage_fwhm=0.01,
        gaussian_order=0,
        gaussian_mode="reflect",
        gaussian_cval=0.0,
        gaussian_truncate=4.0,
    ):
        warn_once(
            "ica.Converter",
            "cellpy.ica.transform_half_cycle with IcaOptions",
            removal="2.1",
        )
        self.capacity = capacity
        self.voltage = voltage

        self.capacity_preprocessed = None
        self.voltage_preprocessed = None
        self.capacity_inverted = None
        self.voltage_inverted = None

        self.incremental_capacity = None
        self._incremental_capacity = None  # before smoothing
        self.voltage_processed = None
        self._voltage_processed = None  # before shifting / centering

        self.voltage_inverted_step = None

        self.points_pr_split = points_pr_split
        self.max_points = max_points
        self.voltage_resolution = voltage_resolution
        self.capacity_resolution = capacity_resolution
        self.minimum_splits = minimum_splits
        self.interpolation_method = interpolation_method
        self.increment_method = increment_method
        self.pre_smoothing = pre_smoothing
        self.smoothing = smoothing
        self.post_smoothing = post_smoothing
        self.savgol_filter_window_divisor_default = savgol_filter_window_divisor_default
        self.savgol_filter_window_order = savgol_filter_window_order
        self.voltage_fwhm = voltage_fwhm
        self.gaussian_order = gaussian_order
        self.gaussian_mode = gaussian_mode
        self.gaussian_cval = gaussian_cval
        self.gaussian_truncate = gaussian_truncate
        self.normalize = normalize
        self.normalizing_factor = normalizing_factor
        self.normalizing_roof = normalizing_roof

        self.d_capacity_mean = None
        self.d_voltage_mean = None
        self.len_capacity = None
        self.len_voltage = None
        self.min_capacity = None
        self.max_capacity = None
        self.start_capacity = None
        self.end_capacity = None
        self.number_of_points = None
        self.std_err_median = None
        self.std_err_mean = None

        self.fixed_voltage_range = False

        self.errors = []

    def __str__(self):
        txt = f"[ica.converter] {str(type(self))}\n"
        for name, att in vars(self).items():
            if isinstance(att, (pd.DataFrame, pd.Series, np.ndarray)):
                str_att = f"<vector> ({str(type(att))})"
            else:
                str_att = str(att)
            txt += f"{name}: {str_att}\n"
        return txt

    def set_data(self, capacity, voltage=None, capacity_label="q", voltage_label="v"):
        """Set the data."""
        logging.debug("setting data (capacity and voltage)")
        if isinstance(capacity, pd.DataFrame):
            self.capacity = capacity[capacity_label]
            self.voltage = capacity[voltage_label]
        else:
            assert len(capacity) == len(voltage)
            self.capacity = capacity
            self.voltage = voltage

    def inspect_data(self, capacity=None, voltage=None, err_est=False, diff_est=False):
        """Check and inspect the data."""
        from scipy import stats

        logging.debug("inspecting the data")

        if capacity is None:
            capacity = self.capacity
        if voltage is None:
            voltage = self.voltage

        if capacity is None or voltage is None:
            raise NullData

        self.len_capacity = len(capacity)
        self.len_voltage = len(voltage)

        if self.len_capacity <= 1:
            raise NullData
        if self.len_voltage <= 1:
            raise NullData

        self.min_capacity, self.max_capacity = value_bounds(capacity)
        self.start_capacity, self.end_capacity = index_bounds(capacity)

        self.number_of_points = len(capacity)

        if diff_est:
            self.d_capacity_mean = np.mean(np.diff(np.asarray(capacity)))
            self.d_voltage_mean = np.mean(np.diff(np.asarray(voltage)))

        if err_est:
            splits = int(self.number_of_points / self.points_pr_split)
            rest = self.number_of_points % self.points_pr_split

            if splits < self.minimum_splits:
                logging.debug("no point in splitting, too little data")
                self.errors.append("splitting: to few points")
            else:
                if rest > 0:
                    _cap = capacity[:-rest]
                    _vol = voltage[:-rest]
                else:
                    _cap = capacity
                    _vol = voltage

                c_pieces = np.split(np.asarray(_cap), splits)
                v_pieces = np.split(np.asarray(_vol), splits)

                std_err = []
                for c, v in zip(c_pieces, v_pieces):
                    std_err.append(stats.linregress(c, v)[4])

                self.std_err_median = np.median(std_err)
                self.std_err_mean = np.mean(std_err)

        if not self.start_capacity == self.min_capacity:
            self.errors.append("capacity: start<>min")

        if not self.end_capacity == self.max_capacity:
            self.errors.append("capacity: end<>max")

        if self.normalizing_factor is None:
            self.normalizing_factor = self.end_capacity

        if self.normalizing_roof is not None:
            self.normalizing_factor = (
                self.normalizing_factor * self.end_capacity / self.normalizing_roof
            )

    def pre_process_data(self):
        """Interpolate V(q), optionally pre-smoothed."""
        logging.debug("pre-processing the data")
        self.capacity_preprocessed, self.voltage_preprocessed = _interpolate_vq(
            self.capacity, self.voltage, _options_from_converter(self)
        )

    def increment_data(self):
        """Perform the dq-dv transform."""
        logging.debug("incrementing data")
        options = _options_from_converter(self)

        (
            self.voltage_inverted,
            self.capacity_inverted,
            self.voltage_inverted_step,
        ) = _invert_qv(self.capacity_preprocessed, self.voltage_preprocessed, options)

        if self.increment_method == "diff":
            self.incremental_capacity = _differentiate(
                self.capacity_inverted, self.voltage_inverted_step
            )
            self._incremental_capacity = self.incremental_capacity
            self._voltage_processed = self.voltage_inverted[1:]
            self.voltage_processed = _midpoints(
                self.voltage_inverted, self.voltage_inverted_step
            )

        elif self.increment_method == "hist":
            # Never finished ("assigned to Asbjoern", 2018). Kept only so the
            # 1.x characterization test that exercises it still runs; the new
            # IcaOptions rejects it outright. See cellpy#566.
            logging.warning(
                "the 'hist' increment method was never completed and is not "
                "available through the new ica API (cellpy#566)"
            )
            df = pd.DataFrame(
                {"Capacity": self.capacity_inverted, "Voltage": self.voltage_inverted}
            )
            df["dQ"] = df.Capacity.diff()
            df["Voltage"] = df.Voltage.round(decimals=4)
            df = df.groupby(["Voltage"])["dQ"].sum().to_frame().reset_index()
            df["dV"] = df.Voltage.diff().rolling(1).sum()
            df["dQdV"] = df.dQ / df.dV

            self.incremental_capacity = df.dQdV
            self.voltage_processed = df.Voltage

        else:
            raise ValueError(f"unknown increment_method: {self.increment_method!r}")

    def post_process_data(
        self, voltage=None, incremental_capacity=None, voltage_step=None
    ):
        """Smooth, normalize and optionally re-grid the finished derivative."""
        logging.debug("post-processing data")

        if voltage is None:
            voltage = self.voltage_processed
            incremental_capacity = self.incremental_capacity
            voltage_step = self.voltage_inverted_step

        options = _options_from_converter(self)

        if options.post_smoothing:
            incremental_capacity = _gaussian_smooth(
                incremental_capacity, options.voltage_fwhm, voltage_step, options
            )
        if options.normalize == "area":
            incremental_capacity = _normalize_to_area(
                incremental_capacity, voltage, self.normalizing_factor
            )

        self.incremental_capacity = incremental_capacity

        fixed_range = False
        if isinstance(self.fixed_voltage_range, np.ndarray):
            fixed_range = True
        elif self.fixed_voltage_range:
            fixed_range = True

        if fixed_range:
            logging.debug(" - using fixed voltage range (interpolating)")
            v1, v2, number_of_points = self.fixed_voltage_range
            v = np.linspace(v1, v2, number_of_points)
            f = interp1d(
                x=self.voltage_processed,
                y=incremental_capacity,
                kind=self.interpolation_method,
                bounds_error=False,
                fill_value=np.nan,
            )
            self.incremental_capacity = f(v)
            self.voltage_processed = v


def _legacy_half_cycle(cycle_df, code, options: IcaOptions):
    """Run one legacy half-cycle through the pure core."""
    part = cycle_df.loc[cycle_df[_CCOLS.direction] == code]
    result = transform_half_cycle(
        part[_CCOLS.potential], part[_CCOLS.capacity], options, derivative="dqdv"
    )
    return result.x, result.y


def _legacy_options(kwargs: dict[str, Any]) -> IcaOptions:
    """Translate the 1.x Converter keyword soup into an IcaOptions."""
    gaussian = GaussianOptions(
        order=kwargs.get("gaussian_order", 0),
        mode=kwargs.get("gaussian_mode", "reflect"),
        cval=kwargs.get("gaussian_cval", 0.0),
        truncate=kwargs.get("gaussian_truncate", 4.0),
    )
    normalize = kwargs.get("normalize", True)
    return IcaOptions(
        voltage_resolution=kwargs.get("voltage_resolution"),
        capacity_resolution=kwargs.get("capacity_resolution"),
        max_points=kwargs.get("max_points"),
        interpolation_method=kwargs.get("interpolation_method", "linear"),
        pre_smoothing=kwargs.get("pre_smoothing", False),
        diff_smoothing=kwargs.get("smoothing", False),
        post_smoothing=kwargs.get("post_smoothing", True),
        savgol_window_divisor=kwargs.get("savgol_filter_window_divisor_default", 50),
        savgol_order=kwargs.get("savgol_filter_window_order", 3),
        voltage_fwhm=kwargs.get("voltage_fwhm", 0.01),
        gaussian=gaussian,
        normalize="area" if normalize else False,
        normalizing_factor=kwargs.get("normalizing_factor"),
        normalizing_roof=kwargs.get("normalizing_roof"),
    )


def dqdv_cycle(cycle_df, splitter=True, label_direction=False, **kwargs):
    """Deprecated. Use [`dqdv`][cellpy.ica.dqdv] with a curve frame.

    Returns a tuple of numpy arrays rather than a frame, and reports failure by
    substituting empty arrays.

    Args:
        cycle_df: One cycle ('potential', 'capacity', 'direction' as ±1).
        splitter: Insert a NaN row between the two half-cycles.
        label_direction: Also return the ±1 direction array.
    """
    warn_once(
        "ica.dqdv_cycle",
        "cellpy.ica.dqdv (returns the specced long frame)",
        removal="2.1",
    )
    return _dqdv_cycle_impl(
        cycle_df, splitter=splitter, label_direction=label_direction, **kwargs
    )


def _dqdv_cycle_impl(cycle_df, splitter=True, label_direction=False, **kwargs):
    if cycle_df.empty:
        raise NullData(f"The cycle (type={type(cycle_df)}) is empty.")

    options = _legacy_options(kwargs)

    try:
        voltage_first, incremental_first = _legacy_half_cycle(cycle_df, -1, options)
        if splitter:
            voltage_first = np.append(voltage_first, np.nan)
            incremental_first = np.append(incremental_first, np.nan)
    except Exception as e:  # noqa: BLE001 - 1.x behaviour, preserved
        logging.warning("Error in dqdv_cycle - first half-cycle")
        logging.warning(f" - error-message: '{e}'")
        voltage_first = np.array([])
        incremental_first = np.array([])

    try:
        voltage_last, incremental_last = _legacy_half_cycle(cycle_df, 1, options)
        voltage_last = voltage_last[::-1]
        incremental_last = incremental_last[::-1]
    except Exception as e:  # noqa: BLE001 - 1.x behaviour, preserved
        logging.warning("Error in dqdv_cycle - last half-cycle")
        logging.warning(f" - error-message: '{e}'")
        voltage_last = np.array([])
        incremental_last = np.array([])

    voltage = np.concatenate((voltage_first, voltage_last))
    incremental_capacity = np.concatenate((incremental_first, incremental_last))

    if label_direction:
        direction = np.concatenate(
            (-np.ones(len(voltage_first)), np.ones(len(voltage_last)))
        )
        return voltage, incremental_capacity, direction

    return voltage, incremental_capacity


def dqdv_cycles(cycles_df, not_merged=False, label_direction=False, **kwargs):
    """Deprecated. Use [`dqdv`][cellpy.ica.dqdv] with a curve frame.

    Args:
        cycles_df: Curve frame with a cycle-number column.
        not_merged: Return ``(cycle_numbers, frames)`` instead of one frame.
        label_direction: Include the ±1 ``direction`` column.
    """
    warn_once(
        "ica.dqdv_cycles",
        "cellpy.ica.dqdv (returns the specced long frame)",
        removal="2.1",
    )
    return _dqdv_cycles_impl(
        cycles_df, not_merged=not_merged, label_direction=label_direction, **kwargs
    )


def _dqdv_cycles_impl(cycles_df, not_merged=False, label_direction=False, **kwargs):
    if len(cycles_df) < 1:
        logging.debug("no curve data to work with")
        return pd.DataFrame()

    ica_dfs = []
    keys = []
    for cycle_number, cycle in cycles_df.groupby(_CCOLS.cycle_num):
        cycle = cycle.dropna()
        try:
            if label_direction:
                v, dq, direction = _dqdv_cycle_impl(
                    cycle, splitter=True, label_direction=True, **kwargs
                )
                _d = {"voltage": v, "dq": dq, "direction": direction}
                _cols = ["voltage", "dq", "direction"]
            else:
                v, dq = _dqdv_cycle_impl(
                    cycle, splitter=True, label_direction=False, **kwargs
                )
                _d = {"voltage": v, "dq": dq}
                _cols = ["voltage", "dq"]
            _ica_df = pd.DataFrame(_d)
            if not not_merged:
                _cols.insert(0, "cycle")
                _ica_df["cycle"] = cycle_number
                _ica_df = _ica_df[_cols]
            else:
                keys.append(cycle_number)
                _ica_df = _ica_df[_cols]
            ica_dfs.append(_ica_df)
        except NullData:
            logging.debug(f"Could not calculate data for cycle {cycle_number}")

    if not_merged:
        return keys, ica_dfs

    return pd.concat(ica_dfs)


def dqdv_np(
    voltage,
    capacity,
    voltage_resolution=None,
    capacity_resolution=None,
    voltage_fwhm=0.01,
    pre_smoothing=True,
    diff_smoothing=False,
    post_smoothing=True,
    post_normalization=True,
    interpolation_method=None,
    gaussian_order=None,
    gaussian_mode=None,
    gaussian_cval=None,
    gaussian_truncate=None,
    points_pr_split=None,
    savgol_filter_window_divisor_default=None,
    savgol_filter_window_order=None,
    max_points=None,
    **kwargs,
):
    """Deprecated. Use [`transform_half_cycle`][cellpy.ica.transform_half_cycle].

    Returns:
        ``(voltage, dqdv)`` as numpy arrays.
    """
    warn_once(
        "ica.dqdv_np",
        "cellpy.ica.transform_half_cycle with IcaOptions",
        removal="2.1",
    )
    gaussian = GaussianOptions(
        order=0 if gaussian_order is None else gaussian_order,
        mode="reflect" if gaussian_mode is None else gaussian_mode,
        cval=0.0 if gaussian_cval is None else gaussian_cval,
        truncate=4.0 if gaussian_truncate is None else gaussian_truncate,
    )
    options = IcaOptions(
        voltage_resolution=voltage_resolution,
        capacity_resolution=capacity_resolution,
        max_points=max_points,
        interpolation_method=(
            "linear" if interpolation_method is None else interpolation_method
        ),
        pre_smoothing=pre_smoothing,
        diff_smoothing=diff_smoothing,
        post_smoothing=post_smoothing,
        savgol_window_divisor=(
            50
            if savgol_filter_window_divisor_default is None
            else savgol_filter_window_divisor_default
        ),
        savgol_order=(
            3 if savgol_filter_window_order is None else savgol_filter_window_order
        ),
        voltage_fwhm=voltage_fwhm,
        gaussian=gaussian,
        normalize="area" if post_normalization else False,
        normalizing_factor=kwargs.get("normalizing_factor"),
        normalizing_roof=kwargs.get("normalizing_roof"),
    )
    result = transform_half_cycle(voltage, capacity, options, derivative="dqdv")
    return result.x, result.y


def _constrained_dq_dv_using_dataframes(capacity, minimum_v, maximum_v, **kwargs):
    """The legacy split path's per-cycle transform, onto a fixed voltage grid."""
    options = _legacy_options(kwargs)
    result = transform_half_cycle(
        capacity["v"], capacity["q"], options, derivative="dqdv"
    )
    v = np.linspace(minimum_v, maximum_v, 100)
    f = interp1d(
        x=result.x,
        y=result.y,
        kind=options.interpolation_method,
        bounds_error=False,
        fill_value=np.nan,
    )
    return v, f(v)


def _make_ica_charge_curves(cycles_dfs, cycle_numbers, minimum_v, maximum_v, **kwargs):
    incremental_charge_list = []

    for c, n in zip(cycles_dfs, cycle_numbers):
        if c.empty:
            logging.info(f"{n} is empty")
            v = [np.nan]
            dq = [np.nan]
        else:
            v, dq = _constrained_dq_dv_using_dataframes(
                c, minimum_v, maximum_v, **kwargs
            )
        if not incremental_charge_list:
            d = pd.DataFrame({"v": v})
            d.name = "voltage"
            incremental_charge_list.append(d)

        d = pd.DataFrame({"dq": dq})
        d.name = n
        incremental_charge_list.append(d)

    return incremental_charge_list


def _dqdv_split_frames(
    cell,
    tidy=False,
    trim_taper_steps=None,
    steps_to_skip=None,
    steptable=None,
    max_cycle_number=None,
    **kwargs,
):
    """The legacy ``split=True`` path.

    Kept verbatim in behaviour, including the fact that it reaches the curves
    through ``collect_capacity_curves`` in the *readers* package rather than
    ``get_cap`` — the asymmetry the redesign exists to remove.
    """
    from cellpy.readers.data_structures import collect_capacity_curves

    cycle = kwargs.pop("cycle", None)
    if cycle and not isinstance(cycle, (list, tuple)):
        cycle = [cycle]

    frames = []
    for direction in ("charge", "discharge"):
        dfs, cycles, minimum_v, maximum_v = collect_capacity_curves(
            cell,
            direction=direction,
            trim_taper_steps=trim_taper_steps,
            steps_to_skip=steps_to_skip,
            steptable=steptable,
            max_cycle_number=max_cycle_number,
            cycle=cycle,
        )
        logging.debug(f"retrieved {len(dfs)} {direction} cycles")
        ica_dfs = _make_ica_charge_curves(dfs, cycles, minimum_v, maximum_v, **kwargs)
        frame = pd.concat(ica_dfs, axis=1, keys=[k.name for k in ica_dfs])
        frame.columns.names = ["cycle", "value"]
        if tidy:
            frame = frame.melt(
                "voltage", var_name="cycle", value_name="dq", col_level=0
            )
        frames.append(frame)

    return frames[0], frames[1]


def _dqdv_combined_frame(cell, tidy=True, label_direction=False, **kwargs):
    """The legacy non-split path."""
    cycle = kwargs.pop("cycle", None)
    number_of_points = kwargs.pop("number_of_points", None)
    cycles = cell.get_cap(
        cycle=cycle,
        method="forth-and-forth",
        categorical_column=True,
        label_cycle_number=True,
        insert_nan=False,
        number_of_points=number_of_points,
    )

    ica_df = _dqdv_cycles_impl(
        cycles, not_merged=not tidy, label_direction=label_direction, **kwargs
    )

    if not tidy:
        keys, frames = ica_df
        return pd.concat(frames, axis=1, keys=keys)

    return ica_df


# --- the 1.x dqdv() call patterns -------------------------------------------
#
# `dqdv` keeps its name but returns the specced frame. The 1.x-only keywords
# that changed the *shape* of the return value route to the old implementation
# and warn, so existing scripts keep working for one release instead of
# silently receiving a differently-shaped frame.

_LEGACY_DQDV_KWARGS = ("split", "tidy", "label_direction", "cycle")


def _pop_legacy_dqdv_kwargs(overrides: dict[str, Any]) -> dict[str, Any] | None:
    """Remove 1.x-only keywords from *overrides*; return them, or None."""
    legacy = {
        key: overrides.pop(key) for key in _LEGACY_DQDV_KWARGS if key in overrides
    }
    if not legacy:
        return None

    if "cycle" in legacy:
        warn_once("ica.dqdv(cycle=...)", "cellpy.ica.dqdv(cycles=...)", removal="2.1")
    if "label_direction" in legacy:
        warn_once(
            "ica.dqdv(label_direction=...)",
            "the direction column, which the specced frame always carries",
            removal="2.1",
        )
    if "split" in legacy or "tidy" in legacy:
        warn_once(
            "ica.dqdv(split=... / tidy=...)",
            "cellpy.ica.dqdv(direction=...) and cellpy.ica.to_wide()",
            removal="2.1",
        )
    return legacy


def _legacy_dqdv(
    source,
    cycles,
    legacy: dict[str, Any],
    overrides: dict[str, Any],
    number_of_points: int | None,
):
    """Reproduce the 1.x ``dqdv`` return shapes."""
    split = legacy.get("split", False)
    tidy = legacy.get("tidy", True)
    label_direction = legacy.get("label_direction", False)
    cycle = legacy.get("cycle", cycles)

    kwargs = dict(overrides)
    if cycle is not None:
        kwargs["cycle"] = cycle
    if number_of_points is not None:
        kwargs["number_of_points"] = number_of_points

    if split:
        kwargs.pop("number_of_points", None)  # the split path never took it
        return _dqdv_split_frames(source, tidy=tidy, **kwargs)

    if not tidy or label_direction:
        return _dqdv_combined_frame(
            source, tidy=tidy, label_direction=label_direction, **kwargs
        )

    # Only `cycle=` was renamed away: the caller did not ask for a legacy
    # *shape*, so give them the specced frame.
    return _transform_all(
        source, "dqdv", cycle, BOTH, None, False, None, number_of_points, overrides
    )
