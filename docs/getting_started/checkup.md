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
| `edit` | Open the config, database or environment file |
| `new` | Start a batch experiment from a template |
| `run` | Run a batch job from the shell |
| `serve` | Start Jupyter |
| `pull` | Download examples or tests (needs git) |
| `convert` | Upgrade a legacy cellpy file |
| `mcp` | Run cellpy as an MCP server |

Help for a subcommand:

```console
cellpy info --help
```

Every sub-command and option is listed in the
[command-line reference](../reference/cli.md). Note that
`cellpy setup migrate` (legacy `.conf` → `cellpy.toml`) is a sub-command of
`setup`, not a top-level command.

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

## Still not working?

[Troubleshooting](../troubleshooting.md) is indexed by symptom —
error messages, files that will not load, and numbers that look wrong.
