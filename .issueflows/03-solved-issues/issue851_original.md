# Issue #851: cellpy info / edit config / info --check still point at the legacy .conf after migration

Source: https://github.com/jepegit/cellpy/issues/851

## Original issue text

## Problem / context

After `cellpy setup migrate` writes `cellpy.toml`, the config *loader* correctly prefers it — `load_config` only falls back to the legacy YAML when no TOML was loaded (`cellpy/config/loader.py:203-213`). But the CLI still reports and edits the old file:

```
❯ cellpy setup migrate
[cellpy] (setup migrate) source: C:\Users\jepe\.cellpy_prms_jepe.conf
[cellpy] (setup migrate) target: C:\Users\jepe\AppData\Local\cellpy\cellpy\cellpy.toml
[cellpy] (setup migrate) done - the old file is kept untouched.

❯ cellpy info
[cellpy] version: 2.1.1.post8.dev1+fad801ac
[cellpy] -> C:\Users\jepe\.cellpy_prms_jepe.conf     # ← stale, nothing reads this
```

Root cause: `_configloc()` (`cellpy/cli_api.py:1276`) calls `prmreader.get_user_dir_and_dst()`, which composes `~/.cellpy_prms_<user>.conf` unconditionally and never consults `cellpy.config.loader.user_config_path()`.

Three surfaces are affected, and two are worse than a wrong printout:

- **`cellpy info` / `cellpy info --configloc`** — names a file that no longer has any effect.
- **`cellpy edit config`** (`cli_api.py:1876`) — opens the stale `.conf`, so the user edits a file that is silently ignored. Most damaging: the edit appears to succeed and changes nothing.
- **`cellpy info --check`** (`_check_config_file`, `cli_api.py:999-1011`) — validates the stale YAML via `_read_prm_file_without_updating`, so it checks paths the runtime is not using.

`cellpy info --show-config` is already correct — it goes through `config.get_config()` with provenance (`_dump_config_resolved`, `cli_api.py:1223`).

## Spec

- Resolve the *active* config file with the same precedence as `load_config`: user `cellpy.toml` → legacy `.conf` → none. Put this in one helper (e.g. `cellpy.config.loader.active_config_file()`) so the CLI and the loader cannot drift apart again.
- `_configloc()` reports that file. When a legacy `.conf` exists but is shadowed by a TOML, say so explicitly, e.g.
  `[cellpy] (legacy C:\Users\jepe\.cellpy_prms_jepe.conf is ignored — cellpy.toml takes precedence)`.
- `cellpy edit config` opens the active file.
- `_check_config_file` validates the active file; for a TOML, check it through the config models rather than the YAML reader.

## Acceptance criteria

- With a `cellpy.toml` present, `cellpy info` prints the TOML path and mentions the shadowed legacy file when one exists.
- With no TOML, output is unchanged from today (legacy path).
- `cellpy edit config` opens the TOML when it exists.
- `cellpy info --check` passes/fails based on the TOML's paths, not the legacy YAML's.
- Tests cover all three states: TOML only, legacy only, both (TOML wins + shadow notice). Marked `essential` — this is the "which config am I actually using" question and it must stay honest.

## Out of scope

- Changing precedence itself, or deprecating/deleting the legacy `.conf`.
- `cellpy setup migrate` behaviour (it works correctly).
- Project-level `cellpy.toml` discovery (`find_project_config_file`) — worth a follow-up, since a project file also outranks the user file and `info` will not mention it either.
