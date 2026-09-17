# Issue #1023 — plan (iteration 11: glossary)

## Goal

Add a scientist-facing glossary that maps battery-science vocabulary onto the
names cellpy actually uses, then wire it into navigation and the pages a
reader is already on. One focused PR. Issue stays open for later iterations.

## Constraints

- Docs-only. No product-code, schema, or CLI changes.
- Do not redo pages shipped in #1024–#1035 (`troubleshooting.md`,
  `guides/units.md`, `guides/plotting.md`, `guides/batch_database.md`,
  `reference/cli.md`, `guides/exporting.md`, `reference/summary_columns.md`,
  `guides/step_table.md`, `getting_started/first_hour.md`, `how_do_i.md`
  as a whole). New links *into* those pages are fine.
- Out of this PR: tutorial-notebook render pass (`examples/*.ipynb` +
  `dev/render_example_notebooks.py`); experienced-Python pass (typing,
  extending, plugin surface). Those stay on the open issue.
- Every identifier and unit string must be checked against source or
  executed against bundled example data — no hoped-for names.
- Writing: task-first, scientist with limited Python. No unexplained idioms.
- Docs live on `master` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).
- Docs build must stay link-clean.

### Prior art

- Toolbox (`00-tools/`): nothing docs-related.
- Graph: `graphify-out/` not present in this worktree — skipped.
- Existing term coverage (link, do not duplicate):
  - [docs/guides/units.md](../../docs/guides/units.md) — mass / area / nom_cap / gravimetric–areal–absolute.
  - [docs/reference/summary_columns.md](../../docs/reference/summary_columns.md) — per-column summary meanings.
  - [docs/guides/step_table.md](../../docs/guides/step_table.md) — step types and `c_rate`.
  - [docs/fundamentals/data_structure.md](../../docs/fundamentals/data_structure.md) — `CellpyCell` / `Data` / frames / `c.schema`.
  - [docs/how_do_i.md](../../docs/how_do_i.md) — already has “know what a summary column means?”.
  - [docs/other/header_migration_map.md](../../docs/other/header_migration_map.md) — 1.x → 2.x header strings, not battery vocab.
- Convention: one new markdown page + `zensical.toml` nav entry + cross-links
  from the pages the persona is already on (same pattern as #1024–#1035).

## Approach

Persona / trigger: battery scientist who knows “coulombic efficiency”,
“C-rate”, “areal capacity”, “IR”, “OCV”, “step”, “SOC” and is staring at
`c.data.summary` / `c.schema` names.

New page `docs/fundamentals/glossary.md` under Concepts (vocabulary, not API
reference). Each entry is: **lab term → cellpy name(s) → one-line meaning →
link** to the page that already explains it.

Seed list (trim or add only after checking source / `c.schema` /
`example_data.raw_file()`):

| Lab term | Likely cellpy landing |
|---|---|
| cycle | `cycle_num` (`c.schema`) |
| step | `step` / `step_type` / step table |
| charge / discharge / rest | `step_type` values the classifier actually emits |
| OCV | `get_ocv`, rest-after-charge/discharge |
| coulombic efficiency | `coulombic_efficiency` (+ inversion note → troubleshooting) |
| C-rate | `c_rate` / `nominal_capacity` |
| gravimetric / areal / specific / absolute | suffix family + `guides/units.md` |
| IR / internal resistance | `ir_charge` / `ir_discharge` |
| mass / loading / area | `mass=`, `area=` on `get` |
| raw / steps / summary | the three frames |
| ICA / DVA | `cellpy.ica` (`dqdv` / `dvdq`) |
| batch / journal | `batch.load` / journal JSON |
| CellpyCell / Data / schema | objects, not lab terms — short block at top |
| SOC / DOD | only if cellpy has a real name; otherwise “not a column — compute from capacity” |

No invented columns. If a lab term has no cellpy object, say so in one
sentence rather than stretching a nearby name.

Wire-in:

- `zensical.toml` Concepts nav, after data structure.
- `docs/fundamentals/index.md` bullet.
- `docs/how_do_i.md` one question (“…look up what cellpy calls X?”).
- One-line “see also” on `data_structure.md` and `guides/units.md`.

## Files to touch

- `docs/fundamentals/glossary.md` — new page.
- `zensical.toml` — Concepts nav entry.
- `docs/fundamentals/index.md` — link.
- `docs/how_do_i.md` — one index question + link.
- `docs/fundamentals/data_structure.md` — see-also.
- `docs/guides/units.md` — see-also.
- `HISTORY.md` — Unreleased docs bullet (close step).

## Test strategy

- Execute any snippet on the new page against `example_data.raw_file()`
  (`uv run`).
- `uv run --group docs zensical build` — no broken links / missing anchors.
- `uv run pytest -m essential` — docs-only change; expect existing suite green.
  No new pytest.

## Open questions

1. **This iteration = glossary?** Recommended yes. Alternative remaining
   passes (notebooks, experienced-Python) wait for later PRs on the same
   open issue.
2. **Placement:** Concepts (`fundamentals/glossary.md`) vs Reference.
   Recommended Concepts.
