# Epic #896: v2.1.3 perceived batch-load speed

Anchor: https://github.com/jepegit/cellpy/issues/896
Status: confirmed

## Goal

Land the measured, patch-safe first-load / reopen cuts from #895 on milestone
`v.2.1.3`. Epoch done when every published child is closed and
`uv run pytest -m essential` is green on `master`.

## Constraints

- Default `auto_use_file_list` stays false; default executor stays `serial`.
- Do not implement #691 (v.2.2). Do not edit `cellpy_cookies`.
- Decisions are in each GitHub issue Spec; agents do not ask the maintainer.
- Loop budget: 2 fix-loops per child, then stop that child.

## Stage 1 — isolated (yolo-fit)

- Goal: four independent PRs that do not change defaults.

### Issue: Keep remote find -L stdout when exit status is 1

- Spec: see #897
- Goal: `files_only` rglob uses find stdout even when exit is 1
- Model: fast
- Depends on: none
- yolo: yes
- Published: #897

### Issue: Store v9 parquet zip members uncompressed

- Spec: see #898
- Goal: parquet members `ZIP_STORED`; v9 tests green
- Model: fast
- Depends on: none
- yolo: yes
- Published: #898

### Issue: search_for_files uses files_only / find -L

- Spec: see #899
- Goal: per-cell remote search passes `files_only=True`
- Model: fast
- Depends on: none
- yolo: yes
- Published: #899

### Issue: Docs: executor=threads and measured speed knobs

- Spec: see #903
- Goal: agents.md + load docstring document threads-for-reopen
- Model: fast
- Depends on: none
- yolo: yes
- Published: #903

## Stage 2 — first-load cuts

- Goal: dump-once wiring, fewer SFTP STATs, one HDF read on arbin_sql_h5.

### Issue: Wire auto_use_file_list in journal_from_db / find_files

- Spec: see #900
- Goal: flag True dumps once (project-scoped when project set); False unchanged
- Model: default
- Depends on: none
- yolo: no
- Published: #900

### Issue: OtherPath reuse credentialed fs; skip pre-copy is_file

- Spec: see #901
- Goal: one credentialed UPath per instance; from_raw does not STAT before copy
- Model: deep
- Depends on: none
- yolo: no
- Published: #901

### Issue: arbin_sql_h5 one HDF read; skip leftover legacy post-process

- Spec: see #902
- Goal: successful two-stage load selects HDF once; no row-wise datetime apply
- Model: deep
- Depends on: none
- yolo: no
- Published: #902

## Later (unstaged)

- Cookie defer pandas (`cellpy_cookies`, other repo).
- #691 project-folder fuzzy match (milestone v.2.2).
- SSH ControlMaster / parallel SFTP.
