# Speed harness (#895)

Diagnostic scripts from the 2026-08-15 perceived-speed session. They take
**your** journal / paths via environment variables. Do not put hostnames,
usernames, project names, or cell IDs in these files.

Findings (anonymized): [`NOTES.md`](NOTES.md). Issue: [jepegit/cellpy#895](https://github.com/jepegit/cellpy/issues/895).

Scratch copies land in `_tmp/` (gitignored).

## Env

| Variable | Used by | What |
| --- | --- | --- |
| `SPEEDTEST_JOURNAL` | most scripts | path to a batch journal JSON (keep it out of git) |
| `SPEEDTEST_LABEL` | one-cell / OtherPath / h5 | cell label; default = first journal row |
| `SPEEDTEST_PROJECT` | filefinder | project subfolder under `rawdatadir` |
| `SPEEDTEST_EXT` | filefinder | raw extension without dot (default `h5`) |
| `SPEEDTEST_CELLPY` | `time_cellpy_io.py` | one local `.cellpy` |
| `SPEEDTEST_RAW` | OtherPath / h5 | optional raw URI override |
| `SPEEDTEST_RAW_LOCAL` | `time_arbin_h5.py` | optional already-copied local raw |

Scripts print **basenames** or redacted URIs (`scp://<host>/…`), not full lab paths.

## Run

Use the project env (conda `cellpy_dev_313` or `uv run`). Example (Windows cmd):

```bat
set SPEEDTEST_JOURNAL=C:\path\to\your_journal.json
set SPEEDTEST_PROJECT=YourProject
set SPEEDTEST_CELLPY=C:\path\to\one.cellpy
python dev/speed-test-01/time_imports.py
python dev/speed-test-01/time_one_cell.py
python dev/speed-test-01/time_otherpath.py
python dev/speed-test-01/time_otherpath.py --cold
python dev/speed-test-01/time_executors.py
python dev/speed-test-01/time_filefinder.py
python dev/speed-test-01/time_cellpy_io.py
python dev/speed-test-01/time_arbin_h5.py
```

`summarize_importtime.py` only needs a `python -X importtime` dump:

```bat
python -X importtime -c "import pandas" 2> importtime.txt
python dev/speed-test-01/summarize_importtime.py importtime.txt
```
