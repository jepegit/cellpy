# Issue #916 — status

Interactive `/iflow-fix` session: add progress bars for batch.

- [x] Done

## Iterative fixes log

- 2026-08-15: One PR for the whole bar surface. Process-wide `ProgressEvent` bus (`cellpy.internals.progress`); `tqdm.auto` UI (`cellpy.batch.progress`) for TTY + JupyterLab; overall + per-cell copy/parse/save; threads get one child bar per in-flight cell; processes keep overall only. `progress=None|False|True|callable`. 3-arg `on_progress` unchanged. Byte ticks on `OtherPath.copy` when fsspec `callback=` works.

## Close

Landed on `916-add-progress-bars-for-batch`. Local `tests/test_batch_progress.py` (14) plus runner/copy/persist tests green. Full `pytest -m essential` on this Windows box still dies in matplotlib (`0xc06d007f`) — pre-existing, Linux CI is the gate.
