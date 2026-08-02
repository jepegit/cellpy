"""Batch runner.

Per-cell work is a pure function -- one cell in, one result out, no shared
mutable state. Serial vs parallel execution is then a choice of executor, not a
second 300-line method (the legacy ``update`` / ``parallel_update`` clone):
``executor="serial" | "threads" | "processes"`` all reuse :func:`load_cell`.
"""

from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from cellpy import get as _cellpy_get
from cellpy.batch.journal import Journal
from cellpy.batch.policy import CellSpec, LoadPolicy, SourcePreference, resolve_specs
from cellpy.batch.result import BatchResult, CellOutcome, CellResult

ProgressHook = Callable[[int, int, CellResult], None]


def _cellpy_file_exists(path: Any) -> bool:
    """True when ``path`` points at an existing local cellpy file."""
    if path is None:
        return False
    try:
        return Path(path).expanduser().is_file()
    except (OSError, TypeError, ValueError):
        return False


def _get_kwargs(spec: CellSpec, policy: LoadPolicy) -> tuple[dict, str | None]:
    """Map a resolved :class:`CellSpec` + policy onto ``cellpy.get`` kwargs.

    Returns the kwargs and the source label ("cellpy"/"raw"/None) we expect.

    ``AUTO`` loads an existing local ``.cellpy`` without a raw freshness check;
    use ``NEWEST`` to pass both paths into ``cellpy.get`` (remote/raw stats).
    """
    kwargs: dict[str, Any] = {
        "mass": spec.mass,
        "nominal_capacity": spec.nom_cap,
        "nom_cap_specifics": spec.nom_cap_specifics,
        "area": spec.area,
        "cycle_mode": spec.cycle_mode,
        "instrument": spec.instrument,
        "model": spec.model,
        "selector": policy.selector,
    }

    raw = spec.raw_files or None
    if policy.source is SourcePreference.RAW_ONLY:
        kwargs["filename"] = raw
        source = "raw" if raw else None
    elif policy.source is SourcePreference.CELLPY_ONLY:
        kwargs["cellpy_file"] = spec.cellpy_file
        source = "cellpy" if spec.cellpy_file else None
    elif policy.source is SourcePreference.NEWEST:
        kwargs["cellpy_file"] = spec.cellpy_file
        kwargs["filename"] = raw
        source = "cellpy" if spec.cellpy_file else ("raw" if raw else None)
    else:  # AUTO: prefer existing local cellpy; no remote FID check
        if _cellpy_file_exists(spec.cellpy_file):
            kwargs["cellpy_file"] = spec.cellpy_file
            source = "cellpy"
        else:
            kwargs["filename"] = raw
            source = "raw" if raw else None

    kwargs = {key: val for key, val in kwargs.items() if val is not None}
    kwargs.update(policy.loader_kwargs)
    return kwargs, source


def load_cell(spec: CellSpec, policy: LoadPolicy | None = None) -> CellResult:
    """Load one cell from its resolved spec. Pure-ish: no prints, no mutation.

    Returns a :class:`CellResult` carrying the cell or the exception; only
    re-raises when ``policy.accept_errors`` is False.
    """
    policy = policy or LoadPolicy()
    kwargs, source = _get_kwargs(spec, policy)

    started = time.perf_counter()
    try:
        cell = _cellpy_get(**kwargs)
        if policy.recalc and cell is not None:
            # Summary C-rates are derived from the step table; remake both.
            cell.make_step_table()
            cell.make_summary()
    except Exception as error:  # noqa: BLE001 - errors are data (accept_errors)
        if not policy.accept_errors:
            raise
        return CellResult(
            label=spec.label,
            outcome=CellOutcome.FAILED,
            source=source,
            seconds=time.perf_counter() - started,
            error=error,
        )
    return CellResult(
        label=spec.label,
        outcome=CellOutcome.LOADED,
        cell=cell,
        source=source,
        seconds=time.perf_counter() - started,
    )


def _strip_cell(result: CellResult) -> CellResult:
    """Drop the live cell (and un-pickleable exception) for cross-process return."""
    if result.cell is None and (result.error is None or isinstance(result.error, RuntimeError)):
        return result
    return CellResult(
        label=result.label,
        outcome=result.outcome,
        cell=None,
        source=result.source,
        seconds=result.seconds,
        error=None if result.error is None else RuntimeError(str(result.error)),
    )


def _dispatch(spec: CellSpec, policy: LoadPolicy, bad: frozenset) -> CellResult:
    if spec.label in bad:
        return CellResult(spec.label, CellOutcome.SKIPPED, source=None)
    return load_cell(spec, policy)


def _dispatch_lite(spec: CellSpec, policy: LoadPolicy, bad: frozenset) -> CellResult:
    """Process-pool worker: like :func:`_dispatch` but returns a picklable result.

    The live :class:`CellpyCell` is not returned across the process boundary
    (batch plan section 7, Windows pickling); ``executor="processes"`` yields
    outcomes/timings, and cells are re-read from their cellpy files on demand.
    """
    return _strip_cell(_dispatch(spec, policy, bad))


def _run_serial(specs, policy, bad, on_progress) -> list[CellResult]:
    results: list[CellResult] = []
    total = len(specs)
    for index, spec in enumerate(specs, start=1):
        result = _dispatch(spec, policy, bad)
        results.append(result)
        if on_progress is not None:
            on_progress(index, total, result)
    return results


def _run_pool(pool_cls, worker, specs, policy, bad, on_progress) -> list[CellResult]:
    results: list[CellResult | None] = [None] * len(specs)
    total = len(specs)
    with pool_cls() as pool:
        futures = {
            pool.submit(worker, spec, policy, bad): i
            for i, spec in enumerate(specs)
        }
        done = 0
        for future in as_completed(futures):
            index = futures[future]
            results[index] = future.result()
            done += 1
            if on_progress is not None:
                on_progress(done, total, results[index])
    return results  # type: ignore[return-value]


def _run_threads(specs, policy, bad, on_progress) -> list[CellResult]:
    return _run_pool(ThreadPoolExecutor, _dispatch, specs, policy, bad, on_progress)


def _run_processes(specs, policy, bad, on_progress) -> list[CellResult]:
    return _run_pool(ProcessPoolExecutor, _dispatch_lite, specs, policy, bad, on_progress)


#: Available executors. Serial/threads keep live cells; processes returns
#: outcomes only (frames/paths, not live objects) to stay pickle-safe.
EXECUTORS = {
    "serial": _run_serial,
    "threads": _run_threads,
    "processes": _run_processes,
}


def run(
    journal: Journal,
    policy: LoadPolicy | None = None,
    per_cell: dict | None = None,
    on_progress: ProgressHook | None = None,
    executor: str = "serial",
) -> BatchResult:
    """Load every cell in ``journal``, returning a :class:`BatchResult`.

    ``executor`` chooses ``"serial"`` (default), ``"threads"`` or
    ``"processes"`` -- all reuse :func:`load_cell`. Progress is reported via the
    ``on_progress`` callback; the runner never imports tqdm or prints.
    """
    policy = policy or LoadPolicy()
    specs = resolve_specs(journal, policy, per_cell)
    bad = (
        frozenset(journal.session.get("bad_cells") or [])
        if policy.skip_bad_cells
        else frozenset()
    )
    try:
        runner_fn = EXECUTORS[executor]
    except KeyError:
        raise ValueError(
            f"unknown executor {executor!r}; choose one of {sorted(EXECUTORS)}"
        ) from None
    return BatchResult(runner_fn(specs, policy, bad, on_progress))
