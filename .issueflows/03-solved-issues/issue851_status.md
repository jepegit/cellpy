# Issue #851 — status

- [x] Done

Branch: `851-configloc-active-file` · Issue: https://github.com/jepegit/cellpy/issues/851

## What was done

**One resolver, consumed by both sides.** `cellpy/config/loader.py` gained
`ActiveConfigFile` (frozen dataclass: `path`, `kind`, `shadowed_legacy`) and
`active_config_file(options)`. `load_config` no longer decides the user layer
itself — it calls the helper and switches on `kind`, so a reporting command and
the loader cannot disagree about which file wins. That was the actual defect:
`_configloc()` re-derived `~/.cellpy_prms_<user>.conf` via
`prmreader.get_user_dir_and_dst()` and never asked the loader.

**`_configloc()`** reports the winning file and names a shadowed legacy one:

```
[cellpy] -> C:\Users\jepe\AppData\Local\cellpy\cellpy\cellpy.toml
[cellpy] (legacy C:\Users\jepe\.cellpy_prms_jepe.conf is ignored - cellpy.toml takes precedence)
```

With no config at all it keeps the old "File does not exist!" + `None` return, so
callers that branch on `None` are unaffected.

**`cellpy edit config`** needed no change of its own (it opens whatever
`_configloc()` returns). Verified: `cli_api.config_path()` now returns the TOML.
This also fixes a case worse than the one reported — on a **TOML-only** install
`_configloc()` used to return `None`, so `cellpy edit config` answered "could not
find the config file" and opened nothing at all.

**`_check_config_file()`** stopped parsing the raw legacy YAML
(`prmreader._read_prm_file_without_updating`, which cannot read TOML) and now
checks the resolved `config.paths`. Per-path listing, the `OTHERPATHS` skip, the
`db_filename` check and the return value are unchanged.

**`_envloc()` was investigated and left alone** — it reads
`config.paths.env_file` through the resolved config
(`prmreader.get_env_file_name`), so it never had the self-derived-path defect. No
follow-up needed.

Exported `active_config_file` / `ActiveConfigFile` from `cellpy.config`.

## Verified on the reporting machine

The setup that produced the bug report (migrated: both files on disk):

```
[cellpy] -> C:\Users\jepe\AppData\Local\cellpy\cellpy\cellpy.toml
[cellpy] (legacy C:\Users\jepe\.cellpy_prms_jepe.conf is ignored - cellpy.toml takes precedence)
```

`cellpy info --check` now reads the TOML's paths — "Succeeded 3 out of 3 checks."

## Tests

New, in `tests/test_config.py` (three `essential`): TOML wins / legacy-only
fallback / shadowed-legacy flagged / neither file present, plus an anti-drift test
asserting the helper and `load_config` pick the same file when both exist.
In `tests/test_cellpy_cmd.py` (both `essential`): `--configloc` reports the TOML,
and prints the shadow notice.

`tests/test_cellpy_cmd.py::test_info_configloc` asserted `"conf" in result.output`,
which a `cellpy.toml` path fails — made format-agnostic (`"[cellpy] ->"`).

Runner: `uv run pytest` (the documented conda env `cellpy_dev_313` has a broken
`pyarrow` DLL, as noted under #845).

- `uv run pytest -m essential` → **684 passed**, 1 skipped.
- `uv run pytest` (full) → **1532 passed**, 3 failed.
- Those 3 (`test_cell_readers.py::test_search_for_files`,
  `test_filefinder.py::test_search_for_files_with_dirs`,
  `::test_search_for_files_recursive`) are **pre-existing**: re-confirmed failing
  on a stashed clean tree. They depend on the developer's real `rawdatadir`, an
  unreachable `scp://` remote.
- `black`: added code is clean; the files carry pre-existing reformat
  suggestions that were deliberately left untouched to keep the diff small.

## Files touched

- `cellpy/config/loader.py` — `ActiveConfigFile`, `active_config_file()`;
  `load_config` routes its user layer through it
- `cellpy/config/__init__.py` — re-export
- `cellpy/cli_api.py` — `_configloc()`, `_check_config_file()`
- `tests/test_config.py`, `tests/test_cellpy_cmd.py`
- `docs/getting_started/configuration.md` — document the shadow notice
- `HISTORY.md`, `.issueflows/04-designs-and-guides/test-registry.md`

## Remaining work

None for this issue. Merged as PR #852 (squash `7d432004`).

Deliberately out of scope, now tracked as **#853** (`yolo`, milestone v.2.1.2): a
**project-level** `cellpy.toml` (`find_project_config_file`) also outranks the user
file, and `--configloc` still does not mention it. `--config` / `-C` already shows
per-field provenance, so the information is reachable today.
