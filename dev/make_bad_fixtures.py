"""Generate the deliberately-broken 'bad file' fixtures for #655.

Packages a small, deterministic set of malformed files so the test-suite can
pin how cellpy behaves on pathological input (graceful failure / filtering vs
crash / silent corruption) instead of relying only on synthetic in-test hooks.

All variants are derived from the committed ``custom_data_001.csv`` (the custom
CSV loader, ``custom_instrument_001.yml``) so they parse through a real loader
path, but each isolates one defect. Output goes to ``testdata/bad/``.

Usage::

    uv run python dev/make_bad_fixtures.py            # (re)write fixtures
    uv run python dev/make_bad_fixtures.py --verify   # regenerate twice, assert identical

The generator is pure (fixed input slice + fixed transforms), so ``--verify``
regenerates to a temp dir and asserts byte-identical output.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "testdata" / "data" / "custom_data_001.csv"
OUT_DIR = REPO_ROOT / "testdata" / "bad"
ENCODING = "ISO-8859-1"

# custom_instrument_001.yml: 19 metadata rows, then header, then data rows (';').
SKIPROWS = 19
N_DATA_ROWS = 60  # keep fixtures tiny
SEP = ";"
VOLTAGE_COL = "voltage"
CYCLE_COL = "cycle"


def _read_slice() -> tuple[list[str], str, list[str]]:
    """Return (metadata_lines, header_line, data_lines) for the small slice."""
    text = SOURCE.read_text(encoding=ENCODING)
    lines = text.splitlines()
    metadata = lines[:SKIPROWS]
    header = lines[SKIPROWS]
    data = lines[SKIPROWS + 1 : SKIPROWS + 1 + N_DATA_ROWS]
    return metadata, header, data


def _write_bytes(path: Path, body: str) -> None:
    # newline="" => write the literal LF in `body` verbatim (no CRLF translation
    # on Windows), so fixtures are byte-identical across platforms.
    path.write_text(body, encoding=ENCODING, newline="")


def _write(path: Path, metadata: list[str], header: str, data: list[str]) -> None:
    _write_bytes(path, "\n".join([*metadata, header, *data]) + "\n")


def _cols(header: str) -> list[str]:
    return header.split(SEP)


def generate(out_dir: Path) -> list[Path]:
    """Write the base + four defect variants; return the paths written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata, header, data = _read_slice()
    cols = _cols(header)
    v_idx = cols.index(VOLTAGE_COL)
    c_idx = cols.index(CYCLE_COL)
    written: list[Path] = []

    # 0) clean small base — must load fine (sanity anchor for the contract).
    p = out_dir / "custom_good_small.csv"
    _write(p, metadata, header, data)
    written.append(p)

    # 1) embedded NaN (empty cell) and Inf in the voltage column.
    nan_inf = list(data)
    for i, value in ((3, ""), (7, "inf"), (11, "-inf")):
        parts = nan_inf[i].split(SEP)
        parts[v_idx] = value
        nan_inf[i] = SEP.join(parts)
    _write(out_dir / "custom_nan_inf.csv", metadata, header, nan_inf)
    written.append(out_dir / "custom_nan_inf.csv")

    # 2) missing cycle — deterministically block rows into cycles 1/2/3, then
    #    drop the whole cycle-2 block so cycle_index is non-contiguous (1, 3).
    blocked = []
    for row_idx, line in enumerate(data):
        parts = line.split(SEP)
        parts[c_idx] = str(1 + row_idx // 20)  # 0-19->1, 20-39->2, 40-59->3
        blocked.append(SEP.join(parts))
    missing_cycle = [
        line for line in blocked if line.split(SEP)[c_idx] != "2"
    ]
    _write(out_dir / "custom_missing_cycle.csv", metadata, header, missing_cycle)
    written.append(out_dir / "custom_missing_cycle.csv")

    # 3) truncated — cut the final data row mid-line (partial fields, no newline).
    truncated_body = "\n".join([*metadata, header, *data[:-1]]) + "\n"
    last = data[-1].split(SEP)
    truncated_body += SEP.join(last[: len(last) // 2])  # half a row, no newline
    _write_bytes(out_dir / "custom_truncated.csv", truncated_body)
    written.append(out_dir / "custom_truncated.csv")

    # 4) missing required column — drop the voltage column from header + rows.
    drop_header = SEP.join(c for j, c in enumerate(cols) if j != v_idx)
    drop_data = [
        SEP.join(p for j, p in enumerate(line.split(SEP)) if j != v_idx)
        for line in data
    ]
    _write(out_dir / "custom_missing_column.csv", metadata, drop_header, drop_data)
    written.append(out_dir / "custom_missing_column.csv")

    return written


def _verify() -> int:
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        pa = {p.name: p for p in generate(Path(a))}
        pb = {p.name: p for p in generate(Path(b))}
        assert pa.keys() == pb.keys()
        bad = [n for n in pa if not filecmp.cmp(pa[n], pb[n], shallow=False)]
        if bad:
            print(f"[verify] NOT identical: {bad}")
            return 1
        print(f"[verify] {len(pa)} bad fixtures byte-identical across two runs")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="regenerate twice, assert identical")
    args = parser.parse_args()
    if args.verify:
        return _verify()
    if not SOURCE.is_file():
        print(f"missing source: {SOURCE}", file=sys.stderr)
        return 1
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    written = generate(OUT_DIR)
    for p in written:
        print(f"wrote {p.relative_to(REPO_ROOT)} ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
