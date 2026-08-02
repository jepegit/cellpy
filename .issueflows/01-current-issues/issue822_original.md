# Issue #822: Restore orchestrated batch.load (v1 flow on v3)

URL: https://github.com/jepegit/cellpy/issues/822

## Summary
Extend `cellpy.batch.load` so it again orchestrates the v1 notebook flow: journal autoload → DB → update → persist `.cellpy` + journal. `cellpy.utils.batch.load` stays a thin forwarder.

## Decisions
- Journal hit: `update()` with `AUTO` (not noop `link`)
- Persist `.cellpy` + journal by default; opt-out `save_cellpy=False`
- Map `force_raw_file` / `force_cellpy` → `LoadPolicy.source`; conflict with `policy=` raises
- `export_*`: accept, ignore, `warn_once`
- `drop_bad_cells=True`: drop `session.bad_cells`
- Raise on hard failures; per-cell soft errors via `accept_errors`
- `journal_dir=None` → cwd; optional override

## Acceptance
- [ ] `batch.load(name, project)` autoloads journal from cwd/`journal_dir` or builds from DB
- [ ] Returns populated Batch ready to plot
- [ ] Saves `.cellpy` + journal unless `save_cellpy=False`
- [ ] Essential tests for autoload, persist opt-out, force/policy conflict, drop_bad, export warn
