# Command-line reference

Installing cellpy also installs a `cellpy` command. It is the shortest route to
setting things up, checking that they work, and starting a batch experiment
from a template — no Python needed.

```console
cellpy --help
```

| Command | What it is for |
| --- | --- |
| [`setup`](#cellpy-setup) | create folders and `cellpy.toml` |
| [`info`](#cellpy-info) | version, paths, and health checks |
| [`edit`](#cellpy-edit) | open the config, database or environment file |
| [`new`](#cellpy-new) | start a batch experiment from a template |
| [`run`](#cellpy-run) | run a batch job without opening a notebook |
| [`serve`](#cellpy-serve) | start Jupyter |
| [`pull`](#cellpy-pull) | download the examples or test data |
| [`convert`](#cellpy-convert) | upgrade an old cellpy file |
| [`mcp`](#cellpy-mcp) | run cellpy as an MCP server |

Three options work everywhere:

| Option | Effect |
| --- | --- |
| `-q`, `--quiet` | only problems and what you asked for |
| `--verbose` | extra detail |
| `--no-color` | plain output (`NO_COLOR` is honoured too) |

---

## `cellpy setup`

Creates the `cellpy_data` folder tree and writes `cellpy.toml`. Run it once
after installing.

```console
cellpy setup
```

| Option | Effect |
| --- | --- |
| `-i`, `--interactive` | ask about each folder instead of using defaults |
| `-s`, `--silent` | ask nothing |
| `-d`, `--root-dir <path>` | put the folders under this directory instead of your home directory |
| `-n`, `--folder-name <path>` | name of the folder to create |
| `-nr`, `--not-relative` | with `--root-dir`, place it at the root rather than under your home directory |
| `-r`, `--reset` | ignore your current config when suggesting defaults |
| `-dr`, `--dry-run` | print what would happen, change nothing |
| `--deps` | report which optional extras are missing |
| `-c`, `--check` | run the sanity checks afterwards |

`cellpy setup` writes (or refreshes) `cellpy.toml` only. It does not create a
legacy `.cellpy_prms_*.conf`.

### `cellpy setup migrate`

Converts a legacy `.conf` file to `cellpy.toml`:

```console
cellpy setup migrate --dry-run
cellpy setup migrate
```

| Option | Effect |
| --- | --- |
| `--src <path>` | the legacy file (auto-detected when not given) |
| `--dst <path>` | where to write the TOML (defaults to the user-config location) |
| `-dr`, `--dry-run` | print only |
| `-f`, `--force` | overwrite an existing `cellpy.toml` |

The old file is left untouched; the TOML wins once it exists.

---

## `cellpy info`

```console
cellpy info --version
cellpy info --check
```

| Option | Shows |
| --- | --- |
| `-v`, `--version` | the installed version |
| `-c`, `--check` | import, Arbin-driver and configuration checks |
| `-l`, `--configloc` | full path to the config file |
| `-C`, `--config` | the resolved settings, with where each came from |
| `-p`, `--params` | a dump in the legacy parameter style |

`--check` is the one to run when something is not working, and the one to paste
into a bug report:

```text
cellpy 2.1.4 - checking your setup

  ✓ imports             cellpy, log, cellreader
  ✓ arbin .res support  Microsoft Access Driver (*.mdb, *.accdb)
  ✓ configuration       .../cellpy.toml
      cellpydatadir     .../cellpy_data/cellpyfiles
      rawdatadir        .../cellpy_data/raw
      db_path           .../cellpy_data/db
      db_filename       cellpy_db.xlsx
      ...

  3 of 3 checks passed
```

Not every check has to pass — they cover optional features. A failing Arbin
check only matters if you read `.res` files.

`--config` is the fastest way to find `filelogdir` when you are hunting for
`cellpy_debug.log`.

---

## `cellpy edit`

Opens one of your cellpy files in an editor.

```console
cellpy edit           # the config file
cellpy edit config
cellpy edit db        # the batch database spreadsheet
cellpy edit env       # the environment file
```

| Option | Effect |
| --- | --- |
| `-e`, `--default-editor <str>` | use this editor, e.g. `cellpy edit env -e notepad.exe` |
| `-d`, `--debug` / `-s`, `--silent` | more or less output |

`cellpy edit db` is a convenient shortcut once you have a
[cellpy database](../guides/batch_database.md) configured — no hunting for the
spreadsheet.

---

## `cellpy new`

Creates a project folder with notebooks already wired to your database, from a
[cookiecutter](https://cookiecutter.readthedocs.io/) template.

```console
cellpy new --list
cellpy new -p my_project -e paper01
```

```text
batch templates

      default           standard

  · registered (on github)
      standard          https://github.com/jepegit/cellpy_cookies.git
      ife               https://github.com/jepegit/cellpy_cookies.git
      single            https://github.com/jepegit/cellpy_cookies.git
  · local (.../cellpy_data/templates)
```

| Option | Effect |
| --- | --- |
| `-l`, `--list` | list templates and exit |
| `-t`, `--template <str>` | which template to use |
| `-p`, `--project <str>` | project name (the sub-directory) |
| `-e`, `--experiment <str>` | experiment name (the batch lookup value) |
| `-d`, `--directory <str>` | create it somewhere other than the default |
| `-u`, `--local-user-template` | use a template from your local templates folder |
| `-s`, `--serve` | start Jupyter afterwards |
| `-j`, `--lab` | use Jupyter Lab rather than Notebook when serving |
| `-r`, `--run` | execute the template notebooks with PaperMill |
| `--jupyter-executable <str>` | Jupyter to use, if it is in another environment |

Fetching a registered template needs git and network access.

---

## `cellpy run`

Runs a batch job from the shell — useful for a long re-processing job, or from
a scheduler.

```console
cellpy run --list
cellpy run -j cellpy_batch_paper01.json
```

| Option | Effect |
| --- | --- |
| `-l`, `--list` | list the batch (journal) files it can see |
| `-j`, `--journal` | run the batch described by a journal file |
| `-k`, `--key` | run the batch with this name |
| `-f`, `--folder` | run every batch job in a folder |
| `-p`, `--cellpy-project` | run a project folder's notebooks with PaperMill |
| `--raw` / `--cellpyfile` | force loading from raw files / from cellpy files |
| `--minimal` | minimal processing |
| `--nom-cap <float>` | nominal capacity, for rates |
| `--batch_col <str>` / `--project <str>` | batch column and project, when running from the database |
| `-d`, `--debug` / `-s`, `--silent` | more or less output |

!!! note "Windows paths"
    `--cellpy-project` interprets the name as a Python string, so a single
    backslash is an escape character. Use `/` or `\\`.

---

## `cellpy serve`

Starts a Jupyter server. cellpy is a library, not a web service — this is the
only thing it "serves".

```console
cellpy serve --lab
```

| Option | Effect |
| --- | --- |
| `-l`, `--lab` | Jupyter Lab instead of Notebook |
| `-d`, `--directory <str>` | start in this directory |
| `-e`, `--executable <str>` | Jupyter from another environment |

---

## `cellpy pull`

Downloads the example notebooks or the test data from GitHub. Needs git.

```console
cellpy pull --examples
cellpy pull --tests
cellpy pull --clone -d some_dir
```

| Option | Effect |
| --- | --- |
| `-e`, `--examples` | the example notebooks and their data |
| `-t`, `--tests` | the test files |
| `-c`, `--clone` | the whole repository |
| `-d`, `--directory <str>` | download into this directory |
| `-p`, `--password <str>` | repository password, if needed |

---

## `cellpy convert`

Upgrades a cellpy file written by an older version.

```console
cellpy convert old_cell.h5 new_cell.cellpy
```

| Argument / option | Meaning |
| --- | --- |
| `OLD_H5` (required) | the file to convert |
| `NEW_H5` | where to write it |
| `--to <str>` | `v9` (zip-of-parquet `.cellpy`) or `v8` (legacy HDF5). Inferred from the new file's suffix, otherwise `v9` |

Reading the old HDF5 layout needs the HDF5 stack:
`pip install "cellpy[legacy-files]"`. Converting once means you do not need it
again.

---

## `cellpy mcp`

Runs cellpy as an [MCP](https://modelcontextprotocol.io/) server, so a chat
client can load and inspect cell data.

```console
cellpy mcp status
cellpy mcp install
cellpy mcp serve
```

| Sub-command | Effect |
| --- | --- |
| `status` | whether the server is installed, and what it would serve |
| `install` | register the server with a chat client |
| `serve` | run the server over stdio (clients normally do this themselves) |

The server itself lives in a separate package:

```console
python -m pip install cellpy-mcp
```

---

## See also

- [Check your installation](../getting_started/checkup.md) — the short version
  of `cellpy info`
- [Setup and configuration](../getting_started/configuration.md) — what
  `cellpy setup` writes, and how to change it afterwards
- [Configuration reference](../getting_started/configuration_reference.md) —
  every setting
- [Troubleshooting](../troubleshooting.md) — including
  `cellpy: command not found`
