"""Live SFTP integration tests for OtherPath (Docker atmoz/sftp).

Deselected by default (``onlylocal``). The session fixture starts
``docker/sftp-test/compose.yml`` when Docker is available.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import time

import pytest

from cellpy.internals.connections import OtherPath

pytestmark = pytest.mark.onlylocal

COMPOSE_FILE = (
    pathlib.Path(__file__).resolve().parents[1] / "docker" / "sftp-test" / "compose.yml"
)
SFTP_USER = "cellpy"
SFTP_PASSWORD = "cellpy"
SFTP_HOST = "127.0.0.1"
SFTP_PORT = 2223
REMOTE_ROOT = "/testdata"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            timeout=20,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False


def _compose(*args: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "docker compose failed "
            f"(exit {proc.returncode}): {' '.join(args)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def _wait_for_sftp(timeout: float = 30.0) -> None:
    """Poll until Paramiko/fsspec can authenticate."""
    import paramiko

    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                SFTP_HOST,
                port=SFTP_PORT,
                username=SFTP_USER,
                password=SFTP_PASSWORD,
                allow_agent=False,
                look_for_keys=False,
                timeout=2,
            )
            client.close()
            return
        except Exception as exc:  # noqa: BLE001 - retry until ready
            last_err = exc
            time.sleep(0.5)
        finally:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass
    raise TimeoutError(f"SFTP server not ready on {SFTP_HOST}:{SFTP_PORT}: {last_err}")


@pytest.fixture(scope="session")
def sftp_server():
    """Start the docker SFTP fixture for the test session."""
    if not COMPOSE_FILE.is_file():
        pytest.skip(f"compose file missing: {COMPOSE_FILE}")
    if not _docker_available():
        pytest.skip("Docker not available")

    _compose("up", "-d", "--wait")
    try:
        _wait_for_sftp()
        yield {
            "user": SFTP_USER,
            "password": SFTP_PASSWORD,
            "host": SFTP_HOST,
            "port": SFTP_PORT,
            "root": REMOTE_ROOT,
        }
    finally:
        _compose("down", "-v")


@pytest.fixture
def sftp_env(monkeypatch, sftp_server):
    """Point cellpy env credentials at the docker SFTP user."""
    monkeypatch.setenv("CELLPY_PASSWORD", sftp_server["password"])
    monkeypatch.delenv("CELLPY_KEY_FILENAME", raising=False)
    monkeypatch.setenv("CELLPY_USER", sftp_server["user"])
    monkeypatch.setenv("CELLPY_HOST", f"{sftp_server['host']}:{sftp_server['port']}")
    return sftp_server


def _uri(sftp_server, *parts: str, scheme: str = "sftp") -> str:
    path = "/".join(p.strip("/") for p in parts)
    return (
        f"{scheme}://{sftp_server['user']}@{sftp_server['host']}:{sftp_server['port']}"
        f"/{path}"
    )


def test_remote_properties_and_truthful_stat(sftp_env):
    hello = OtherPath(_uri(sftp_env, REMOTE_ROOT, "hello.txt"))
    missing = OtherPath(_uri(sftp_env, REMOTE_ROOT, "no-such-file.txt"))
    nested_dir = OtherPath(_uri(sftp_env, REMOTE_ROOT, "nested"))

    assert hello.is_external is True
    assert hello.uri_prefix == "sftp://"
    assert hello.location == f"{sftp_env['user']}@{sftp_env['host']}:{sftp_env['port']}"
    assert hello.raw_path == f"{REMOTE_ROOT}/hello.txt"
    assert hello.name == "hello.txt"
    assert hello.suffix == ".txt"

    assert hello.exists() is True
    assert hello.is_file() is True
    assert hello.is_dir() is False

    assert missing.exists() is False
    assert missing.is_file() is False

    assert nested_dir.exists() is True
    assert nested_dir.is_dir() is True
    assert nested_dir.is_file() is False

    st = hello.stat()
    assert st.st_size > 0


def test_remote_glob_rglob_and_joinpath(sftp_env):
    root = OtherPath(_uri(sftp_env, REMOTE_ROOT))
    names = sorted(p.name for p in root.glob("*.txt"))
    assert "hello.txt" in names

    nested = sorted(p.name for p in root.rglob("*.txt"))
    assert "hello.txt" in nested
    assert "sample.txt" in nested

    child = root / "nested" / "sample.txt"
    assert child.is_external is True
    assert child.exists() is True
    assert child.name == "sample.txt"
    assert child.parent.name == "nested"


def test_remote_copy_returns_local_path_with_content(sftp_env, tmp_path):
    remote = OtherPath(_uri(sftp_env, REMOTE_ROOT, "hello.txt"))
    local = remote.copy(destination=tmp_path)
    assert isinstance(local, pathlib.Path)
    assert not isinstance(local, OtherPath)
    assert local.is_file()
    assert local.read_text(encoding="utf-8").strip() == "cellpy sftp fixture"


def test_scp_alias_hits_same_backend(sftp_env):
    remote = OtherPath(_uri(sftp_env, REMOTE_ROOT, "hello.txt", scheme="scp"))
    assert remote.is_external is True
    assert remote.uri_prefix == "scp://"
    assert remote.exists() is True
    assert remote.is_file() is True


def test_ssh_scheme_against_docker(sftp_env):
    remote = OtherPath(_uri(sftp_env, REMOTE_ROOT, "hello.txt", scheme="ssh"))
    assert remote.uri_prefix == "ssh://"
    assert remote.exists() is True
