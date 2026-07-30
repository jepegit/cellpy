# Issue #786: list_instruments() still logs loader-probe warnings on every call

Source: https://github.com/jepegit/cellpy/issues/786

## Original issue text

## Problem
`cellpy.readers.data_structures.instrument_configurations()` is the right way to
discover loaders (it's what `print_instruments` uses), but for an app it has two
rough edges:

1. **It logs a `WARNING` per non-loader module on every call** — `config_declarations`,
   `contract`, `hooks`, `declarations`, `registry`, `testing`, and `custom`
   ("Missing instrument definition file"). A GUI calling it at startup has to
   bracket it with a log-level bump to keep the console clean.
2. **The result isn't display-ready** — ids like `maccor_txt` / `pec_csv` need a
   human label, and the raw file **suffix/extension** isn't returned alongside the
   models, so apps keep their own label + extension map.

## Suggestion
A quiet, app-facing helper, e.g.:

```python
cellpy.list_instruments()
# -> [{"id": "maccor_txt", "label": "Maccor (text)",
#      "models": ["one","two","three", ...], "suffixes": [".txt"]}, ...]
```

that (a) does not emit warnings for skipped/non-loader modules, and (b) includes a
human label and the raw suffix(es). This would let apps build an instrument picker
+ ingestion form directly from cellpy.


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy 2.1.0.post1. Full write-up with all items: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*

## Comments (curated summary)

- **Additional tasks**:
  - Make probe/discovery skips quiet: calling `cellpy.list_instruments()` (or `instrument_configurations()`) must not emit a `WARNING` per skipped non-loader module on every call (repro still fails on 2.1.1.post1).
- **Clarifications / constraints**:
  - The app-facing shape (`id` / `label` / `models` / `suffixes`) from the first #786 landing is **done** — do not rework labels/suffixes.
  - Warnings currently hit the **root** logger (`WARNING:root:`), so silencing only `logging.getLogger("cellpy")` is ineffective.
  - Preferred fixes (either OK): log expected discovery skips (no `DataLoader`, or `custom` with no definition file) at `DEBUG`; and/or have `list_instruments()` swallow probe failures so the public helper is quiet by contract.
  - Remaining pain points (metadata read, per-instrument schema, figure theming) stay in #791 / related issues — out of scope here.
- **Superseded / retracted**:
  - Original item (2) “result isn't display-ready” — solved by the shipped `list_instruments()` helper; this reopen is **warnings-only**.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-29._
