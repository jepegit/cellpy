"""Time find -L vs walk vs per-cell search_for_files.

    set SPEEDTEST_JOURNAL=path/to/journal.json
    set SPEEDTEST_PROJECT=YourProject
    set SPEEDTEST_EXT=h5
    python dev/speed-test-01/time_filefinder.py
"""

from __future__ import annotations

import logging
import shlex
import time

from _common import cell_label, journal_path, project_name, raw_extension, step

logging.basicConfig(level=logging.WARNING)

import cellpy.config as config
from cellpy.batch.journal import FILENAME, read_journal
from cellpy.internals.connections import OtherPath
from cellpy.readers import filefinder


def main() -> None:
    ext = raw_extension()
    project = project_name()
    journal = read_journal(journal_path())
    cells = list(journal.pages[FILENAME])
    label = cell_label(journal)
    root = OtherPath(config.paths.rawdatadir)
    proj = root / project
    print(
        f"n_cells={len(cells)}  ext={ext}  "
        f"auto_use_file_list={config.batch.auto_use_file_list}",
        flush=True,
    )

    cred = proj._upath_with_credentials()
    fs, remote_root = cred.fs, cred.path.rstrip("/") or "/"
    bulk = step("find -L project", lambda: proj._remote_find_l_file_paths(fs, remote_root))
    if bulk is None:
        print("  find -L returned None", flush=True)
    else:
        print(f"  n={len(bulk)}  *.{ext}={sum(1 for p in bulk if p.endswith('.' + ext))}", flush=True)

    orig = OtherPath._remote_rglob_from_find
    OtherPath._remote_rglob_from_find = lambda *a, **k: None
    try:
        walked = step(
            "walk project rglob files_only (find disabled)",
            lambda: list(proj.rglob(f"*.{ext}", files_only=True)),
        )
        print(f"  n={len(walked)}", flush=True)
    finally:
        OtherPath._remote_rglob_from_find = orig

    dumped = step(
        "find_in_raw_file_directory(project, ext)",
        lambda: filefinder.find_in_raw_file_directory(
            raw_file_dir=root, project_dir=project, extension=ext
        ),
    )
    print(f"  n={len(dumped)}", flush=True)

    raw, _ = filefinder.search_for_files(
        label, raw_extension=ext, raw_file_dir=root, file_list=dumped, with_prefix=True
    )
    print(f"  sample hits for first label: {len(raw)}", flush=True)

    def _search_list():
        hits = []
        for cell in cells:
            found, _ = filefinder.search_for_files(
                cell, raw_extension=ext, raw_file_dir=root, file_list=dumped, with_prefix=True
            )
            hits.append(len(found) if found else 0)
        return hits

    hits = step(f"{len(cells)}x search + file_list", _search_list)
    print(f"  hits={hits}", flush=True)

    def _search_proj():
        hits = []
        for cell in cells:
            found, _ = filefinder.search_for_files(
                cell, raw_extension=ext, raw_file_dir=proj, file_list=None
            )
            hits.append(len(found) if found else 0)
        return hits

    hits = step(f"{len(cells)}x search project, no list", _search_proj)
    print(f"  hits={hits}", flush=True)

    print("--- full rawdatadir ---", flush=True)
    root_cred = root._upath_with_credentials()
    cmd = f"find -L {shlex.quote(root_cred.path.rstrip('/') or '/')} -type f -print"
    t0 = time.perf_counter()
    _stdin, stdout, stderr = root_cred.fs.client.exec_command(cmd, timeout=300)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read()
    err = stderr.read()
    text = out.decode("utf-8", errors="replace") if isinstance(out, (bytes, bytearray)) else str(out)
    n = sum(1 for line in text.splitlines() if line.strip())
    err_s = err.decode("utf-8", errors="replace") if isinstance(err, (bytes, bytearray)) else str(err)
    print(
        f"{time.perf_counter() - t0:8.3f}s  raw find -L full tree  "
        f"exit={exit_status}  n={n}  stderr_lines={len(err_s.splitlines())}",
        flush=True,
    )

    dumped_all = step(
        "find_in_raw_file_directory(full, ext)",
        lambda: filefinder.find_in_raw_file_directory(raw_file_dir=root, extension=ext),
    )
    print(f"  n={len(dumped_all)}", flush=True)

    def _search_full():
        hits = []
        for cell in cells:
            found, _ = filefinder.search_for_files(
                cell, raw_extension=ext, raw_file_dir=root, file_list=None
            )
            hits.append(len(found) if found else 0)
        return hits

    hits = step(f"{len(cells)}x search FULL rawdatadir, no list", _search_full)
    print(f"  hits={hits}", flush=True)


if __name__ == "__main__":
    main()
