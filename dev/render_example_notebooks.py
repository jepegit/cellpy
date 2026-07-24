"""Render the example notebooks to committed markdown pages (#571).

Zensical does not render ``.ipynb`` — it copies them verbatim — so the example
notebooks are converted to markdown and the result is committed, following the
same approach as cellpy-core.

**Why this script rather than plain nbconvert.** The notebooks contain plotly
figures, and plotly embeds a self-contained HTML+JS blob per figure. A straight
``jupyter nbconvert --to markdown`` produces ~50 MB of generated markdown for
nine notebooks — one page alone is 15 MB — which is not something to put in a
git repository, and not something a reader wants to download either.

So heavy interactive output is stripped before conversion and the static
``image/png`` rendering is kept. Readers get the plots; the repository does not
get 50 MB of base64. Notebooks that only ever produced interactive figures will
show their code and text without a figure — the ``.ipynb`` stays in the docs
tree, linked as a download, for anyone who wants the interactive version.

Usage:

```shell
uv run --group docs python dev/render_example_notebooks.py
```

Re-run and commit the output whenever a notebook changes. This does **not**
execute the notebooks — it renders the outputs their authors committed. See the
note in ``docs/examples/index.md``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "docs" / "examples"

#: Output types that embed an entire JS runtime per figure.
HEAVY_MIMETYPES = (
    "text/html",
    "application/vnd.plotly.v1+json",
    "application/javascript",
    "application/vnd.jupyter.widget-view+json",
)

# CSI / OSC / other common terminal escape sequences from rich, click, etc.
_ANSI_RE = re.compile(
    r"\x1b(?:"
    r"\[[0-9;?]*[ -/]*[@-~]"  # CSI
    r"|][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC
    r"|[PX^_][^\x1b]*\x1b\\"  # DCS / PM / APC / SOS
    r"|[@-Z\\-_]"  # 2-byte sequences
    r")"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text*."""
    return _ANSI_RE.sub("", text)


def _strip_ansi_in_value(value: str | list[str]) -> tuple[str | list[str], int]:
    """Strip ANSI from a notebook text payload (string or list of lines)."""
    hits = 0
    if isinstance(value, list):
        cleaned: list[str] = []
        for line in value:
            if isinstance(line, str) and "\x1b" in line:
                hits += line.count("\x1b")
                cleaned.append(strip_ansi(line))
            else:
                cleaned.append(line)
        return cleaned, hits
    if isinstance(value, str) and "\x1b" in value:
        hits = value.count("\x1b")
        return strip_ansi(value), hits
    return value, hits


def strip_heavy_outputs(notebook: dict) -> tuple[dict, int]:
    """Drop interactive output blobs, keeping static images and text."""
    stripped = 0
    for cell in notebook.get("cells", []):
        for output in cell.get("outputs", []) or []:
            data = output.get("data")
            if not data:
                continue
            for mimetype in HEAVY_MIMETYPES:
                if mimetype in data:
                    del data[mimetype]
                    stripped += 1
    return notebook, stripped


def strip_ansi_outputs(notebook: dict) -> tuple[dict, int]:
    """Strip ANSI colour codes from stream and text/plain outputs."""
    escapes = 0
    for cell in notebook.get("cells", []):
        for output in cell.get("outputs", []) or []:
            if "text" in output:
                output["text"], hits = _strip_ansi_in_value(output["text"])
                escapes += hits
            data = output.get("data")
            if data and "text/plain" in data:
                data["text/plain"], hits = _strip_ansi_in_value(data["text/plain"])
                escapes += hits
    return notebook, escapes


def _plain_text_payload(output: dict) -> str | None:
    """Return text/plain from a display_data output, or None if not pure text."""
    if output.get("output_type") != "display_data":
        return None
    data = output.get("data") or {}
    if list(data.keys()) != ["text/plain"]:
        return None
    value = data["text/plain"]
    if isinstance(value, list):
        return "".join(value)
    return value if isinstance(value, str) else None


def coalesce_text_display_outputs(notebook: dict) -> tuple[dict, int]:
    """Merge consecutive pure-text ``display_data`` outputs into one stream.

    Rich / pretty-print often emits one ``display_data`` per ``print`` line.
    nbconvert then separates them with blank lines in the markdown. Merging
    restores a single contiguous block without re-executing the notebook.
    """
    merged_groups = 0
    for cell in notebook.get("cells", []):
        outputs = cell.get("outputs") or []
        if not outputs:
            continue
        new_outputs: list[dict] = []
        buffer: list[str] = []

        def flush() -> None:
            nonlocal buffer, merged_groups
            if not buffer:
                return
            if len(buffer) > 1:
                merged_groups += 1
            text = "".join(buffer)
            if not text.endswith("\n"):
                text += "\n"
            new_outputs.append(
                {"output_type": "stream", "name": "stdout", "text": text}
            )
            buffer = []

        for output in outputs:
            plain = _plain_text_payload(output)
            if plain is not None:
                buffer.append(plain)
            else:
                flush()
                new_outputs.append(output)
        flush()
        cell["outputs"] = new_outputs
    return notebook, merged_groups


_MYST_ADMONITION_RE = re.compile(
    r"^:::\{\s*(\w+)\s*\}\s*\n(.*?)^:::\s*$",
    re.MULTILINE | re.DOTALL,
)


def convert_myst_admonitions(markdown: str) -> tuple[str, int]:
    """Convert MyST ``:::{note}`` blocks to pymdown ``!!! note`` admonitions.

    mkdocstrings owns the ``:::`` fence; leftover MyST admonitions make the
    docs build fail with ``Could not collect '{note}'``.
    """
    converted = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal converted
        converted += 1
        kind = match.group(1)
        body = match.group(2).rstrip("\n")
        indented = "\n".join(
            f"    {line}" if line.strip() else "" for line in body.splitlines()
        )
        return f"!!! {kind}\n{indented}\n"

    return _MYST_ADMONITION_RE.sub(_repl, markdown), converted


def render(notebook_path: Path) -> None:
    notebook_path = notebook_path.resolve()
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / notebook_path.name
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook, stripped = strip_heavy_outputs(notebook)
        notebook, coalesced = coalesce_text_display_outputs(notebook)
        notebook, ansi = strip_ansi_outputs(notebook)
        staged.write_text(json.dumps(notebook), encoding="utf-8")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "nbconvert",
                "--to",
                "markdown",
                "--output-dir",
                str(notebook_path.parent),
                "--output",
                notebook_path.stem,
                str(staged),
            ],
            check=True,
            capture_output=True,
        )

    rendered = notebook_path.with_suffix(".md")
    md = rendered.read_text(encoding="utf-8")
    md, myst = convert_myst_admonitions(md)
    if myst:
        rendered.write_text(md, encoding="utf-8")
    size_kb = rendered.stat().st_size / 1024 if rendered.exists() else 0
    print(
        f"{notebook_path.relative_to(REPO_ROOT)}: "
        f"{size_kb:.0f} KB (stripped {stripped} interactive outputs, "
        f"coalesced {coalesced} text groups, {ansi} ANSI escapes, "
        f"{myst} MyST admonitions)"
    )


def main() -> None:
    notebooks = sorted(EXAMPLES.rglob("*.ipynb"))
    if not notebooks:
        raise SystemExit(f"no notebooks under {EXAMPLES}")

    # Remove previously rendered support directories so deleted figures do not
    # linger as orphans in the repository.
    for support in EXAMPLES.rglob("*_files"):
        if support.is_dir():
            shutil.rmtree(support)

    for notebook in notebooks:
        render(notebook)


if __name__ == "__main__":
    main()
