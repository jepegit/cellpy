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
def test_arguments_did_not_become_options(expected, actual):
    """Positional arguments must stay positional.

    Worth its own test because this is the check the *first* version of the
    snapshot script could not make: it classified parameters with
    `isinstance(param, click.Argument)` against the installed Click, and Typer
    vendors its own, so under Typer every argument would have been silently
    recorded as an option and this comparison would have passed either way.
    """
    expected_by_name = {c["name"]: c for c in expected["commands"]}
    differences = []

    for command in actual["commands"]:
        before = expected_by_name.get(command["name"])
        if before is None:
            continue
        before_kind = {tuple(p["opts"]): p["kind"] for p in before["params"]}
        for param in command["params"]:
            key = tuple(param["opts"])
            if key in before_kind and before_kind[key] != param["kind"]:
                differences.append(
                    f"{command['name']}: {'/'.join(key)} became "
                    f"{param['kind']} (was {before_kind[key]})"
                )

    assert not differences, "\n  ".join(differences)
    # and there really are arguments to check
    assert any(
        p["kind"] == "argument" for c in expected["commands"] for p in c["params"]
    )


@pytest.mark.essential
def test_the_snapshot_is_not_empty(expected):
    """Guard against a truncated snapshot silently passing everything."""
    assert len(expected["commands"]) >= 8
    assert sum(len(c["params"]) for c in expected["commands"]) >= 50


@pytest.mark.essential
def test_click_is_not_a_declared_dependency():
    """cellpy speaks Typer now; Click comes along only inside it (#569)."""
    import tomllib

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    declared = data["project"]["dependencies"]
    bare = {
        d.split(">")[0].split("<")[0].split("=")[0].split(";")[0].strip()
        for d in declared
    }
    assert "click" not in bare, "click is back in the dependency list"
    assert "typer" in bare


@pytest.mark.essential
@pytest.mark.parametrize(
    "manifest",
    [
        "environment.yml",
        "environment_dev.yml",
        "github_actions_environment.yml",
        "dev/conda-recipes/cellpy/meta.yaml",
    ],
)
def test_click_is_gone_from_the_packaging_manifests(manifest):
    """pyproject is not the only place a dependency is declared.

    Parsed line-wise rather than as YAML: the conda recipe is a Jinja
    template, so a YAML parser chokes on it.
    """
    path = Path(__file__).resolve().parents[1] / manifest
    if not path.is_file():
        pytest.skip(f"missing {manifest}")

    listed = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() in {"- click", "- click,"}
    ]
    assert not listed, f"{manifest} still lists click"


@pytest.mark.essential
def test_the_cli_module_does_not_import_click():
    """A declared-dependency check alone would miss a stray `import click`."""
    source = (
        Path(__file__).resolve().parents[1] / "cellpy" / "cli.py"
    ).read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import click", "from click"))
    ]
    assert not offenders, offenders
