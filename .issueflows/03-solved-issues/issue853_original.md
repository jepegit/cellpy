# Issue #853: cellpy info --configloc does not mention a project-level cellpy.toml that overrides the user file

Source: https://github.com/jepegit/cellpy/issues/853

## Original issue text

Follow-up to #851 / #852, which was deliberately scoped to the *user-level* config file.

## Problem / context

`load_config` merges a **project** `cellpy.toml` after the user file, so it wins
(`cellpy/config/loader.py`, `find_project_config_file()` walks up from the cwd).
`active_config_file()` — added in #852 and used by `cellpy info --configloc` and
`cellpy edit config` — only resolves the user-level file (`cellpy.toml` vs. legacy
`.cellpy_prms_*.conf`) and says nothing about a project file.

So a user with a `cellpy.toml` in their project directory is told their config lives
under e.g. `AppData\Local\cellpy\cellpy\cellpy.toml`, while a *different* file is
actually changing the values they are asking about. Same class of dishonesty as #851
(the command names a file that is not the whole truth), just one layer up.

`cellpy info --config` / `-C` already exposes it through per-field provenance
(`SourceLayer.PROJECT_FILE`), so the information is reachable — it is just missing
from the command whose entire job is answering "where is my config?".

## Spec

- `cellpy info --configloc` reports the project file when one is found, alongside the
  user file, making the override direction clear. Something like:

  ```
  [cellpy] -> C:\Users\you\AppData\Local\cellpy\cellpy\cellpy.toml
  [cellpy] (project C:\work\proj\cellpy.toml also applies and takes precedence)
  ```

- Reuse the existing discovery (`find_project_config_file`) and honour
  `LoadOptions.project_config_file` / `skip_files`, exactly as `load_config` does —
  do not add a second discovery implementation (that is the mistake #851 was about).
- Keep `load_config` behaviour and layer precedence unchanged; this is reporting only.
- Note the existing `project_file != user_file_path` guard in `load_config` — do not
  report the same path twice.

### `cellpy edit config`

Open question for whoever picks this up: `edit config` goes through the same helper,
and with a project file present it is genuinely ambiguous which file the user means.
Suggested: keep opening the **user** file (today's behaviour, least surprising) and
leave `--configloc` as the place that discloses the project file. Worth a line in the
docs either way.

## Acceptance criteria

- With a project `cellpy.toml` on the path, `cellpy info --configloc` names it and
  makes clear it outranks the user file.
- With no project file, output is unchanged from #852.
- The user-level TOML-vs-legacy reporting from #851 still behaves as it does now,
  including the shadowed-legacy notice.
- Tests cover: project file only, project + user file, and no project file. Extend the
  `active_config_file` tests in `tests/test_config.py` rather than starting a new file.
- `docs/getting_started/configuration.md` mentions it in the "Where is my config?"
  section, next to the legacy-shadow note.

## Out of scope

- Changing layer precedence.
- Making `cellpy edit config` open the project file (see the open question above).
