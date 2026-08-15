"""Shared helpers for the #895 speed harness.

Paths come from the environment or a local journal — never hard-coded hosts,
usernames, or project names. Printed paths are redacted.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
TMP = HERE / "_tmp"


def env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def journal_path() -> Path:
    raw = env("SPEEDTEST_JOURNAL")
    if raw:
        return Path(raw)
    raise SystemExit(
        "Set SPEEDTEST_JOURNAL to a batch journal JSON "
        "(do not commit that file; it usually has remote URIs)."
    )


def project_name() -> str:
    name = env("SPEEDTEST_PROJECT")
    if not name:
        raise SystemExit("Set SPEEDTEST_PROJECT to the project subfolder under rawdatadir.")
    return name


def cell_label(journal=None) -> str:
    label = env("SPEEDTEST_LABEL")
    if label:
        return label
    if journal is not None:
        from cellpy.batch.journal import FILENAME

        return journal.pages[FILENAME][0]
    raise SystemExit("Set SPEEDTEST_LABEL or pass a journal with pages.")


def raw_extension() -> str:
    return env("SPEEDTEST_EXT", "h5")


def redact(value) -> str:
    """Hide host, user home, and AD-style user@domain path segments."""
    text = str(value)
    text = re.sub(r"(?i)[A-Za-z]:[\\/]Users[\\/][^\\/]+", "<home>", text)
    text = re.sub(r"/home/[^/]+", "/home/<user>", text)
    text = re.sub(r"(?i)\\Users\\[^\\]+", r"\\Users\\<user>", text)
    parts = urlsplit(text)
    if parts.scheme and parts.netloc:
        path = parts.path
        path = re.sub(r"/home/[^/]+", "/home/<user>", path)
        return f"{parts.scheme}://<host>{path}"
    return text


def redact_name(value) -> str:
    """Print only the basename (safe for logs)."""
    text = str(value)
    if not text:
        return text
    return Path(text.replace("\\", "/").rstrip("/")).name


def step(label: str, fn):
    t0 = time.perf_counter()
    value = fn()
    print(f"{time.perf_counter() - t0:8.3f}s  {label}", flush=True)
    return value
