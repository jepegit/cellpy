"""Unit tests for remote OtherPath.rglob symlink following (#688) and perf (#690)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cellpy.internals.connections import OtherPath


class _FakeFS:
    """Minimal fsspec-like FS: projects/LongLife is a symlink to real_store."""

    def __init__(self):
        self.tree = {
            "/home/user/projects": [
                {
                    "name": "/home/user/projects/LongLife",
                    "type": "link",
                    "size": 8,
                    "destination": "/data/LongLife",
                },
                {"name": "/home/user/projects/plain", "type": "directory", "size": 0},
            ],
            "/home/user/projects/LongLife": [
                {
                    "name": "/home/user/projects/LongLife/20250709_lol079_01_cc_01.h5",
                    "type": "file",
                    "size": 10,
                },
            ],
            "/home/user/projects/plain": [
                {
                    "name": "/home/user/projects/plain/other.h5",
                    "type": "file",
                    "size": 4,
                },
            ],
            # Cycle via two link paths that share destination /real/loop
            "/home/user/cycle": [
                {
                    "name": "/home/user/cycle/loop_a",
                    "type": "link",
                    "destination": "/real/loop",
                },
            ],
            "/home/user/cycle/loop_a": [
                {
                    "name": "/home/user/cycle/loop_a/loop_b",
                    "type": "link",
                    "destination": "/real/loop",
                },
                {
                    "name": "/home/user/cycle/loop_a/ok.h5",
                    "type": "file",
                    "size": 1,
                },
            ],
            "/home/user/cycle/loop_a/loop_b": [
                {
                    "name": "/home/user/cycle/loop_a/loop_b/again",
                    "type": "link",
                    "destination": "/real/loop",
                },
            ],
        }
        self._info = {
            "/home/user/projects/LongLife": {
                "name": "/home/user/projects/LongLife",
                "type": "directory",
                "destination": "/data/LongLife",
            },
            "/home/user/cycle/loop_a": {
                "name": "/home/user/cycle/loop_a",
                "type": "directory",
                "destination": "/real/loop",
            },
            "/home/user/cycle/loop_a/loop_b": {
                "name": "/home/user/cycle/loop_a/loop_b",
                "type": "directory",
                "destination": "/real/loop",
            },
            "/home/user/cycle/loop_a/loop_b/again": {
                "name": "/home/user/cycle/loop_a/loop_b/again",
                "type": "directory",
                "destination": "/real/loop",
            },
        }
        self.link_dirs = set(self._info)
        self.info_calls = 0
        self.isdir_calls = 0
        self.ls_calls = 0
        self.isfile_calls = 0
        self.client = None

    def info(self, path):
        self.info_calls += 1
        path = path.rstrip("/") or "/"
        if path in self._info:
            return dict(self._info[path])
        if path in self.tree:
            return {"name": path, "type": "directory"}
        for entries in self.tree.values():
            for e in entries:
                if e["name"] == path:
                    return dict(e)
        raise FileNotFoundError(path)

    def ls(self, path, detail=True):
        self.ls_calls += 1
        path = path.rstrip("/") or "/"
        # Symlink project dirs list via their path key (Paramiko follows for listdir).
        entries = self.tree.get(path)
        if entries is None and path in self.link_dirs:
            # Destination-only keys are not listed; treat as empty dir listing success.
            entries = []
        if entries is None:
            entries = []
        if detail:
            return list(entries)
        return [e["name"] for e in entries]

    def isdir(self, path):
        self.isdir_calls += 1
        path = path.rstrip("/") or "/"
        if path in self.tree or path in self.link_dirs:
            return True
        return False

    def isfile(self, path):
        self.isfile_calls += 1
        path = path.rstrip("/") or "/"
        for entries in self.tree.values():
            for e in entries:
                if e["name"] == path and e.get("type") == "file":
                    return True
        return False


class _FakeUPath:
    def __init__(self, *args, fs=None, **kwargs):
        self._url = str(args[0])
        after_scheme = self._url.split("://", 1)[-1]
        self.path = "/" + after_scheme.split("/", 1)[-1]
        self.storage_options = kwargs
        self.fs = fs if fs is not None else _FakeFS()
        self.name = self.path.rstrip("/").rsplit("/", 1)[-1]
        self.protocol = "sftp"

    def __str__(self):
        return self._url


@pytest.fixture
def fake_remote(monkeypatch, mock_env_cellpy_key_filename):
    shared_fs = _FakeFS()

    class _BoundFakeUPath(_FakeUPath):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, fs=shared_fs, **kwargs)

    monkeypatch.setattr("cellpy.internals.otherpath.UPath", _BoundFakeUPath)
    return shared_fs


def test_rglob_follows_directory_symlink(fake_remote):
    root = OtherPath("sftp://user@host/home/user/projects")
    names = sorted(p.name for p in root.rglob("*.h5", testing=True))
    assert "20250709_lol079_01_cc_01.h5" in names
    assert "other.h5" in names


def test_rglob_star_includes_symlink_children(fake_remote):
    root = OtherPath("sftp://user@host/home/user/projects")
    paths = [p.raw_path for p in root.rglob("*", testing=True)]
    assert any(p.endswith("20250709_lol079_01_cc_01.h5") for p in paths)


def test_rglob_cycle_guard_terminates(fake_remote):
    root = OtherPath("sftp://user@host/home/user/cycle")
    names = sorted(p.name for p in root.rglob("*.h5", testing=True))
    assert names == ["ok.h5"]


def test_rglob_files_only_skips_directories(fake_remote):
    root = OtherPath("sftp://user@host/home/user/projects")
    paths = [p.raw_path for p in root.rglob("*", testing=True, files_only=True)]
    assert all(p.endswith(".h5") for p in paths)
    assert any(p.endswith("20250709_lol079_01_cc_01.h5") for p in paths)
    assert any(p.endswith("other.h5") for p in paths)


def test_rglob_walk_avoids_per_dir_info_and_isdir(fake_remote):
    """STAT diet (#690): reuse ls detail; probe links with ls, not isdir+info."""
    root = OtherPath("sftp://user@host/home/user/projects")
    list(root.rglob("*.h5", testing=True))
    # Root may still call info once; children should use ls detail / destination.
    assert fake_remote.info_calls <= 1
    assert fake_remote.isdir_calls == 0


def test_rglob_find_l_fast_path(fake_remote):
    """When Paramiko exec is available, files_only uses find -L (#690)."""

    class _Stdout:
        def __init__(self, text: str):
            self.channel = SimpleNamespace(recv_exit_status=lambda: 0)
            self._text = text.encode("utf-8")

        def read(self):
            return self._text

    class _Stderr:
        def read(self):
            return b""

    def exec_command(cmd, timeout=None):
        assert "find -L" in cmd
        assert "-type f" in cmd
        body = "\n".join(
            [
                "/home/user/projects/LongLife/20250709_lol079_01_cc_01.h5",
                "/home/user/projects/plain/other.h5",
            ]
        )
        return None, _Stdout(body), _Stderr()

    fake_remote.client = SimpleNamespace(exec_command=exec_command)
    ls_before = fake_remote.ls_calls
    root = OtherPath("sftp://user@host/home/user/projects")
    names = sorted(p.name for p in root.rglob("*.h5", testing=True, files_only=True))
    assert names == ["20250709_lol079_01_cc_01.h5", "other.h5"]
    assert fake_remote.ls_calls == ls_before  # walk not used


def test_rglob_find_l_keeps_listing_on_exit_1(fake_remote):
    """Partial ``find`` (unreadable sibling -> exit 1) still lists files (#897)."""

    class _Stdout:
        def __init__(self, text: str):
            self.channel = SimpleNamespace(recv_exit_status=lambda: 1)
            self._text = text.encode("utf-8")

        def read(self):
            return self._text

    class _Stderr:
        def read(self):
            return b"find: '/home/user/projects/secret': Permission denied\n"

    def exec_command(cmd, timeout=None):
        body = "\n".join(
            [
                "/home/user/projects/LongLife/20250709_lol079_01_cc_01.h5",
                "/home/user/projects/plain/other.h5",
            ]
        )
        return None, _Stdout(body), _Stderr()

    fake_remote.client = SimpleNamespace(exec_command=exec_command)
    ls_before = fake_remote.ls_calls
    root = OtherPath("sftp://user@host/home/user/projects")
    names = sorted(p.name for p in root.rglob("*.h5", testing=True, files_only=True))
    assert names == ["20250709_lol079_01_cc_01.h5", "other.h5"]
    assert fake_remote.ls_calls == ls_before  # walk not used


def test_rglob_find_l_exit_1_without_output_falls_back_to_walk(fake_remote):
    """Exit 1 and nothing listed is a real failure -> walk (#897)."""

    class _Stdout:
        def __init__(self):
            self.channel = SimpleNamespace(recv_exit_status=lambda: 1)

        def read(self):
            return b"\n  \n"

    class _Stderr:
        def read(self):
            return b"find: '/home/user/projects': Permission denied\n"

    def exec_command(cmd, timeout=None):
        return None, _Stdout(), _Stderr()

    fake_remote.client = SimpleNamespace(exec_command=exec_command)
    root = OtherPath("sftp://user@host/home/user/projects")
    names = sorted(p.name for p in root.rglob("*.h5", testing=True, files_only=True))
    assert "20250709_lol079_01_cc_01.h5" in names
    assert fake_remote.ls_calls > 0


def test_rglob_find_l_failure_falls_back_to_walk(fake_remote):
    def exec_command(cmd, timeout=None):
        raise OSError("no shell")

    fake_remote.client = SimpleNamespace(exec_command=exec_command)
    root = OtherPath("sftp://user@host/home/user/projects")
    names = sorted(p.name for p in root.rglob("*.h5", testing=True, files_only=True))
    assert "20250709_lol079_01_cc_01.h5" in names
    assert fake_remote.ls_calls > 0
