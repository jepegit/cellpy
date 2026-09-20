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

import json
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
    """`cellpy_mcp` is not importable, however the machine is actually set up.

    ``None`` in ``sys.modules`` makes both ``import`` and
    ``importlib.import_module`` raise ``ImportError`` — patching
    ``builtins.__import__`` alone leaves ``importlib`` finding a real install.
    """
    monkeypatch.setitem(sys.modules, cli_api.MCP_MODULE, None)
    for name in list(sys.modules):
        if name.startswith(f"{cli_api.MCP_MODULE}."):
            monkeypatch.setitem(sys.modules, name, None)


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
    # A real install's submodules must not leak through the stub.
    monkeypatch.setitem(sys.modules, f"{cli_api.MCP_MODULE}.clients", None)
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


def test_list_clients_calls_the_package_and_does_not_write(stub, capsys):
    """`--list-clients` must not call `install` — that writes a config."""

    def list_clients():
        stub.calls.append(("list_clients",))
        return "claude-desktop  /tmp/claude.json"

    stub.list_clients = list_clients
    assert cli_api.mcp_install(list_clients=True, echo=print) is False
    assert stub.calls == [("list_clients",)]
    printed = capsys.readouterr().out
    assert "claude-desktop" in printed
    assert "restart" not in printed.lower()


def test_list_clients_without_helpers_fails_and_does_not_write(stub, capsys):
    """A stub (or old package) with no lister must not invent a path table."""
    assert cli_api.mcp_install(list_clients=True, echo=print) is True
    assert stub.calls == []
    printed = capsys.readouterr().err
    assert "python -m cellpy_mcp install --list-clients" in printed


def test_list_clients_absent_package_uses_the_install_hint(absent, capsys):
    assert cli_api.mcp_install(list_clients=True, echo=print) is True
    printed = capsys.readouterr().err
    assert f"pip install {cli_api.MCP_DISTRIBUTION}" in printed


def test_status_reports_both_versions(stub, capsys):
    cli_api.mcp_status(echo=print)
    printed = capsys.readouterr().out

    import cellpy

    assert cellpy.__version__ in printed
    # Importable but not pip-installed (an editable checkout) still answers.
    assert "0.1.0" in printed
    # And whatever the package wants to add about itself.
    assert "/data/cells" in printed


def test_install_unknown_client_hints_at_an_old_server_build(stub, capsys):
    """cellpy-mcp 0.1.0 knows only Claude Desktop; `--client cursor` is not a typo."""

    def old_build(root=None, client=None, dry_run=False):
        raise ValueError("Unknown client 'cursor'. Known clients: claude-desktop.")

    stub.install = old_build
    assert cli_api.mcp_install(client="cursor", echo=print) is True
    printed = capsys.readouterr().err
    assert "Unknown client 'cursor'" in printed
    assert "upgrade" in printed


# -- check: spawn the server like a client would ---------------------------------

# A stand-in server: answers the three requests the probe makes, over stdio,
# with newline-delimited JSON-RPC — exactly what the MCP SDK does.
FAKE_SERVER = """
import json, sys
mode = sys.argv[1] if len(sys.argv) > 1 else "ok"
if mode == "banner":
    print("cellpy-mcp starting up...", flush=True)
if mode == "exit":
    print("could not import cellpy", file=sys.stderr)
    sys.exit(3)
for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    method = message["method"]
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {},
                  "serverInfo": {"name": "fake-cellpy-mcp", "version": "9.9"}}
    elif method == "tools/list":
        result = {"tools": []} if mode == "notools" else {
            "tools": [{"name": "list_instruments"}, {"name": "load_cell"}]}
    elif method == "tools/call":
        result = {"content": [{"type": "text",
                  "text": json.dumps({"instruments": [{"id": "arbin_res"}, {"id": "neware_txt"}]})}]}
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
"""


@pytest.fixture()
def fake_server(tmp_path):
    script = tmp_path / "fake_server.py"
    script.write_text(FAKE_SERVER, encoding="utf-8")
    return script


def test_probe_completes_the_handshake_and_lists_tools(fake_server):
    report = cli_api._mcp_probe([sys.executable, str(fake_server)], timeout=30)
    assert report["server"] == {"name": "fake-cellpy-mcp", "version": "9.9"}
    assert report["tools"] == ["list_instruments", "load_cell"]
    assert report["instruments"] == 2


def test_probe_names_a_banner_on_stdout(fake_server):
    """The classic mistake: something friendly printed on the protocol channel."""
    with pytest.raises(cli_api._McpProbeFailed, match="stdout is not JSON-RPC"):
        cli_api._mcp_probe([sys.executable, str(fake_server), "banner"], timeout=30)


def test_probe_quotes_stderr_when_the_server_dies(fake_server):
    with pytest.raises(cli_api._McpProbeFailed, match="exited with code 3.*could not import cellpy"):
        cli_api._mcp_probe([sys.executable, str(fake_server), "exit"], timeout=30)


def test_probe_gives_up_after_the_timeout(fake_server):
    silent = [sys.executable, "-c", "import time; time.sleep(30)"]
    with pytest.raises(cli_api._McpProbeFailed, match="no answer to initialize within"):
        cli_api._mcp_probe(silent, timeout=1)


def test_check_without_a_client_spawns_this_interpreter(stub, monkeypatch, capsys):
    seen = {}

    def probe(command, env=None, timeout=60.0):
        seen.update(command=command, env=env)
        return {"server": {"name": "cellpy"}, "protocol": "2025-06-18", "tools": ["load_cell"], "instruments": 3}

    monkeypatch.setattr(cli_api, "_mcp_probe", probe)
    assert cli_api.mcp_check(root="/data/cells", echo=print) is False
    assert seen["command"] == [sys.executable, "-m", cli_api.MCP_MODULE]
    assert seen["env"]["CELLPY_MCP_ROOT"] == "/data/cells"
    printed = capsys.readouterr().out
    assert "load_cell" in printed
    assert "3 instruments" in printed


def test_check_absent_package_uses_the_install_hint(absent, capsys):
    assert cli_api.mcp_check(echo=print) is True
    assert f"pip install {cli_api.MCP_DISTRIBUTION}" in capsys.readouterr().err


@pytest.fixture()
def cursor_config(stub, monkeypatch, tmp_path):
    """A stubbed `cellpy_mcp.clients` that points Cursor's config at tmp_path."""
    clients = types.ModuleType(f"{cli_api.MCP_MODULE}.clients")
    target = tmp_path / "mcp.json"
    clients.CLIENTS = {"cursor": types.SimpleNamespace(key="mcpServers")}

    def config_path(name):
        if name != "cursor":
            raise ValueError(f"Unknown client {name!r}. Known clients: cursor.")
        return target

    clients.config_path = config_path
    monkeypatch.setitem(sys.modules, clients.__name__, clients)
    return target


def _register(target, command, args, env=None):
    target.write_text(
        json.dumps({"mcpServers": {"cellpy": {"command": command, "args": args, "env": env or {}}}}),
        encoding="utf-8",
    )


def test_check_client_runs_the_registered_command(cursor_config, fake_server, capsys):
    """What Cursor will spawn is what gets tested — not what this env would write."""
    _register(cursor_config, sys.executable, [str(fake_server)], {"CELLPY_MCP_ROOT": "/data/cells"})
    assert cli_api.mcp_check(client="cursor", echo=print) is False
    printed = capsys.readouterr().out
    assert str(cursor_config) in printed
    assert "fake-cellpy-mcp 9.9" in printed
    assert "2 (list_instruments, load_cell)" in printed
    assert "restart cursor" in printed


def test_check_client_not_registered_says_how(cursor_config, capsys):
    assert cli_api.mcp_check(client="cursor", echo=print) is True
    printed = capsys.readouterr().err
    assert "no MCP config yet" in printed
    assert "cellpy mcp install --client cursor" in printed


def test_check_client_names_a_missing_interpreter(cursor_config, capsys):
    """The number one reason a client shows the server as failed."""
    _register(cursor_config, "/nowhere/bin/python", ["-m", "cellpy_mcp"])
    assert cli_api.mcp_check(client="cursor", echo=print) is True
    printed = capsys.readouterr().err
    assert "/nowhere/bin/python" in printed
    assert "does not exist" in printed
    assert "re-run" in printed


def test_check_client_reports_a_server_without_tools(cursor_config, fake_server, capsys):
    _register(cursor_config, sys.executable, [str(fake_server), "notools"])
    assert cli_api.mcp_check(client="cursor", echo=print) is True
    assert "lists no tools" in capsys.readouterr().err


def test_check_unknown_client_is_reported(cursor_config, capsys):
    assert cli_api.mcp_check(client="windsurf", echo=print) is True
    assert "Unknown client 'windsurf'" in capsys.readouterr().err


# -- through the command line ----------------------------------------------------


def test_the_command_group_exposes_four_verbs():
    result = CliRunner().invoke(cli.cli, ["mcp", "--help"])
    assert result.exit_code == 0
    for verb in ("serve", "install", "status", "check"):
        assert verb in result.output


def test_check_help_lists_client_and_timeout():
    result = CliRunner().invoke(cli.cli, ["mcp", "check", "--help"])
    assert result.exit_code == 0
    assert "--client" in result.output
    assert "--timeout" in result.output


def test_check_exits_non_zero_when_the_package_is_missing(absent):
    result = CliRunner().invoke(cli.cli, ["mcp", "check"])
    assert result.exit_code == 1


def test_install_help_lists_list_clients():
    result = CliRunner().invoke(cli.cli, ["mcp", "install", "--help"])
    assert result.exit_code == 0
    assert "--list-clients" in result.output


def test_serve_exits_non_zero_when_the_package_is_missing(absent):
    result = CliRunner().invoke(cli.cli, ["mcp", "serve"])
    assert result.exit_code == 1


def test_status_exits_zero_when_the_package_is_missing(absent):
    result = CliRunner().invoke(cli.cli, ["mcp", "status"])
    assert result.exit_code == 0
    assert "not installed" in result.output


def test_cli_list_clients_does_not_write(stub):
    stub.list_clients = lambda: stub.calls.append(("list_clients",)) or "ok"
    result = CliRunner().invoke(cli.cli, ["mcp", "install", "--list-clients"])
    assert result.exit_code == 0
    assert stub.calls == [("list_clients",)]
    assert "restart" not in result.output.lower()
