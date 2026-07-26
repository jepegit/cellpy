"""Batch runner (batch v3, #700).

Per-cell work is a pure function -- one cell in, one result out, no shared
mutable state. Serial vs parallel execution is then a choice of executor, not a
second 300-line method (the legacy ``update`` / ``parallel_update`` clone).
This arc ships the serial executor; the process pool is A8 (#704).
"""

from __future__ import annotations

import time
from typing import Any, Callable

from cellpy import get as _cellpy_get
from cellpy.batch.journal import Journal
from cellpy.batch.policy import CellSpec, LoadPolicy, SourcePreference, resolve_specs
from cellpy.batch.result import BatchResult, CellOutcome, CellResult

ProgressHook = Callable[[int, int, CellResult], None]


def _get_kwargs(spec: CellSpec, policy: LoadPolicy) -> tuple[dict, str | None]:
    """Map a resolved :class:`CellSpec` + policy onto ``cellpy.get`` kwargs.

    Returns the kwargs and the source label ("cellpy"/"raw"/None) we expect.
    """
    kwargs: dict[str, Any] = {
        "mass": spec.mass,
        "nominal_capacity": spec.nom_cap,
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
    else:  # AUTO
        kwargs["cellpy_file"] = spec.cellpy_file
        kwargs["filename"] = raw
        source = "cellpy" if spec.cellpy_file else ("raw" if raw else None)

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


def run(
    journal: Journal,
    policy: LoadPolicy | None = None,
    per_cell: dict | None = None,
    on_progress: ProgressHook | None = None,
) -> BatchResult:
    """Load every cell in ``journal`` (serial), returning a :class:`BatchResult`.

    Progress is reported via the ``on_progress`` callback; the runner never
    imports tqdm or prints.
    """
    policy = policy or LoadPolicy()
    specs = resolve_specs(journal, policy, per_cell)
    bad = set(journal.session.get("bad_cells") or []) if policy.skip_bad_cells else set()

    results: list[CellResult] = []
    total = len(specs)
    for index, spec in enumerate(specs, start=1):
        if spec.label in bad:
            result = CellResult(spec.label, CellOutcome.SKIPPED, source=None)
        else:
            result = load_cell(spec, policy)
        results.append(result)
        if on_progress is not None:
            on_progress(index, total, result)
    return BatchResult(results)
