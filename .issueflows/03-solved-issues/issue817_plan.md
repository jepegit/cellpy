# Issue #817 — Plan: honour `share_y` / `match_axes` on `spread_plot`

Status: **confirmed** (2026-08-04) — Accept; implement as written.

## Goal

Make collected summary **Group avg + Spread** honour `share_y` / `match_axes` the same way the non-spread path does after #804, so apps need not patch `yaxisN.matches` after `collection.plot`.

## Constraints

- Scope: collected summary Plotly path only (`summary_plotter` → `_cycles_plotter` → `sequence_plotter` → `spread_plot`). No prepare→PanelSpec migration.
- Keep #804 contracts: summary default independent; `share_y` wins over `match_axes`; non-empty `y_ranges` forces independent axes.
- Back-compat: `share_y=False` (default) must keep independent autorange on spread.
- Design doc: [plotting-collected.md](../04-designs-and-guides/plotting-collected.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| `_cycles_plotter` post-pass `if not match_axes: update_yaxes(matches=None)` | [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | Clears shared scale; never **sets** matches when True — fine for `px.line` facets, broken for `spread_plot` |
| `spread_plot` → `make_subplots(...)` without `shared_yaxes` | same file | Root cause: matches never established |
| `summary_plotter` → `_resolve_share_y` + `match_axes=share_y_resolved` | same file | Already resolves + forwards; reuse |
| `_apply_summary_y_ranges` / `_yaxis_key_for_variable` | same file | Title-based lookup works for spread (no `variable=` strips); today gated `if y_ranges and not spread` |
| `tests/test_collected_summary_axes.py` | tests | Extend with mean/std group frame + spread cases |
| Toolbox / graphify | — | None found (toolbox + grep; no `graphify-out/`) |

## Approach

1. **Centralise match apply in `_cycles_plotter` (Plotly).**  
   After layout chrome, replace one-sided clear with:
   - `match_axes is True` → `fig.update_yaxes(matches="y")` (link secondary facet rows to primary).
   - `match_axes is False` → keep today’s `matches=None` on y (and x as today).  
   This fixes spread without teaching `spread_plot` about share knobs, and makes the non-spread True path explicit (idempotent with `px.line` defaults).

2. **`y_ranges` on spread (coherence).**  
   Drop the `and not spread` guard so `_apply_summary_y_ranges` runs after `spread_plot` too. Lookup already falls back to y-axis titles (spread sets those from `y_label_mapper`). `summary_plotter` already forces `share_y_resolved=False` when `y_ranges` non-empty, so step 1 will not re-link over fixed limits.

3. **Docs.**  
   One bullet in `plotting-collected.md`: `kind="spread"` / `spread=True` honours the same `share_y` / `match_axes` / `y_ranges` rules as the line summary path.

4. **Out of scope:** matplotlib/seaborn spread; refactoring `spread_plot` onto prepare→spec; changing experimental status of spread.

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | Affirmative `matches="y"` when `match_axes`; apply `y_ranges` on spread branch |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | Note spread + share_y parity |
| [`tests/test_collected_summary_axes.py`](../../tests/test_collected_summary_axes.py) | Group-avg (`mean`/`std`) frame; spread + `share_y` True/False; spread + `y_ranges` |

## Test strategy

```bash
MPLBACKEND=Agg uv run pytest tests/test_collected_summary_axes.py -q
MPLBACKEND=Agg uv run pytest -m essential -q
```

- Synthetic long frame with `mean`/`std`/`group`/`variable`/`cycle` (no `cell`) so `summary_plotter` takes the group-averaged → spread path.
- Assert: `spread=True, share_y=True` → `fig.layout.yaxis2.matches == "y"`.
- Assert: `spread=True` default / `share_y=False` → matches cleared.
- Assert: `spread=True, share_y=True, y_ranges={ce: [0, 110]}` → independent axes + CE range set (no re-link).

## Open questions

None blocking — recommended defaults above match #804. Confirm Accept to proceed (`auto_build` will chain `/iflow-build`).
