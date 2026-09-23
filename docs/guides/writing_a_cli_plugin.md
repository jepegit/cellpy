# Writing a CLI plugin

A third-party package can add commands under `cellpy` without changing this
repo. Declare an entry point; cellpy finds it the same way it finds instrument
loaders.

```toml
# your package's pyproject.toml
[project.entry-points."cellpy.cli_plugins"]
connectors = "cellpy_connectors.cli:app"
```

The **entry-point name** is the top-level command (`cellpy connectors …`).
cellpy does not use the object's own Click/Typer name for that slot.

## What you can register

The object must be one of:

- `typer.Typer`
- `click.Group`
- `click.Command`

Anything else is logged (entry name + distribution) and skipped.

## Keep the import light

`cellpy --help` lists your command **without importing your module**. The
module loads when someone runs that command (or its own `--help`). Keep the
entry-point target import-cheap: do not pull the reader stack or a heavy HTTP
client at module import if you can defer it.

A plugin that raises on import is skipped; `cellpy --help` still exits 0.

## Collisions

If your entry-point name is a built-in (`convert`, `edit`, `info`, `mcp`,
`new`, `pull`, `run`, `serve`, `setup`), cellpy keeps the built-in and warns.
Two plugins claiming the same name: first wins.

## Related

- Instrument loaders use `[project.entry-points."cellpy.loaders"]` —
  [Writing an instrument loader](writing_a_loader_plugin.md).
- Contract: `.issueflows/04-designs-and-guides/cli-plugins.md` in the repo.
