# Issue #639 — Plan: matplotlib backend; retire SeabornPlotBuilder; unify `backend=`

## Goal

Add `cellpy/plotting/backends/mpl.py` that renders the same summary `(frame, FigureSpec)` as plotly, delete `SeabornPlotBuilder`, and switch public `summary_plot` to `backend="plotly"|"matplotlib"` with `interactive=` as a `warn_once` alias (removal 2.1).

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../../../architecture-plan/cellpy2-plotting-redesign-plan.md) §3.1 / Phase 2 item 4; epic [`.issueflows/05-epics/epic567_plan.md`](../05-epics/epic567_plan.md) Stage 1 issue 4.
- Depends on #638 (merged): prepare → `FigureSpec` → `PlotlyBackend.render` is the interactive path; static path still uses `SeabornPlotBuilder` on the same prepared frame ([`plotting-prepare.md`](../04-designs-and-guides/plotting-prepare.md), [`plotting-backends.md`](../04-designs-and-guides/plotting-backends.md)).
- Oracle gate: `tests/test_figure_specs.py` matplotlib summary cases stay green **without** intentional `figure_specs.json` regen unless a proven structural change is required.
- Scope is **`summary_plot` only** — do not retarget `raw_plot` / `cycles_plot` / `cycle_info_plot` `interactive=` (Stage 2).
- Not yolo — static-output engine change; seaborn-loyalist surface.

### Prior art

- `SeabornPlotBuilder` — `cellpy/utils/plotutils.py` (~1002–1856, ~850 lines, 14 methods). Owns `sns.relplot` construction, formation facet columns, axis info dicts, legend convert, line hooks. Returns `sns_fig.figure` (already a matplotlib `Figure`).
- `summary_plot` orchestration (~2190–2218) — `interactive` → `PlotlyBackend` vs `SeabornPlotBuilder`.
- `SummaryPlotConfig.interactive` / seaborn styling fields (`seaborn_palette`, `seaborn_style`, `seaborn_line_hooks`) — keep styling knobs; replace the bool switch with `backend`.
- `PlotlyBackend.render(frame, spec)` — contract to mirror; mpl reads the same `spec.extras` (`prepared_data_info`, and any mpl-needed keys we add under `render` / top-level extras).
- `tests/figure_spec_support.py` — menu uses `interactive=True/False` and `needs_seaborn=True` for matplotlib summary cases; `_describe_matplotlib` already structural.
- `cellpy._deprecation.warn_once` + `DEPRECATIONS.md` — pattern used by `summary_plot_legacy` (#596).
- Architecture policy: two backends (`plotly` | `matplotlib`); seaborn = styling inside mpl, not a third backend name.
- Toolbox / graphify: nothing relevant.

## Approach

1. **`cellpy/plotting/backends/mpl.py` — `MatplotlibBackend`**
   - Implement `Backend.render(frame, spec) -> matplotlib.figure.Figure`.
   - **Mechanical port** of `SeabornPlotBuilder.build_plot` (+ helpers) into this class/module: keep `sns.relplot` / `sns.set_style` / `sns.set_palette` as the faceting+styling engine so oracle structure stays stable. Seaborn is not a public backend name.
   - Pull layout inputs from `spec.extras` (`prepared_data_info`, labels, row/col ids) rather than a parallel prepare path. Cell-bound bits still needed for titles/units can come from extras already populated by prepare (#638) or a small `extras['cell_name']` / capacity fields — avoid re-importing preparer logic.
   - Soft-fail if seaborn missing (same warn-and-return-data behaviour as today) so optional-deps story does not regress.

2. **`get_backend(name)`**
   - Add thin resolver in `cellpy/plotting/backends/__init__.py` (and optional re-export): `"plotly"` → `PlotlyBackend`, `"matplotlib"` → `MatplotlibBackend`; unknown → clear `ValueError`.

3. **Public `summary_plot` API**
   - Add `backend: Optional[str] = None`.
   - Change `interactive` default to `None` (sentinel). Resolution order:
     1. If `interactive is not None`: `warn_once("summary_plot(interactive=...)", 'backend="plotly"|"matplotlib"', removal="2.1")` and map `True→"plotly"`, `False→"matplotlib"` when `backend` is unset; if both set and conflict, prefer `backend` after warning (document in status).
     2. If `backend is None`: default `"plotly"`.
     3. Validate via `get_backend`.
   - Orchestration becomes: prepare → `get_backend(backend).render(frame, spec)`.
   - Update docstring examples to prefer `backend=`; note `interactive=` deprecated.
   - Mirror fields on `SummaryPlotConfig` (`backend`, `interactive` optional).
   - Regenerate / ensure `DEPRECATIONS.md` picks up the new `warn_once` name (run `uv run python -m cellpy._deprecation` or the project’s documented regen path when the call site is live).

4. **Delete `SeabornPlotBuilder`**
   - Remove the class from `plotutils.py`. No shim class. Grep tests/docs for the name and update.

5. **Tests / oracle harness**
   - Point `figure_spec_support` summary matplotlib cases at `backend="matplotlib"` (and plotly at `backend="plotly"`); keep `needs_seaborn` (or rename lightly) while mpl render still imports seaborn.
   - Add focused tests: `get_backend` smoke; `interactive=False/True` emits `DeprecationWarning` once and selects the right backend; `SeabornPlotBuilder` absent; oracle + `tests/test_plotutils_summary_plot.py` green (migrate call sites to `backend=` to avoid warning noise, plus 1–2 explicit interactive-deprecation cases).
   - Prefer **no** `figure_specs.json` regen; if matplotlib describe shape drifts unavoidably, regen in the same commit with a status note.

6. **Design notes**
   - Update [`plotting-backends.md`](../04-designs-and-guides/plotting-backends.md) and [`plotting-prepare.md`](../04-designs-and-guides/plotting-prepare.md): mpl owns static summary render; seaborn is styling-only; `backend=` is the public switch.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/backends/mpl.py` | **new** — `MatplotlibBackend` (ported seaborn builder) |
| `cellpy/plotting/backends/__init__.py` | export `MatplotlibBackend`, `get_backend` |
| `cellpy/plotting/__init__.py` | light re-exports / docstring |
| `cellpy/utils/plotutils.py` | `backend=` + interactive sentinel; delete `SeabornPlotBuilder`; thin orchestrate via `get_backend` |
| `DEPRECATIONS.md` | regen row for `summary_plot(interactive=...)` |
| `tests/figure_spec_support.py` | menu kwargs → `backend=` |
| `tests/test_plotutils_summary_plot.py` | migrate to `backend=`; add deprecation cases |
| `tests/test_summary_prepare.py` / new `tests/test_mpl_backend.py` | backend selection + builder-gone |
| `.issueflows/04-designs-and-guides/plotting-*.md` | document flip |

## Test strategy

```bash
uv sync --extra batch
MPLBACKEND=Agg uv run pytest tests/test_mpl_backend.py tests/test_summary_prepare.py tests/test_plotutils_summary_plot.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py
```

Parity focus: all summary families × matplotlib oracle entries; formation on/off; `interactive=` warn+map; no `SeabornPlotBuilder`.

## Open questions

1. **How much of seaborn stays inside `MatplotlibBackend`?** — **Recommend:** keep `sns.relplot` + style/palette helpers for this PR (oracle-stable “styling+facet engine”). Alternative: rewrite with plain `matplotlib` Axes immediately — higher blast radius; defer unless Accept insists.
2. **`interactive=` default sentinel** — **Recommend:** `interactive: Optional[bool] = None` so quiet default is `backend="plotly"` with no warning; only explicit `interactive=` warns. Alternative: keep `interactive=True` default and warn always — too noisy.
3. **Both `backend=` and `interactive=` passed** — **Recommend:** warn on `interactive=`, honour `backend=` if set. Alternative: error on conflict — harsher for transitional callers.
4. **Escape hatch to old builder** — **Recommend:** none (issue requires class deleted). Architecture’s `CELLPY_LEGACY_SUMMARY_PLOT` is obsolete once prepare path is the only prepare.

## Scope check

One Stage-1 slice: mpl backend module + API unify + delete seaborn builder. Fits a single PR. Follow-ups already in epic: Stage 2 ports (`cycles_plot`, etc.) reuse `backend=` / backends.
