"""`cellpy mcp` — the shim over the separate `cellpy-mcp` distribution (#840).

cellpy deliberately does not depend on the MCP SDK: the server lives in its own
package so it can move at the SDK's pace, and so a long-lived network-facing
process is not something the data library carries. What cellpy provides is the
entry point people can find.

That makes the interesting behaviour *the absence case* — what happens when the
package is not installed — and the contract with it when it is. Both are tested
here against a stub, because installing the real package to test the shim would
be testing the wrong thing.

Assertions read the console, not the `echo` callable: passing an `echo` is what
switches the reporter on (a library does not print because someone imported
it), but the reporter then writes to the console itself — successes to stdout
and failures to stderr, which the tests check separately because for `serve`
that separation is load-bearing.
"""

from __future__ import annotations

import logging
import sys
import types

import pytest
from typer.testing import CliRunner

from cellpy import cli, cli_api, log

log.setup_logging(default_level=logging.DEBUG, testing=True)

pytestmark = pytest.mark.essential


@pytest.fixture(autouse=True)
def _plain_output(monkeypatch):
    """Help and reporter output without ANSI, so substring assertions hold."""
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")


@pytest.fixture()
def absent(monkeypatch):
    """`cellpy_mcp` is not importable, however the machine is actually set up."""
    monkeypatch.delitem(sys.modules, cli_api.MCP_MODULE, raising=False)
    real_import = __import__

    def _import(name, *args, **kwargs):
        if name == cli_api.MCP_MODULE:
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _import)


@pytest.fixture()
def stub(monkeypatch):
    """A stand-in for the real package, recording what the shim passed it."""
    module = types.ModuleType(cli_api.MCP_MODULE)
    module.__version__ = "0.1.0"
    module.calls = []

    def serve(root=None):
        module.calls.append(("serve", root))

    def install(root=None, client=None, dry_run=False):
        module.calls.append(("install", root, client, dry_run))
        return "/somewhere/claude_desktop_config.json"

    def describe():
        return {"root": "/data/cells", "client": "claude-desktop"}

    module.serve = serve
    module.install = install
    module.describe = describe
    monkeypatch.setitem(sys.modules, cli_api.MCP_MODULE, module)
    return module


# -- the absence case ------------------------------------------------------------


def test_serve_says_how_to_install_and_fails(absent, capsys):
    """A missing optional package is a usage problem, not a traceback.

    On **stderr**: a failure has to survive `cellpy mcp serve > somewhere`,
    and stdout is the protocol channel for this command in particular.
    """
    assert cli_api.mcp_serve(echo=print) is True
    printed = capsys.readouterr().err
    assert cli_api.MCP_DISTRIBUTION in printed
    assert f"pip install {cli_api.MCP_DISTRIBUTION}" in printed


def test_status_reports_not_installed_and_still_succeeds(absent, capsys):
    """`cellpy mcp status` is the command you script to find this out.

    Exiting non-zero for "not installed" would make it useless as the check it
    exists to be — the answer is true and useful, not an error.
    """
    assert cli_api.mcp_status(echo=print) is False
    printed = capsys.readouterr().out
    assert "not installed" in printed
    assert f"pip install {cli_api.MCP_DISTRIBUTION}" in printed


def test_the_hint_names_the_distribution_not_the_module(absent, capsys):
    """`pip install cellpy_mcp` is a 404. The two names differ on purpose."""
    cli_api.mcp_serve(echo=print)
    printed = capsys.readouterr().err
    assert "pip install cellpy-mcp" in printed
    assert "pip install cellpy_mcp" not in printed


# -- the contract with the package -----------------------------------------------


def test_serve_hands_the_root_through(stub):
    assert cli_api.mcp_serve(root="/data/cells", echo=print) is False
    assert stub.calls == [("serve", "/data/cells")]


def test_serve_prints_nothing(stub, capsys):
    """stdout *is* the protocol channel — a banner on it is a parse error.

    Every other command in cellpy reports what it is doing. This one must not.
    """
    cli_api.mcp_serve(root="/data/cells", echo=print)
    assert capsys.readouterr().out == ""


def test_install_passes_the_arguments_and_reports_where(stub, capsys):
    assert (
        cli_api.mcp_install(
            root="/data/cells", client="claude-desktop", dry_run=True, echo=print
        )
        is False
    )
    assert stub.calls == [("install", "/data/cells", "claude-desktop", True)]
    assert "claude_desktop_config.json" in capsys.readouterr().out


def test_a_dry_run_does_not_tell_you_to_restart(stub, capsys):
    cli_api.mcp_install(dry_run=True, echo=print)
    assert "restart" not in capsys.readouterr().out.lower()

    cli_api.mcp_install(dry_run=False, echo=print)
    assert "restart" in capsys.readouterr().out.lower()


def test_install_failure_is_reported_not_raised(stub, monkeypatch, capsys):
    """The package raising is a message on screen and a non-zero exit."""

    def boom(root=None, client=None, dry_run=False):
        raise RuntimeError("config file is not valid json")

    monkeypatch.setattr(stub, "install", boom)
    assert cli_api.mcp_install(echo=print) is True
    assert "not valid json" in capsys.readouterr().err


def test_status_reports_both_versions(stub, capsys):
    cli_api.mcp_status(echo=print)
    printed = capsys.readouterr().out

    import cellpy

    assert cellpy.__version__ in printed
    # Importable but not pip-installed (an editable checkout) still answers.
    assert "0.1.0" in printed
    # And whatever the package wants to add about itself.
    assert "/data/cells" in printed


# -- through the command line ----------------------------------------------------


def test_the_command_group_exposes_three_verbs():
    result = CliRunner().invoke(cli.cli, ["mcp", "--help"])
    assert result.exit_code == 0
    for verb in ("serve", "install", "status"):
        assert verb in result.output


def test_serve_exits_non_zero_when_the_package_is_missing(absent):
    result = CliRunner().invoke(cli.cli, ["mcp", "serve"])
    assert result.exit_code == 1


def test_status_exits_zero_when_the_package_is_missing(absent):
    result = CliRunner().invoke(cli.cli, ["mcp", "status"])
    assert result.exit_code == 0
    assert "not installed" in result.output
