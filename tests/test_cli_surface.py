"""The command-line surface is a contract (#569).

Changing the CLI framework must not change the CLI. This test compares the
live app against ``tests/data/cli_surface.json``, a snapshot taken from the
Click implementation before the Typer cutover, so a dropped flag or a renamed
option is a failing test rather than a user's broken script.

If a change to the surface is *intended*, regenerate the snapshot in the same
commit — that makes it visible in review instead of invisible:

```shell
uv run python dev/snapshot_cli_surface.py
```
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from cellpy import log

log.setup_logging(default_level=logging.DEBUG, testing=True)

SNAPSHOT = Path(__file__).parent / "data" / "cli_surface.json"


def _live_surface() -> dict:
    """Describe the live CLI using the same code the snapshot script uses.

    Loaded by path rather than imported as ``dev.snapshot_cli_surface``:
    ``dev/`` is a scripts directory, not a package, so whether it is importable
    depends on how pytest was invoked. Sharing the *implementation* is the
    point; sharing an import path is not.
    """
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "dev" / "snapshot_cli_surface.py"
    spec = importlib.util.spec_from_file_location("_cli_surface_snapshot", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_surface()


@pytest.fixture(scope="module")
def expected() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def actual() -> dict:
    return _live_surface()


@pytest.mark.essential
def test_the_command_set_is_unchanged(expected, actual):
    assert [c["name"] for c in actual["commands"]] == [
        c["name"] for c in expected["commands"]
    ]


@pytest.mark.essential
def test_every_command_keeps_its_flags(expected, actual):
    """The check that matters: no option silently renamed or dropped."""
    expected_by_name = {c["name"]: c for c in expected["commands"]}
    differences = []

    for command in actual["commands"]:
        name = command["name"]
        before = expected_by_name.get(name)
        if before is None:
            differences.append(f"{name}: new command not in the snapshot")
            continue

        before_opts = {tuple(p["opts"]) for p in before["params"]}
        after_opts = {tuple(p["opts"]) for p in command["params"]}

        for missing in sorted(before_opts - after_opts):
            differences.append(f"{name}: lost {'/'.join(missing)}")
        for added in sorted(after_opts - before_opts):
            differences.append(f"{name}: added {'/'.join(added)}")

    assert not differences, "the CLI surface changed:\n  " + "\n  ".join(differences)


@pytest.mark.essential
def test_flags_stay_flags(expected, actual):
    """A flag that becomes a value option breaks `cellpy run --raw`."""
    expected_by_name = {c["name"]: c for c in expected["commands"]}
    differences = []

    for command in actual["commands"]:
        before = expected_by_name.get(command["name"])
        if before is None:
            continue
        before_flags = {
            tuple(p["opts"]): p["is_flag"] for p in before["params"]
        }
        for param in command["params"]:
            key = tuple(param["opts"])
            if key in before_flags and before_flags[key] != param["is_flag"]:
                differences.append(
                    f"{command['name']}: {'/'.join(key)} flag-ness changed "
                    f"({before_flags[key]} -> {param['is_flag']})"
                )

    assert not differences, "\n  ".join(differences)


@pytest.mark.essential
def test_subcommands_are_unchanged(expected, actual):
    expected_by_name = {c["name"]: c for c in expected["commands"]}
    for command in actual["commands"]:
        before = expected_by_name.get(command["name"], {})
        assert command.get("subcommands") == before.get("subcommands"), command["name"]


@pytest.mark.essential
def test_the_snapshot_is_not_empty(expected):
    """Guard against a truncated snapshot silently passing everything."""
    assert len(expected["commands"]) >= 8
    assert sum(len(c["params"]) for c in expected["commands"]) >= 50
