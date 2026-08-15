"""Time batch.runner.run() serial vs threads vs processes.

    set SPEEDTEST_JOURNAL=path/to/journal.json
    python dev/speed-test-01/time_executors.py
"""

from __future__ import annotations

import logging
import time

from _common import journal_path

logging.basicConfig(level=logging.WARNING)

from cellpy.batch.journal import FILENAME, Journal, read_journal
from cellpy.batch.policy import LoadPolicy, SourcePreference
from cellpy.batch.runner import run


def _subset(journal: Journal, labels: list[str]) -> Journal:
    pages = journal.pages.filter(journal.pages[FILENAME].is_in(labels))
    return Journal(
        name=journal.name,
        project=journal.project,
        pages=pages,
        session=journal.session,
        meta=journal.meta,
    )


def _report(title: str, result, wall: float) -> None:
    rows = list(result)
    failed = [r for r in rows if r.outcome.value == "failed"]
    loaded = [r for r in rows if r.outcome.value == "loaded"]
    cell_s = [r.seconds for r in loaded]
    print(
        f"\n== {title}  wall={wall:.2f}s  n={len(rows)} "
        f"loaded={len(loaded)} failed={len(failed)}",
        flush=True,
    )
    if cell_s:
        print(
            f"   per-cell s: min={min(cell_s):.2f}  "
            f"median={sorted(cell_s)[len(cell_s)//2]:.2f}  "
            f"max={max(cell_s):.2f}  sum={sum(cell_s):.2f}",
            flush=True,
        )
    for r in failed[:5]:
        print(f"   FAIL {r.label}: {type(r.error).__name__}: {r.error}", flush=True)


def _run(journal: Journal, policy: LoadPolicy, executor: str, title: str) -> None:
    t0 = time.perf_counter()
    result = run(journal, policy, executor=executor)
    _report(title, result, time.perf_counter() - t0)


def main() -> None:
    journal = read_journal(journal_path())
    labels = list(journal.pages[FILENAME])
    print(f"journal cells={len(labels)}", flush=True)
    auto = LoadPolicy(source=SourcePreference.AUTO, accept_errors=True)
    raw = LoadPolicy(source=SourcePreference.RAW_ONLY, accept_errors=True)
    raw_journal = _subset(journal, labels[:3])

    for ex in ("serial", "threads", "processes"):
        _run(journal, auto, ex, f"AUTO {ex} (local .cellpy)")
    for ex in ("serial", "threads", "processes"):
        _run(raw_journal, raw, ex, f"RAW_ONLY {ex} (first 3 raw)")


if __name__ == "__main__":
    main()
