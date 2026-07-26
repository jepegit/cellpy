"""Unit tests for remote OtherPath.rglob symlink following (issue #688)."""

from __future__ import annotations

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

    def info(self, path):
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
        path = path.rstrip("/") or "/"
        entries = self.tree.get(path, [])
        if detail:
            return list(entries)
        return [e["name"] for e in entries]

    def isdir(self, path):
        path = path.rstrip("/") or "/"
        if path in self.tree or path in self.link_dirs:
            return True
        return False

    def isfile(self, path):
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
