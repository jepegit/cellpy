# Setup and configuration

To get the most out of cellpy, set up your folders and a config file once.
Runtime settings live in **`cellpy.config`** and are stored as **`cellpy.toml`**
(not the old YAML `.conf`).

## Quick setup

Interactive setup prompts for preferred locations:

```console
cellpy setup -i
```

Silent / default layout:

```console
cellpy setup --silent
```

Optional root folder for the directory tree:

```console
cellpy setup -i -d /Users/you/cellpy_data
```

`cellpy setup` writes (or refreshes) a user **`cellpy.toml`**, tries to create
the usual directory layout, and creates a `.env_cellpy` file for secrets /
remote credentials (edit that file before using SSH remotes).

Typical directories:

```text
batchfiles/
cellpyfiles/
db/
examples/
instruments/
logs/
notebooks/
out/
raw/
templates/
```

!!! tip
    Re-run setup after upgrading cellpy if paths or defaults changed.

Where is my config?

```console
cellpy info --configloc
cellpy info --config
```

`--configloc` / `-l` prints the path; `--config` / `-C` dumps resolved values
with provenance (which layer each setting came from).

`--configloc` names the file cellpy actually reads. If you migrated from cellpy 1
and kept the old `.cellpy_prms_<user>.conf`, it says so explicitly — the legacy
file is still on disk but no longer has any effect:

```text
[cellpy] -> C:\Users\you\AppData\Local\cellpy\cellpy\cellpy.toml
[cellpy] (legacy C:\Users\you\.cellpy_prms_you.conf is ignored - cellpy.toml takes precedence)
```

When a **project** `cellpy.toml` is found by walking up from the current
directory, `--configloc` names it too. That file is merged after the user file
and wins on conflicts (`cellpy edit config` still opens the user file):

```text
[cellpy] -> C:\Users\you\AppData\Local\cellpy\cellpy\cellpy.toml
[cellpy] (project C:\work\proj\cellpy.toml also applies and takes precedence)
```

## Configuration layers

Settings resolve later-over-earlier:

**defaults → user `cellpy.toml` → project `cellpy.toml` → environment /
`.env` → runtime overrides**

Ask in Python:

```python
import cellpy.config

print(cellpy.config.sources())
```

Environment variables use `CELLPY_<SECTION>__<FIELD>` (two underscores), e.g.
`CELLPY_READER__AUTO_DIRS=0`.

Full key list: [Configuration settings](configuration_reference.md).

## Example `cellpy.toml`

Paths are the part most people edit. A short example:

```toml
[paths]
outdatadir = "/home/you/cellpy_data/out"
rawdatadir = "/home/you/lab/raw"
cellpydatadir = "/home/you/cellpy_data/cellpyfiles"
db_path = "/home/you/cellpy_data/db"
filelogdir = "/home/you/cellpy_data/logs"
db_filename = "cellpy_db.xlsx"
env_file = "/home/you/.env_cellpy"

[reader]
cycle_mode = "anode"
sep = ";"
```

`rawdatadir` (and optionally `cellpydatadir`) may be a remote URI — see
[Work with remote files](remote_paths.md).

## Runtime overrides

`import cellpy` does **not** load config by itself; first access / setup does.
Prefer the new API:

```python
import cellpy.config as config

config.reader.cycle_mode = "cathode"
config.reader.sep = ","
config.paths.outdatadir = "experiment01/processed_data"
```

Legacy `from cellpy.parameters import prms` still forwards with a
`DeprecationWarning` — see [Coming from cellpy 1.x](migration_v1_to_v2.md).

## Database file

cellpy can use a simple Excel “database” for cell metadata (name, mass,
type, …) when running batch workflows. The first row is headers, the second
row types, then one row per cell. A sample file ships with the
[batch tutorial](../examples/batch_utility/cellpy_batch_processing.md).

## Credentials

Passwords, SSH keys, and remote host details are **not** stored in
`cellpy.toml`. They come from the environment or your `.env` / `.env_cellpy`
file:

| Setting | Environment variable |
| --- | --- |
| password | `CELLPY_PASSWORD` |
| ssh key file | `CELLPY_KEY_FILENAME` (required for reliable remotes; see [Remote paths](remote_paths.md) / #687) |
| host | `CELLPY_HOST` |
| user | `CELLPY_USER` |

A `[secrets]` section in `cellpy.toml` is an error, not a silent override.
Passwords are held as `SecretStr` so they do not appear in reprs, logs, or
config dumps.

## Legacy `.conf` files

Older installs used a YAML file named `.cellpy_prms_USERNAME.conf`. cellpy 2.x
reads and migrates that format:

```console
cellpy migrate
```

or let `cellpy setup` write a fresh TOML. Details:
[Coming from cellpy 1.x](migration_v1_to_v2.md) (configuration section).
