# Issue #476: golden test fails

Source: https://github.com/jepegit/cellpy/issues/476

## Original issue text

Part 1: loader_pec_csv golden fails on Windows (datetime64[ns] vs datetime64[us]. Fix it.

Part 2: Benchmarks fail. Tests seem flaky. Either due to bad limits or floating benchmark values. Set to limits, warning + exception. Exception only with extreme slow-downs (> 100%). Error message:

```
Run uv run pytest benchmarks/ --benchmark-only --benchmark-json=/tmp/bench.json
============================= test session starts ==============================
platform linux -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/cellpy/cellpy/.venv/bin/python
cachedir: .pytest_cache
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/runner/work/cellpy/cellpy
configfile: pyproject.toml
plugins: benchmark-5.2.3, timeout-2.4.0
collecting ... collected 5 items

benchmarks/test_performance.py::test_benchmark_single_cell_pipeline PASSED [ 20%]
benchmarks/test_performance.py::test_benchmark_batch_summary_collection PASSED [ 40%]
benchmarks/test_performance.py::test_benchmark_v8_cellpy_file_load PASSED [ 60%]
benchmarks/test_performance.py::test_benchmark_get_cap_all_cycles PASSED [ 80%]

Wrote benchmark data in: <_io.BufferedWriter name='/tmp/bench.json'>
benchmarks/test_performance.py::test_benchmark_peak_rss_kib PASSED       [100%]

=============================== warnings summary ===============================
benchmarks/test_performance.py::test_benchmark_single_cell_pipeline
benchmarks/test_performance.py::test_benchmark_single_cell_pipeline
benchmarks/test_performance.py::test_benchmark_get_cap_all_cycles
benchmarks/test_performance.py::test_benchmark_peak_rss_kib
  /home/runner/work/cellpy/cellpy/cellpy/readers/cellreader.py:5919: DeprecationWarning: `specific_converters` is deprecated; use `specific_conversion_factors` instead
    data = self.core.add_scaled_summary_columns(

benchmarks/test_performance.py::test_benchmark_v8_cellpy_file_load
benchmarks/test_performance.py::test_benchmark_v8_cellpy_file_load
  /home/runner/work/cellpy/cellpy/cellpy/readers/cellreader.py:2335: UserWarning: no fid_table - you should update your cellpy-file
    warnings.warn("no fid_table - you should update your cellpy-file")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

---------------------------------------------------------------------------------------------- benchmark: 5 tests ---------------------------------------------------------------------------------------------
Name (time in ms)                                Min                 Max                Mean            StdDev              Median               IQR            Outliers      OPS            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_benchmark_batch_summary_collection      61.7604 (1.0)       61.7604 (1.0)       61.7604 (1.0)      0.0000 (1.0)       61.7604 (1.0)      0.0000 (1.0)           0;0  16.1916 (1.0)           1           1
test_benchmark_get_cap_all_cycles            72.3815 (1.17)      72.3815 (1.17)      72.3815 (1.17)     0.0000 (1.0)       72.3815 (1.17)     0.0000 (1.0)           0;0  13.8157 (0.85)          1           1
test_benchmark_v8_cellpy_file_load           87.2147 (1.41)      87.2147 (1.41)      87.2147 (1.41)     0.0000 (1.0)       87.2147 (1.41)     0.0000 (1.0)           0;0  11.4660 (0.71)          1           1
test_benchmark_single_cell_pipeline         149.1890 (2.42)     149.1890 (2.42)     149.1890 (2.42)     0.0000 (1.0)      149.1890 (2.42)     0.0000 (1.0)           0;0   6.7029 (0.41)          1           1
test_benchmark_peak_rss_kib                 153.5246 (2.49)     153.5246 (2.49)     153.5246 (2.49)     0.0000 (1.0)      153.5246 (2.49)     0.0000 (1.0)           0;0   6.5136 (0.40)          1           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
============================== slowest durations ===============================
5.80s setup    benchmarks/test_performance.py::test_benchmark_batch_summary_collection
2.13s call     benchmarks/test_performance.py::test_benchmark_single_cell_pipeline
0.17s call     benchmarks/test_performance.py::test_benchmark_v8_cellpy_file_load
0.16s setup    benchmarks/test_performance.py::test_benchmark_get_cap_all_cycles
0.15s call     benchmarks/test_performance.py::test_benchmark_peak_rss_kib
0.07s call     benchmarks/test_performance.py::test_benchmark_get_cap_all_cycles
0.07s call     benchmarks/test_performance.py::test_benchmark_batch_summary_collection

(8 durations < 0.005s hidden.  Use -vv to show these durations.)
======================== 5 passed, 6 warnings in 10.60s ========================
Benchmark baseline regression:
  - test_benchmark_batch_summary_collection: mean 0.061760s vs baseline 0.048794s (ratio 1.266, max slowdown +20%)
```
