# Issue #851 — plan: CLI must report the *active* config file

Source: https://github.com/jepegit/cellpy/issues/851
Milestone: v.2.1.2 · Labels: bug, v2

## Goal

`cellpy info`, `cellpy edit config`, and `cellpy info --check` must all act on the
config file the loader actually uses (`cellpy.toml` when present, else the legacy
`.cellpy_prms_*.conf`), and say when a legacy file is being shadowed.

## Constraints

- **Precedence is not up for debate** — `load_config` already does it right
  ([`config/loader.py:203-213`](../../cellpy/config/loader.py)): user TOML wins,
  legacy YAML only when no TOML loaded. This issue changes *reporting*, not
  resolution.
- **One code path, or it will drift again.** The bug exists because `_configloc`
  re-derives a filename (`prmreader.get_user_dir_and_dst()` →
  `~/.cellpy_prms_<user>.conf`) instead of asking the loader. A second parallel
  "which file?" implementation would rot the same way, so `load_config` itself
  must consume the new helper rather than merely agreeing with it.
- **Legacy-only setups must be unchanged** — no TOML present ⇒ byte-identical
  output to today.
- Do not touch `cellpy setup migrate`, and do not deprecate or delete the legacy
  `.conf` (it keeps working through the v2.0 deprecation window).
- `cellpy info --show-config` is already correct; leave it alone.

### Prior art

- `.issueflows/00-tools/README.md` — nothing config-related; no reuse.
- `config/loader.py`: `user_config_path()`, `find_project_config_file()`,
  `CONFIG_FILENAME = "cellpy.toml"` — the pieces the helper composes.
- `config/legacy.py`: `find_legacy_yaml_file()` — legacy discovery, already the
  function `load_config` calls. Reuse as-is.
- `cli_api.py:1223 _dump_config_resolved()` — the one surface that already reads
  through `config.get_config()` + `sources()`. It is the model to follow.
- `cli_api.py:1285 _envloc()` — same shape for the env file; out of scope, but
  worth a glance if it turns out to have the same defect.
- Docs already document the commands in
  `docs/getting_started/configuration.md:50-57`.

## Approach

1. **`config/loader.py` — one resolver.** Add a frozen dataclass and a function:

   ```python
   @dataclass(frozen=True)
   class ActiveConfigFile:
       path: Path | None            # what load_config uses for the user layer
       kind: str                    # "toml" | "legacy" | "none"
       shadowed_legacy: Path | None # legacy file present but outranked

   def active_config_file(options: LoadOptions | None = None) -> ActiveConfigFile:
   ```

   TOML at `user_config_path()` (or `opts.user_config_file`) wins; else the
   legacy file from `find_legacy_yaml_file()` (or `opts.legacy_yaml_file`); else
   `kind="none"`. `shadowed_legacy` is set only when a legacy file exists *and* a
   TOML won.

2. **Rewire `load_config` through it.** Its user-layer branch calls
   `active_config_file(opts)` and switches on `kind`, so the CLI and the loader
   cannot disagree by construction. Merge/secret handling per layer stays exactly
   as it is today (`_reject_secrets_from_file` for TOML,
   `_drop_legacy_secrets` for YAML).

3. **`_configloc()`** reports `result.path`, and adds one line when
   `shadowed_legacy` is set:

   ```
   [cellpy] -> C:\...\AppData\Local\cellpy\cellpy\cellpy.toml
   [cellpy] (legacy C:\Users\jepe\.cellpy_prms_jepe.conf is ignored - cellpy.toml takes precedence)
   ```

   `kind="none"` keeps today's "File does not exist!" + `None` return, so
   callers that branch on `None` are unaffected.

4. **`cellpy edit config`** needs no change of its own — it opens whatever
   `_configloc()` returns (`cli_api.py:1876`). This also fixes a worse case than
   the issue described: on a **TOML-only** install (fresh `cellpy setup` with no
   legacy file) `_configloc()` returns `None` today, so `cellpy edit config`
   currently answers "could not find the config file" and opens nothing at all.

5. **`_check_config_file()`** stops parsing the raw legacy YAML
   (`prmreader._read_prm_file_without_updating`, which cannot read TOML) and
   checks the **resolved** `config.paths` instead, printing the active file for
   context. One code path covers both formats, and it validates what the runtime
   will really use. The per-path listing, the `OTHERPATHS` skip, the
   `db_filename` check, and the missing-count return value all stay.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/config/loader.py` | add `ActiveConfigFile` + `active_config_file()`; `load_config` user layer routes through it |
| `cellpy/cli_api.py` | `_configloc()` reports the active file + shadow notice; `_check_config_file()` validates resolved `config.paths` |
| `tests/test_config.py` | new: helper precedence for the three states (TOML only / legacy only / both) |
| `tests/test_cellpy_cmd.py` | `test_info_configloc` currently asserts `"conf" in result.output`, which a `.toml` path fails — make it format-agnostic; add a shadow-notice case |
| `tests/test_cli_api.py` | extend `test_config_path_returns_a_path_or_none` for the TOML case |
| `docs/getting_started/configuration.md` | note that `--configloc` names the winning file and flags a shadowed legacy one |

## Test strategy

Runner: `uv run pytest` (the documented conda env `cellpy_dev_313` currently has
a broken `pyarrow` DLL — see #845 status notes). Merge gate:
`uv run pytest -m essential`. Targeted:
`uv run pytest tests/test_config.py tests/test_cellpy_cmd.py tests/test_cli_api.py -m ""`.

Drive the three states through `LoadOptions(user_config_file=..., legacy_yaml_file=...)`
with `tmp_path`, so nothing depends on the developer's real `$HOME`:

1. TOML only → `kind == "toml"`, `shadowed_legacy is None`.
2. Legacy only → `kind == "legacy"`, path is the `.conf`.
3. Both → `kind == "toml"`, `shadowed_legacy` is the `.conf`, and `cellpy info`
   prints the notice.
4. Neither → `kind == "none"`, `_configloc()` returns `None`.
5. Anti-drift: with both files present, assert the layer `load_config` recorded
   comes from the TOML (a value set only there wins), proving helper and loader
   agree.

Mark 1–3 `essential`: "which config am I using" must not silently regress.

## Decisions (confirmed 2026-08-09)

1. **`_check_config_file` validates the resolved `config.paths`**, not the active
   file's own contents. Format-agnostic and it checks what the runtime will really
   use. Accepted cost: env-var and project-file layers are folded in, so `--check`
   no longer validates the user file in isolation.
   Rejected: per-format parsing of the active file, which keeps the check
   file-local but reintroduces two parsers to keep in step.
2. **`_envloc()`** — investigate during build; fix here only if it is literally the
   same self-derived-path defect. Otherwise file a follow-up.
3. Shadow-notice wording as drafted above.
