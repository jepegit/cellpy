# Issue #1038 — plan

## Goal

Answer the issue: yes, `[db_cols]` in `cellpy.toml` is how you map cellpy's
internal names onto whatever headers your Excel sheet actually uses — and
make that obvious with a worked example. An old workbook whose columns were
renamed should work by editing those strings, not by renaming the sheet back.

## Constraints

- Docs (and maybe a one-line model docstring). No reader/code behaviour
  change unless we find a real mapping bug while writing the example.
- Do **not** hand-edit `configuration_reference.md` — it is generated
  (`uv run python -m cellpy.config.reference`). The generator uses only the
  **first line** of each section model's docstring.
- Keep the batch-database column table on the *default sheet names*
  (`cell`, `mass_active_material`, …). The remap story sits next to it, not
  instead of it.

### Prior art

- [`docs/guides/batch_database.md`](../../docs/guides/batch_database.md) —
  sheet layout and the one-liner that `[db_cols]` is configurable; no toml
  example, no “I renamed a column” walkthrough.
- [`docs/getting_started/configuration.md`](../../docs/getting_started/configuration.md)
  — example toml has `[paths]` / `[reader]` only.
- [`docs/getting_started/configuration_reference.md`](../../docs/getting_started/configuration_reference.md)
  `## db_cols` — key → default header table; no left-vs-right explanation.
- [`DbColsConfig`](../../cellpy/config/models.py) — left-hand keys are
  cellpy names; values are the Excel header strings.
- [`docs/how_do_i.md`](../../docs/how_do_i.md) — “set up the database”
  points at the guide; no “my column names differ / I renamed a column”.
- Toolbox + graph: none (`00-tools/` is AST/header scanners; no
  `GRAPH_REPORT.md`).

## Approach

1. **Confirm the mapping.** Key in `[db_cols]` = cellpy field
   (`cell_name`, `mass_active`, `file_name_indicator`, …). Value = exact
   header string in row 1 of the sheet. Defaults already match the example
   workbook (`cell_name = "cell"`).
2. **Worked toml** in `configuration.md` next to the existing example:

   ```toml
   [db_cols]
   cell_name = "sample"                 # sheet header used to be "cell"
   file_name_indicator = "raw_stem"
   mass_active = "mass_active_material" # default; omit if unchanged
   ```

3. **`batch_database.md`** — short subsection after “The columns that
   actually matter”: if you renamed (or never used) a default header, set
   `[db_cols]` rather than editing every notebook. Point at the toml
   example. Keep the existing missing-header warning note.
4. **`how_do_i.md`** — one question under “Work on many cells”:
   “…use a spreadsheet whose column names are not the defaults?”
5. **`DbColsConfig` docstring first line** — only if we can say the
   left/right rule in one sentence without breaking the generated table
   (optional; the how-to is the user-facing fix).
6. **Agents** — one line in `agents.md` / `AGENTS.md` only if the public
   “how do I point batch at my sheet” recipe changes (likely just the
   how-do-I link).

## Files to touch

- [`docs/getting_started/configuration.md`](../../docs/getting_started/configuration.md)
- [`docs/guides/batch_database.md`](../../docs/guides/batch_database.md)
- [`docs/how_do_i.md`](../../docs/how_do_i.md)
- Optionally [`cellpy/config/models.py`](../../cellpy/config/models.py)
  (`DbColsConfig.__doc__` first line) + regenerate the reference if that
  line changes.

## Test strategy

```bash
uv run pytest tests/test_config_secrets.py::test_configuration_reference_matches_the_models -m essential
uv run pytest -m essential
```

No new Python tests unless the docstring/reference is regenerated. Docs
preview locally with `uv run --group docs zensical serve` if a page looks
off.

## Open questions

- The issue does not name *which* column was renamed. The plan treats it
  as the general remap story. If you have the old and new header strings,
  put them in the example instead of the placeholders above.
