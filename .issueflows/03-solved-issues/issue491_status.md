# Issue #491 — Iterative fixes: full-suite test failures

Interactive `/iflow-fix` session.

- [x] Done

## Iterative fixes log

- **2026-07-14** — `test_extract_fids_from_cellpy_file`: call module-level `extract_fids_from_cellpy_file` from `cellpy.readers.cellpy_file.read` instead of removed `CellpyCell._extract_fids_from_cellpy_file`.
- **2026-07-14** — `test_check_file_ids_external_not_accessible`: monkeypatch external `OtherPath.is_file` → `False` so test exercises inaccessible-file path without live SCP (avoids ~22s timeout).
- **2026-07-14** — `curve_get_dcap_null_cycle` / ODBC flake: close Access ODBC connections in `arbin_res._query_table` and dispose SQLAlchemy engine in `_loader_win` finally block (prevents connection exhaustion in long test runs).
