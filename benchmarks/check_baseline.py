#!/usr/bin/env python3
"""Compare a pytest-benchmark JSON run against the committed v1.x baseline.

Warns on moderate slowdowns; fails only on extreme regressions. Faster runs
pass — refresh the committed baseline when an intentional speedup should become
the new ruler.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompareResult:
    """Outcome of comparing current benchmark means to a baseline."""

    warnings: tuple[str, ...]
    failures: tuple[str, ...]


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
    current_path: Path,
    baseline_path: Path,
    *,
    warn_tolerance: float = 0.20,
    fail_tolerance: float = 1.0,
) -> CompareResult:
    """Compare benchmark means to baseline with tiered warn/fail bands.

    Args:
        current_path: pytest-benchmark JSON from the current run.
        baseline_path: committed baseline JSON.
        warn_tolerance: Emit a warning when slowdown exceeds this fraction
            (default 0.20 = +20%%).
        fail_tolerance: Fail when slowdown exceeds this fraction (default 1.0 =
            +100%%, ratio 2.0).

    Returns:
        CompareResult with warning and failure messages.
    """
    current = json.loads(current_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    cur = _means_by_name(current)
    ref = _means_by_name(baseline)
    warnings: list[str] = []
    failures: list[str] = []
    warn_ratio = 1 + warn_tolerance
    fail_ratio = 1 + fail_tolerance

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
        message = (
            f"{name}: mean {cur_mean:.6f}s vs baseline {ref_mean:.6f}s "
            f"(ratio {ratio:.3f})"
        )
        if ratio > fail_ratio:
            failures.append(
                f"{message}, exceeds max slowdown +{fail_tolerance:.0%}"
            )
        elif ratio > warn_ratio:
            warnings.append(
                f"{message}, above warn threshold +{warn_tolerance:.0%}"
            )

    return CompareResult(tuple(warnings), tuple(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "current", type=Path, help="pytest-benchmark JSON from the current run"
    )
    parser.add_argument("baseline", type=Path, help="committed baseline JSON")
    parser.add_argument(
        "--warn-tolerance",
        type=float,
        default=0.20,
        help="warn when slowdown exceeds this fraction (default: 0.20 = +20%%)",
    )
    parser.add_argument(
        "--fail-tolerance",
        type=float,
        default=1.0,
        help="fail when slowdown exceeds this fraction (default: 1.0 = +100%%)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=None,
        help="deprecated alias for --warn-tolerance",
    )
    args = parser.parse_args(argv)

    warn_tolerance = args.warn_tolerance
    if args.tolerance is not None:
        warn_tolerance = args.tolerance

    result = compare(
        args.current,
        args.baseline,
        warn_tolerance=warn_tolerance,
        fail_tolerance=args.fail_tolerance,
    )
    if result.warnings:
        print("Benchmark baseline warnings:", file=sys.stderr)
        for item in result.warnings:
            print(f"  - {item}", file=sys.stderr)
    if result.failures:
        print("Benchmark baseline regression:", file=sys.stderr)
        for item in result.failures:
            print(f"  - {item}", file=sys.stderr)
        return 1
    if result.warnings:
        print(
            f"Benchmarks within +{args.fail_tolerance:.0%} fail band vs {args.baseline} "
            f"({len(result.warnings)} warn-only slowdown(s))"
        )
    else:
        print(
            f"No benchmark slowdown beyond +{warn_tolerance:.0%} vs {args.baseline} "
            "(faster runs are OK — rebaseline when intentional)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
