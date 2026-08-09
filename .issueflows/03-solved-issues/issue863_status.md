# Status — Issue #863

- [x] Done

## What's done

- Investigated `collect_ica` / `ica_plotter` / `Collection._FAMILY` / `render_collected` end to
  end to establish the mirror pattern for DVA.
- Identified the resolution-knob subtlety: `dqdv` uses `voltage_resolution`, `dvdq` uses
  `capacity_resolution`.
- Plan written (`issue863_plan.md`), accepted.
- `cellpy/collect/options.py::IcaOptions` — added `capacity_resolution` field (shared by ICA
  and DVA, each forwarding only its own knob).
- New `cellpy/collect/dva.py::collect_dva` — mirrors `collect_ica`, per-cell cycle isolation,
  `kind="dva"`, forwards `capacity_resolution` to `ica.dvdq`.
- `cellpy/collect/collector.py::dva_collector` convenience wrapper.
- Exported `collect_dva` / `dva_collector` from `cellpy/collect/__init__.py`.
- `cellpy/collect/collection.py::Collection._FAMILY["dva"] = "dva"`.
- `cellpy/plotting/collected.py`: new `dva_plotter` (mirrors `ica_plotter`, x=capacity/y=dvdq),
  wired into `render_collected`'s `family_kind == "dva"` branch, docstring updated.
- New `tests/test_collect_dva.py` (5 tests): specced frame, `Collection.kind`, resolution-knob
  regression guard (`capacity_resolution` reaches `dvdq`, not `voltage_resolution`), `_FAMILY`
  wiring regression guard, `fig_pr_cycle` layout.
- `uv run pytest tests/test_collect_dva.py` (5 passed), related collect/ICA/plotting tests
  (70 passed), and the full `uv run pytest -m essential` merge gate (703 passed, 1 skipped,
  2 xfailed, 1 xpassed — no regressions) all green with `MPLBACKEND=Agg`.
- `black --diff` / `flake8` on touched/new files: only pre-existing, unrelated findings
  (line-length config mismatch; fixture-shadowing F811 identical to `test_collectors.py`;
  pre-existing unused `field` import in `options.py`); nothing new from this change.

## Remaining work

None.
