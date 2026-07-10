#!/usr/bin/env python3
"""Compare a pytest-benchmark JSON run against the committed v1.x baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _means_by_name(payload: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for bench in payload.get("benchmarks", []):
        name = bench.get("name")
        stats = bench.get("stats") or {}
        mean = stats.get("mean")
        if name and mean is not None:
            out[name] = float(mean)
    return out


def compare(
    current_path: Path, baseline_path: Path, tolerance: float = 0.20
) -> list[str]:
    current = json.loads(current_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    cur = _means_by_name(current)
    ref = _means_by_name(baseline)
    failures: list[str] = []

    for name, ref_mean in sorted(ref.items()):
        if name.startswith("test_benchmark_peak_rss"):
            continue
        if name not in cur:
            failures.append(f"missing benchmark {name!r} in current run")
            continue
        cur_mean = cur[name]
        if ref_mean <= 0:
            failures.append(f"{name}: invalid baseline mean {ref_mean}")
            continue
        ratio = cur_mean / ref_mean
        if ratio > 1 + tolerance or ratio < 1 - tolerance:
            failures.append(
                f"{name}: mean {cur_mean:.6f}s vs baseline {ref_mean:.6f}s "
                f"(ratio {ratio:.3f}, allowed ±{tolerance:.0%})"
            )

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "current", type=Path, help="pytest-benchmark JSON from the current run"
    )
    parser.add_argument("baseline", type=Path, help="committed baseline JSON")
    parser.add_argument("--tolerance", type=float, default=0.20)
    args = parser.parse_args(argv)

    failures = compare(args.current, args.baseline, tolerance=args.tolerance)
    if failures:
        print("Benchmark baseline regression:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print(f"Benchmark means within ±{args.tolerance:.0%} of {args.baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
