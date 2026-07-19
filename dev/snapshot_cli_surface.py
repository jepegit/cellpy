"""Snapshot the cellpy command-line surface (#569).

The snapshot is the contract ``tests/test_cli_surface.py`` checks against, so
that changing the CLI *framework* cannot quietly change the CLI. Regenerate it
only when a surface change is intended, and in the same commit as the change,
so review sees it:

```shell
uv run python dev/snapshot_cli_surface.py
```
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = REPO_ROOT / "tests" / "data" / "cli_surface.json"


def _describe(command: Any, name: str) -> dict:
    """Describe one command, without asking *which* Click it is built on.

    Deliberately duck-typed. The first version of this script used
    ``isinstance(param, click.Argument)`` and ``isinstance(command,
    click.Group)`` against the installed ``click`` — which quietly stops
    working under Typer, because Typer vendors its own Click as
    ``typer._click``. Both checks returned False, so every argument would have
    been recorded as an option and every group as a leaf command: the snapshot
    would have "passed" the framework change by describing the CLI wrongly.

    ``param_type_name`` is Click's own class attribute (``"argument"`` /
    ``"option"``), and a group is a thing with ``.commands``. Both hold for
    either Click.
    """
    entry: dict[str, Any] = {"name": name, "params": []}
    for param in command.params:
        entry["params"].append(
            {
                "kind": getattr(param, "param_type_name", "option"),
                "opts": sorted(param.opts + param.secondary_opts),
                "is_flag": bool(getattr(param, "is_flag", False)),
                "required": bool(getattr(param, "required", False)),
                "multiple": bool(getattr(param, "multiple", False)),
            }
        )
    entry["params"].sort(key=lambda item: (item["kind"], item["opts"]))
    if hasattr(command, "commands"):
        entry["subcommands"] = sorted(command.commands)
    return entry


def build_surface() -> dict:
    """Describe the live CLI.

    Typer builds on Click, so a Typer app is inspected the same way once it is
    converted to its underlying Click command — which is what keeps this
    snapshot meaningful across the framework change.
    """
    from cellpy.cli import cli

    command = cli
    if not hasattr(command, "commands"):
        import typer.main

        command = typer.main.get_command(command)

    return {
        "commands": [
            _describe(sub, name) for name, sub in sorted(command.commands.items())
        ]
    }


def main() -> None:
    surface = build_surface()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(surface, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote {SNAPSHOT_PATH}")
    print("commands:", [c["name"] for c in surface["commands"]])


if __name__ == "__main__":
    main()
