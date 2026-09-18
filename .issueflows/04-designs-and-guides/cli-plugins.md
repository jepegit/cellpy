# CLI plugins (`cellpy.cli_plugins`)

**Issue:** #1055 · **Epic:** #1042

## Context

Third-party packages (cellpy-connectors first) need to add commands under the
`cellpy` CLI. The live app is `typer.Typer` (`cellpy/cli.py`). This note is the
shared contract for Stage 2 (mount) and cellpy-connectors#3 (what to declare).

## Decision

| Rule | Value |
| --- | --- |
| Entry-point group | `cellpy.cli_plugins` |
| Mount name | the **entry-point name** (not the object's own Click/Typer name) |
| Accepted objects | `typer.Typer`, `click.Group`, `click.Command` |
| Anything else | warning (name + distribution) + skip |
| Import / `load()` failure | warning (name + distribution + exception) + skip |
| Duplicate names | first wins; later entries warn + skip |
| When the group is scanned | first `discover()`, not `import cellpy` or `import cellpy.cli_plugins` |
| When `EntryPoint.load()` runs | `load_plugin` / `load_all` only |
| Live CLI mount | Stage 2 — not this module |

Do **not** import `cellpy.cli_plugins` from `cellpy/__init__.py` (keeps
`import cellpy` off typer/click plugin scan; [cli-light-startup.md](cli-light-startup.md)).

Example declaration:

```toml
[project.entry-points."cellpy.cli_plugins"]
connectors = "cellpy_connectors.cli:app"
```

## Alternatives

- Eager `load()` inside `discover()` — rejected; `--help` listing (Stage 2)
  must be able to show names without importing plugin modules.
- Use the object's own command name — rejected; connectors need a stable
  top-level slot (`connectors = ...`) regardless of `Typer.info.name`.
