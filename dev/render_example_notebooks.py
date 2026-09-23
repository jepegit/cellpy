"""Render the example notebooks to committed markdown pages (#571).

The notebooks live in the top-level ``examples/`` folder — one maintained copy,
which is also what readers download. ``docs/examples/`` holds only what this
script generates: a markdown page per notebook, its figure directory, and any
``images/`` assets a notebook links to (#869).

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
show their code and text without a figure — readers who want the interactive
version download the ``.ipynb`` from ``examples/``.

If a notebook has Plotly MIME data but no ``image/png``, backfill static
renderings first (needs the ``batch`` extra for kaleido):

```shell
uv run --extra batch --group docs python dev/backfill_notebook_plotly_pngs.py
```

Pandas DataFrame ``text/html`` tables are kept (markdown allows embedded HTML
and Zensical renders them as real tables). Only scripty / plotly / oversized
HTML is dropped — stripping *all* ``text/html`` left only the ugly
``text/plain`` dataframe dumps.

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
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The notebooks (single maintained copy, and the download readers are pointed at).
SOURCE = REPO_ROOT / "examples"

#: Where the rendered pages land; contains nothing that is not generated.
OUTPUT = REPO_ROOT / "docs" / "examples"

#: Cookiecutter templates are Jinja sources, not tutorials — never rendered.
SKIP_DIRS = (".ipynb_checkpoints", "cellpy project template")

#: Author-supplied assets (screenshots) a notebook links to by relative path.
ASSET_DIR = "images"

#: Output types that embed an entire JS runtime per figure.
#: ``text/html`` is handled separately — pandas tables are kept.
HEAVY_MIMETYPES = (
    "application/vnd.plotly.v1+json",
    "application/javascript",
    "application/vnd.jupyter.widget-view+json",
)

#: Drop ``text/html`` larger than this (bytes); plotly blobs are multi-MB.
_HEAVY_HTML_BYTES = 100_000

#: Show at most this many body rows of a DataFrame table (#1023).
MAX_TABLE_ROWS = 10

#: Shorten text outputs (prints, reprs) longer than this many lines (#1023).
MAX_TEXT_LINES = 40

#: Where readers get the notebooks and their data.
GITHUB_EXAMPLES = "https://github.com/jepegit/cellpy/blob/master/examples"

#: Per-tutorial header injected under the H1 (#1023): what the reader learns
#: and which data it needs. Keyed by the notebook path relative to ``examples/``.
#: ``full_text: True`` keeps long text outputs uncut for that notebook.
TUTORIALS: dict[str, dict[str, object]] = {
    "01_loading_data.ipynb": {
        "learn": [
            "load one or several raw files into a cell object with `cellpy.get`",
            "look at the summary, step table and metadata",
            "save a `.cellpy` file, export to Excel/CSV, and load it again",
        ],
        "data": "the four `20210210_FC_01_cc_0*.res` Arbin files in `examples/data/`",
    },
    "02_Initial_data_inspection.ipynb": {
        "learn": [
            "open a saved cellpy file and check what it contains",
            "plot raw traces and per-cycle information",
            "draw the standard summary plots (capacity fade, efficiency)",
        ],
        "data": "`20210210_FC.cellpy` in `examples/data/` (made by the previous "
        "tutorial), or the bundled example data",
    },
    "03_capacity_vs_voltage.ipynb": {
        "learn": [
            "get capacity–voltage curves for chosen cycles with `get_cap`",
            "choose between the ways of splitting charge and discharge",
        ],
        "data": "the bundled example data (`cellpy.utils.example_data`), "
        "downloaded automatically",
    },
    "04_incremental_capacity_analysis.ipynb": {
        "learn": [
            "compute dQ/dV for selected cycles with `ica.dqdv`",
            "tune the smoothing and resolution",
            "compute dV/dQ with `ica.dvdq` and plot both",
        ],
        "data": "the bundled example data (`cellpy.utils.example_data`), "
        "downloaded automatically",
    },
    "05_GITT.ipynb": {
        "learn": [
            "find the GITT cycles in a test",
            "pick the relaxation steps out of the step table",
            "read off the (pseudo-)OCV points, plot them and save them",
        ],
        "data": "`20210210_FC.h5` in `examples/data/`",
    },
    "06_loading_different_formats.ipynb": {
        "learn": [
            "load PEC, Maccor and Neware files",
            "pick the right instrument name and model for your tester",
        ],
        "data": "the bundled example data (`cellpy.utils.example_data`), "
        "downloaded automatically",
    },
    "07_custom_loaders.ipynb": {
        # The printed YAML files are the point of this tutorial.
        "full_text": True,
        "learn": [
            "describe a new file layout in a YAML file",
            "load it with the `custom` and `local_instrument` loaders",
        ],
        "data": "the bundled example data (`cellpy.utils.example_data`), "
        "downloaded automatically",
    },
    "08_batmo_bdf.ipynb": {
        "learn": [
            "load a BatMo BDF CSV file with the `batmo_bdf` loader",
            "inspect it, plot voltage–capacity curves and export it",
        ],
        "data": "`batmo_bdf.csv` from the cellpy test data (`cellpy pull --tests`)",
    },
    "09_loading_pec_data.ipynb": {
        "learn": [
            "load a PEC CSV export with the `pec_csv` loader",
            "merge several PEC tests of the same cell",
        ],
        "data": "`pec.csv` and `pec_multiple_tests/` in `examples/data/` "
        "(falls back to the bundled example data)",
    },
    "batch_utility/cellpy_batch_processing.ipynb": {
        "learn": [
            "set up the database sheet the batch utility reads",
            "load and summarise many cells as one job",
            "compare summaries, cycles and ICA across cells",
        ],
        "data": "`cellpy_db.xlsx` and the files in `examples/batch_utility/data/`",
    },
    "templates/tutorial_templates.ipynb": {
        "learn": [
            "start a new analysis project from a cookiecutter template",
            "run the notebooks the template gives you",
        ],
        "data": "none — the template makes the project folder for you",
    },
}


def _html_as_str(value: str | list[str]) -> str:
    """Join a notebook HTML payload into one string."""
    if isinstance(value, list):
        return "".join(value)
    return value


def _is_keepable_html(html: str) -> bool:
    """Return True for lightweight table HTML worth embedding in markdown.

    Keeps pandas / Styler tables. Drops plotly widgets, script tags, and
    oversized blobs. Other small HTML (e.g. rich ``<pre>``) is also dropped so
    the existing text/plain coalescing path still applies.
    """
    lower = html.lower()
    if "<script" in lower or "plotly" in lower:
        return False
    # The CellpyCell rich repr: ~1000 lines of nested tables whose <h2> also
    # lands in the page's table of contents. The text/plain repr stays (#1023).
    if "cellpycell-object" in lower:
        return False
    if len(html) > _HEAVY_HTML_BYTES:
        return False
    return 'class="dataframe"' in html or "<table" in lower


_STYLE_TAG_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)


def prepare_dataframe_html(html: str) -> str:
    """Strip pandas scoped CSS and wrap the table for docs styling.

    The wrapper (``.cellpy-dataframe``) is styled in
    ``docs/stylesheets/extra.css`` for horizontal scroll and readable striping.
    """
    cleaned = _STYLE_TAG_RE.sub("", html).strip()
    if 'class="cellpy-dataframe"' in cleaned:
        return cleaned
    # Pandas wraps tables in a bare ``<div>`` — reuse that node as our wrapper.
    if cleaned.startswith("<div>") and cleaned.endswith("</div>"):
        cleaned = cleaned[len("<div>") : -len("</div>")].strip()
    cleaned, hidden = truncate_table_rows(cleaned)
    note = (
        f'\n<p class="cellpy-dataframe-note">… {hidden} more rows not shown '
        f"— run the notebook to see them all.</p>"
        if hidden
        else ""
    )
    return f'<div class="cellpy-dataframe">\n{cleaned}{note}\n</div>'


_TBODY_RE = re.compile(r"(<tbody>)(.*?)(</tbody>)", re.DOTALL | re.IGNORECASE)
_ROW_RE = re.compile(r"<tr\b.*?</tr>", re.DOTALL | re.IGNORECASE)


def truncate_table_rows(html: str, limit: int = MAX_TABLE_ROWS) -> tuple[str, int]:
    """Keep the first *limit* body rows of an HTML table; return the hidden count.

    A wall of numbers is not what a reader comes to a tutorial for, and one
    long table can make a page thousands of lines long (#1023).
    """
    hidden = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal hidden
        rows = _ROW_RE.findall(match.group(2))
        if len(rows) <= limit:
            return match.group(0)
        hidden += len(rows) - limit
        kept = "\n".join(rows[:limit])
        return f"{match.group(1)}\n{kept}\n{match.group(3)}"

    return _TBODY_RE.sub(_repl, html, count=1), hidden


def truncate_text(text: str, limit: int = MAX_TEXT_LINES) -> str:
    """Shorten a long text output to its first lines plus a marker."""
    lines = text.splitlines(keepends=True)
    if len(lines) <= limit:
        return text
    keep = limit - 5
    return "".join(lines[:keep]) + f"… ({len(lines) - keep} more lines)\n"


def truncate_text_outputs(notebook: dict) -> tuple[dict, int]:
    """Apply :func:`truncate_text` to stream and ``text/plain`` outputs."""
    shortened = 0
    for cell in notebook.get("cells", []):
        for output in cell.get("outputs", []) or []:
            targets = [(output, "text")]
            if output.get("data"):
                targets.append((output["data"], "text/plain"))
            for holder, key in targets:
                value = holder.get(key)
                if value is None:
                    continue
                text = "".join(value) if isinstance(value, list) else value
                short = truncate_text(text)
                if short != text:
                    holder[key] = short
                    shortened += 1
    return notebook, shortened


_IPYNB_LINK_RE = re.compile(r"\]\((\./)?([^)\s#]+?)\.ipynb(#[^)\s]*)?\)")


def rewrite_notebook_links(markdown: str, notebook_path: Path) -> tuple[str, int]:
    """Point links at sibling notebooks to their rendered pages (#1023).

    Notebooks link to each other as ``07_custom_loaders.ipynb``; the site has
    no ``.ipynb`` files, only the rendered ``.md`` pages. A link to a notebook
    that is not rendered goes to its copy on GitHub instead.
    """
    rewritten = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal rewritten
        target, anchor = match.group(2), match.group(3) or ""
        source = (notebook_path.parent / f"{target}.ipynb").resolve()
        rewritten += 1
        if source in {path.resolve() for path in notebooks()}:
            return f"]({target}.md{anchor})"
        rel = source.relative_to(SOURCE.resolve()).as_posix()
        return f"]({GITHUB_EXAMPLES}/{rel}{anchor})"

    return _IPYNB_LINK_RE.sub(_repl, markdown), rewritten


def tutorial_header(notebook_path: Path) -> str:
    """The "In this tutorial" box placed under the page title (#1023)."""
    rel = notebook_path.resolve().relative_to(SOURCE.resolve()).as_posix()
    meta = TUTORIALS.get(rel)
    if meta is None:
        return ""
    learn = "\n".join(f"    - {item}" for item in meta["learn"])
    return (
        '!!! abstract "In this tutorial"\n\n'
        "    You will learn how to:\n\n"
        f"{learn}\n\n"
        f"    **Data:** {meta['data']}.\n\n"
        f"    [:material-github: Open the notebook on GitHub]({GITHUB_EXAMPLES}/"
        f"{quote(rel)}){{ .md-button }} — or get every notebook and its data "
        "with `cellpy pull --examples`.\n"
    )


def insert_header(markdown: str, header: str) -> str:
    """Insert *header* right after the first H1 line (or at the top)."""
    if not header:
        return markdown
    lines = markdown.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[: index + 1] + ["", header] + lines[index + 1 :])
    return header + "\n" + markdown


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
    """Drop interactive output blobs, keeping static images, text, and tables.

    Pandas DataFrame HTML is retained so nbconvert can emit real ``<table>``
    markup instead of monospace ``text/plain`` dumps.
    """
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
            if "text/html" in data:
                html = _html_as_str(data["text/html"])
                if not _is_keepable_html(html):
                    del data["text/html"]
                    stripped += 1
                else:
                    data["text/html"] = prepare_dataframe_html(html)
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


def render(notebook_path: Path, output_dir: Path) -> None:
    notebook_path = notebook_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / notebook_path.name
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook, stripped = strip_heavy_outputs(notebook)
        notebook, coalesced = coalesce_text_display_outputs(notebook)
        notebook, ansi = strip_ansi_outputs(notebook)
        rel = notebook_path.relative_to(SOURCE.resolve()).as_posix()
        shortened = 0
        if not TUTORIALS.get(rel, {}).get("full_text"):
            notebook, shortened = truncate_text_outputs(notebook)
        staged.write_text(json.dumps(notebook), encoding="utf-8")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "nbconvert",
                "--to",
                "markdown",
                "--output-dir",
                str(output_dir),
                "--output",
                notebook_path.stem,
                str(staged),
            ],
            check=True,
            capture_output=True,
        )

    rendered = output_dir / f"{notebook_path.stem}.md"
    md = rendered.read_text(encoding="utf-8")
    md, myst = convert_myst_admonitions(md)
    md, links = rewrite_notebook_links(md, notebook_path)
    md = insert_header(md, tutorial_header(notebook_path))
    rendered.write_text(md, encoding="utf-8")

    # Screenshots the notebook links to relatively must sit beside the page too.
    assets = notebook_path.parent / ASSET_DIR
    if assets.is_dir():
        shutil.copytree(assets, output_dir / ASSET_DIR, dirs_exist_ok=True)

    size_kb = rendered.stat().st_size / 1024 if rendered.exists() else 0
    print(
        f"{notebook_path.relative_to(REPO_ROOT)} -> "
        f"{rendered.relative_to(REPO_ROOT)}: "
        f"{size_kb:.0f} KB (stripped {stripped} interactive outputs, "
        f"coalesced {coalesced} text groups, {ansi} ANSI escapes, "
        f"{myst} MyST admonitions, shortened {shortened} text outputs, "
        f"rewrote {links} notebook links)"
    )


def notebooks() -> list[Path]:
    """Every tutorial notebook under :data:`SOURCE`, in a stable order."""
    return sorted(
        path
        for path in SOURCE.rglob("*.ipynb")
        if not any(part in SKIP_DIRS for part in path.parts)
    )


def main() -> None:
    found = notebooks()
    if not found:
        raise SystemExit(f"no notebooks under {SOURCE}")

    # Remove previously rendered support directories so deleted figures do not
    # linger as orphans in the repository.
    for support in OUTPUT.rglob("*_files"):
        if support.is_dir():
            shutil.rmtree(support)

    for notebook in found:
        render(notebook, OUTPUT / notebook.parent.relative_to(SOURCE))


if __name__ == "__main__":
    main()
