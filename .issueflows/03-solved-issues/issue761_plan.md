# Issue #761 — plan

## Goal

Custom loader load of a file missing a column declared in
`normal_headers_renaming_dict` fails at load time with a clear error that
names the missing vendor column. No more silent drop + later `KeyError`.

## Constraints

- One-PR, custom-loader path only. Do not redesign harmonize, do not invent
  NaN stand-in columns, do not change other instruments' `MUST_HAVE` lists.
- Fail loud: name the missing column(s). Match sibling TxtLoader `validate()`
  (maccor / neware / pec / batmo) and `hooks.py` (`LoaderError`).
- The existing xfail is not a usable contract as written: it expects
  `pytest.warns` **and** the column still present, but `_load_bad` wraps
  `from_raw` in `warnings.simplefilter("ignore")`, so a warn-only fix can
  never satisfy it. Rewrite the test to `pytest.raises`.
- After the fix, delete or invert
  `test_missing_required_column_omits_it_silently` (it pins the bug).
- `test_bad_fixtures.py` has no `essential` marker today. Mark the new
  raise-contract test `@pytest.mark.essential` so Tier 1 keeps the gap closed.
- Public `get` / schema / CLI surface unchanged → no `agents.md` update.

### Prior art

- `cellpy.readers.instruments.processors.post_processors.rename_headers` —
  `DataFrame.rename` ignores absent source names (the silent drop).
- `AutoLoader.validate` — no-op hook; runs after `_post_process` (so after
  rename). `maccor_txt` / `neware_txt` / `pec_csv` / `batmo_bdf` override it
  and `raise exceptions.IOError` on missing must-have **canonical** columns.
- `cellpy.readers.instruments.hooks` — `LoaderError` listing missing vendor
  columns (mirror this exception type).
- `cellpy.readers.instruments.harmonize` — declared-but-absent vendor columns
  are `logging.debug` then dropped. `_try_harmonized_raw_frame` swallows any
  exception and falls back to legacy. Default `native_schema=True` still
  calls `loader()` afterwards, so a `validate()` raise on custom still
  fails the load (legacy test path and default `get`).
- `tests/test_bad_fixtures.py` + `testdata/bad/custom_missing_column.csv` +
  `custom_instrument_001.yml` (`voltage_txt: "voltage"`).
- Toolbox (`00-tools/`): none for this.
- Graphify: skipped (no `graphify-out/` in this worktree).

## Approach

1. Implement `DataLoader.validate` on the custom loader. After rename, for
   every key in `config_params.normal_headers_renaming_dict`, require
   `headers_normal[key]` to be in `data.raw.columns`. Collect misses; if any,
   `raise LoaderError` naming the **vendor** header(s) (the dict values) so
   the message matches the file, e.g. `voltage`.
2. Do **not** put the check in shared `rename_headers`. That would apply to
   every AutoLoader config and could break instruments that declare optional
   columns. Custom yaml treats the dict as the load contract.
3. Leave `harmonize`'s debug-drop as-is this PR. Default `get` still hits
   `loader()` → `validate()`. Follow-up if we want harmonize to fail before
   the swallow-and-fallback.
4. Tests: one raise-contract test on the existing fixture (no `_load_bad`
   helper for that case — it would have to not swallow). Drop the silent-omit
   pin. Keep the other bad-fixture pins unchanged.

## Files to touch

- `cellpy/readers/instruments/custom.py` — `DataLoader.validate`.
- `tests/test_bad_fixtures.py` — replace the two missing-column tests; mark
  the new one `essential`.

## Test strategy

```bash
uv run pytest tests/test_bad_fixtures.py
uv run pytest -m essential
```

## Open questions

1. **Raise vs warn.** Recommend **raise `LoaderError`**. Issue allows either;
   sibling loaders raise; warn-only would stay invisible through `_load_bad`.
   Say Revise if you want `UserWarning` and a still-successful load instead.
2. **All declared columns vs a must-have subset.** Recommend **all keys in
   that yaml's `normal_headers_renaming_dict`**. Say Revise to restrict to
   voltage/current/cycle/time only.
