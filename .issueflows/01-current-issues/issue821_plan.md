# Issue #821 — Plan: ICA collected plot direction (line + `both`)

Status: **draft** — awaiting Accept / Revise / Abort.

## Goal

Make collected ICA **line** plots honour `direction="charge"|"discharge"|"both"`: filter half-cycles for single-direction figures, overlay both without silent coerce-to-charge or spurious joins between lobes.

## Constraints

- Scope: collected ICA path (`ica_plotter` → `_cycles_plotter` → `sequence_plotter` / `_select_direction`). Do **not** rework single-cell `ica_plot` prepare→render (already supports `both` via `_render_ica_dva`).
- Keep collected default `direction="charge"` (current `ica_plotter` default) unless Accept says otherwise — apps already assume Charge|Discharge toggle.
- Prefer `logging.warning` over `print` for invalid direction.
- Design docs: [plotting-collected.md](../04-designs-and-guides/plotting-collected.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| `_select_direction` | [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | Filters charge/discharge; string `"both"` currently matches nothing → empty frame |
| `sequence_plotter` only filters when `method=="film"` | same file ~L460 | Root cause for line / `fig_pr_cell` no-op |
| `ica_plotter` rejects anything ≠ charge/discharge via `print` | same file ~L1533 | Blocks `both`; replace with warn + allow `both` |
| Single-cell `_render_ica_dva` one trace per `(cycle, direction)` | [`backends/plotly.py`](../../cellpy/plotting/backends/plotly.py) | Pattern for no join; collected still uses `px.line` |
| `sequence_plotter` docstring already lists `"both"` | collected.py | Intent existed; never wired for ICA lines |
| Toolbox / graphify | — | None found |

## Approach

1. **`_select_direction`**  
   - If `direction == "both"` (case-normalize strip/lower), return frame unchanged.  
   - Keep numeric ±1 and string charge/discharge behaviour.  
   - Invalid values: leave to caller (ica_plotter) rather than silent filter-to-empty.

2. **`ica_plotter` validation**  
   - Allow `charge` / `discharge` / `both`.  
   - Else: `logging.warning(...)`, coerce to `"charge"` (no `print`).  
   - Docstring: document the three values.

3. **`sequence_plotter` — filter line layouts**  
   - After cycle filtering for `fig_pr_cell` / `film` **and** for `fig_pr_cycle`, call `_select_direction` when a `direction` column is present (or always — helper already no-ops if column missing).  
   - For `film`, keep existing histscale transforms after the filter (both = unfiltered film is OK / best-effort).

4. **`direction="both"` without joins (Plotly line)**  
   - When `direction=="both"` and `direction_col` in frame and backend plotly and method in `{fig_pr_cell, fig_pr_cycle}`: set `plotly_arguments["line_dash"] = direction_col` (or equivalent) so `px.line` builds separate traces per `(color, dash)` and half-cycles do not connect.  
   - Legend: cycle colour stays primary; dash distinguishes direction.  
   - Seaborn/matplotlib: best-effort filter-only for single direction; for both, leave unfiltered (document Plotly as supported for overlay).

5. **Docs**  
   - Bullet in `plotting-collected.md`: ICA `direction=` on `layout="per_cell"|"per_cycle"` and `kind="film"`; `both` → overlay with dash distinction on Plotly.

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | `_select_direction` both; filter line methods; `ica_plotter` allow both + warning; Plotly `line_dash` for both |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | ICA direction note |
| `tests/test_collected_ica_direction.py` (new) or extend nearby | Synthetic ICA long frame: charge / discharge / both for `collected_plot` / `ica_plotter` line layout |

## Test strategy

```bash
MPLBACKEND=Agg uv run pytest tests/test_collected_ica_direction.py -q
# or chosen file; mark essential if cheap
MPLBACKEND=Agg uv run pytest -m essential -q
```

- Synthetic tidy ICA frame (`cycle`, `direction`, `voltage`, `dqdv`, `cell`, …) with distinct charge vs discharge voltage ranges / dqdv peaks.  
- Assert charge-only and discharge-only figures differ (e.g. y-data max or trace y arrays).  
- Assert charge-only has no discharge-direction points in traces (no join to other lobe).  
- Assert `direction="both"` does not coerce (no warning path) and produces ≥2 dash styles or ≥2× traces vs single-direction.  
- Assert invalid direction emits a warning (caplog) and falls back to charge.

## Open questions

1. **Default for collected ICA** — keep `"charge"` (**recommend**) or flip to `"both"` like single-cell `ica_plot`?  
2. **`both` styling** — `line_dash` by direction on `px.line` (**recommend**) vs custom go.Scatter loop mirroring `_render_ica_dva` (heavier)?
