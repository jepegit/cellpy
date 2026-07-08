# Issue #425 — Iterative fixes: get() docstring units

Interactive `/iflow-fix` session.

- [x] Done

## Iterative fixes log

- **2026-07-08** — Document `cellpy_units` defaults for `mass`, `nominal_capacity`, `loading`, and `area` in `cellpy.get()` docstring (`cellpy/readers/cellreader.py`). Clarifies default units (mg, mAh/g, cm**2), string-with-unit override via `_dump_cellpy_unit`, and `nom_cap_specifics` effect on nominal capacity unit.

- **2026-07-08** — Google docstring formatting cleanup in `cellreader.py`: fix typos/copy-paste errors (module docstring, `vacant`, `get()` Transferred Parameters), standardize section headers (`Examples:`, `Note:`, `Warning:`, `Parameters:` → `Args:`), replace `(string):` with `(str):`, align `loadcell()` unit docs and `load()` selector type.
