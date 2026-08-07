# Issue #837 — plan

## Goal

Make `cellpy info --version` (and other light CLI entry) avoid loading the full scientific stack so warm runs are well under ~1–2 s and cold conda first-runs no longer look hung for minutes.

## Constraints

- Patch-stream (`v.2.1.2`); not Stage 5.
- CLI surface / output of `info --version` stays the same (`[cellpy] version: …`).
- Heavier commands (`setup`, `info --check`, convert, run, …) keep working; they may still pay full import cost when invoked.
- No broad scientific-import redesign beyond what the light CLI path needs.
- Prefer stdlib / existing patterns; no new dependencies.

### Prior art

- `cellpy.cli` → `cellpy.cli_api` (Typer adapters; library-first extract #568/#651).
- Lazy config: `cellpy.config` PEP 562 / no import-time I/O (conventions + #453) — config itself is light once package is loaded; package `__init__` is still eager.
- Tests: `tests/test_cellpy_cmd.py::test_info_version` (CliRunner); `tests/test_cli_api.py`.
- Toolbox: no import-timing helper in `00-tools/` (profile ad hoc / document in issue comment).
- Graph: not required for this scoped CLI import change.

## Approach

**Root cause (confirmed):** entry point `cellpy.cli:cli` imports `cli_api` at module load; `cli_api` does `import cellpy` (+ config / OtherPath / prmreader / …). `cellpy/__init__.py` eagerly imports readers/cellreader/…. Warm cost ~1.6 s for `import cellpy` alone in the uv env; cold conda amplifies DLL/cache cost to minutes. Second run ~5 s matches “full stack, warm cache.”

**Strategy — light path for version (and cheap CLI bootstrap):**

1. **Profile (document):** record warm timings for `typer`, `import cellpy`, `import cellpy.cli`, and post-fix `info --version` wall time; post short numbers on #837.
2. **`cellpy/cli.py`:** remove module-level `from cellpy import cli_api`; import `cli_api` inside each command body (and `if __name__`). Registering Typer commands then only needs `typer` — so `cellpy --help` stays light.
3. **`cellpy/cli_api.py`:**
   - Drop eager `import cellpy` and other heavy top-level imports (`config`, `OtherPath`, `prmreader`, `internal_settings`, …).
   - Resolve `VERSION` without package `__init__` — prefer `importlib.metadata.version("cellpy")` (works for conda/PyPI/editable; fallback to loading `cellpy._version` via `importlib.util` only if metadata missing in odd layouts).
   - Lazy-import heavy modules inside the functions that need them (`setup_config`, `show_info` non-version branches, convert, run, …).
   - `show_info(version=True)` must only need VERSION + echo.
4. **Package `__init__.py`:** **required** — console entry `cellpy.cli:cli` always executes package init first. Make sanctioned top-level symbols lazy via PEP 562 `__getattr__` (keep `__version__` + NullHandler eager).
5. **Regression guard:** test that after `CliRunner.invoke(..., ["info", "--version"])` (or after importing `cellpy.cli` alone), heavy modules such as `cellpy.readers.cellreader` are **not** in `sys.modules`. Keep existing `test_info_version` behavior assertion.
6. **Cold-run note:** if residual cold delay remains environmental (AV/DLL), mention briefly in PR/`HISTORY` that first process after install can still be slower; the regression we fix is “must load full stack for `--version`.”

## Files to touch

| Path | Change |
|---|---|
| [`cellpy/cli.py`](../../../cellpy/cli.py) | Per-command lazy `cli_api` import |
| [`cellpy/cli_api.py`](../../../cellpy/cli_api.py) | Light module import graph; metadata VERSION; lazy heavy deps |
| [`tests/test_cellpy_cmd.py`](../../../tests/test_cellpy_cmd.py) | Import-graph regression for `--version` |
| `.issueflows/01-current-issues/issue837_status.md` | Log profile numbers + Done checkbox at close |

Optional: short `HISTORY.md` line at `/iflow-close`.

## Test strategy

- `uv run pytest tests/test_cellpy_cmd.py tests/test_cli_api.py -q` (or conda `cellpy_dev_313` if preferred locally).
- Manual: warm `uv run cellpy info --version` timing before/after; if conda env available, spot-check there too.
- No new deps; no full-suite gate for this change beyond essential CLI tests + existing suite at close.

## Open questions

1. **Package `__init__` lazy-load in this PR?** **Resolved:** yes — entry point forces it.
2. **VERSION source:** **Resolved:** keep `cellpy._version` (already `importlib.metadata`).
