# Check your installation

Confirm the CLI is on your `PATH` and the install looks healthy.

## Version and sanity check

```console
cellpy info --version
cellpy info --check
```

!!! hint
    Some checks can fail while day-to-day features still work. Fix reported
    issues if you need the full feature set (for example Arbin `.res` drivers
    or mdbtools).

Config path and resolved settings:

```console
cellpy info --configloc
cellpy info --config
```

`-l` is short for `--configloc`; `-C` is short for `--config`. For a dump of
legacy-style parameters, `cellpy info --params` / `-p` is still available.

## Useful commands

```console
cellpy --help
```

Typical subcommands:

| Command | Role |
| --- | --- |
| `setup` | Create / refresh `cellpy.toml` and folders |
| `info` | Version, config location, checks |
| `migrate` | Convert a legacy `.conf` to `cellpy.toml` |
| `pull` | Download examples or tests (needs git) |
| `serve` | Start Jupyter |
| `edit` / `new` / `run` | Config/db editing, batch setup, batch runs |

Help for a subcommand:

```console
cellpy info --help
```

## Upgrade

```console
python -m pip install --upgrade cellpy
```

Or with conda:

```console
conda update -c conda-forge cellpy
```

## Pre-releases

```console
python -m pip install --pre cellpy
```
