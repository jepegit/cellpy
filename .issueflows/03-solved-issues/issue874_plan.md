# Issue #874 — Plan: validate collected `layout=` / `kind=`

Status: **confirmed** (2026-08-10) — Accept; Q1=(A) alias `layout="film"`; Q2=validate unknown `method=` too.

## Goal

Stop `resolve_collected_layout_kind` (and thus `Collection.plot` / `collected_plot`) from silently mapping unknown `layout=` strings to the line/`fig_pr_cell` path. Fail loud on garbage; optionally treat the common `layout="film"` footgun as `kind="film"`. Document `kind=` on `Collection.plot`.

## Constraints

- Patch-scoped (milestone **v.2.1.2**): resolver + docs/tests only — no renderer / backend rewrite.
- Public API stays `layout=` / `kind=` / legacy `method`/`plot_type`/`spread`.
- Prefer **raise** over warn+coerce for unknown layout/kind (silent wrong figure is the bug). ICA `direction=` still warns+coerces — different footgun; do not change that path here.
- Design doc: [plotting-collected.md](../04-designs-and-guides/plotting-collected.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| `resolve_collected_layout_kind` | [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) ~L1710 | Bug: `_LAYOUT_TO_METHOD.get(layout, "fig_pr_cell")` default |
| `_METHOD_TO_LAYOUT` / `_LAYOUT_TO_METHOD` | same file ~L1696 | Canonical allowed layout/method sets; `film` is method→layout only |
| `collected_plot` docstring | same file | Already documents `layout` / `kind` values |
| `Collection.plot` docstring | [`cellpy/collect/collection.py`](../../cellpy/collect/collection.py) | Mentions `layout=` only — miss that bit `kind=` |
| `plotting-collected.md` | designs | Maps `film` → `kind="film"`; no validation note |
| ICA invalid `direction` | collected.py (`ica_plotter`) | warn+coerce — **do not mirror** for layout/kind |
| Toolbox / graphify | — | None needed (pure resolver) |

## Approach

1. **Canonical sets** (module-level frozensets or reuse map keys):
   - layouts: `per_cell`, `per_cycle`, `summary`
   - kinds: `line`, `film`, `spread`
   - methods (legacy, when provided): `fig_pr_cell`, `fig_pr_cycle`, `film`, `summary`

2. **`layout="film"` alias** (recommended — see Open Q1): if `layout == "film"`:
   - treat as request for `kind="film"` / `layout="per_cell"`;
   - if `kind` is already set and ≠ `"film"`, raise `ValueError` (conflict);
   - then continue normal resolution.

3. **Validate after defaults resolved** (or validate only user-provided non-`None` args before defaults — same effect if alias runs first):
   - unknown `layout` → `ValueError` listing allowed layouts (+ note that `film` is a `kind`);
   - unknown `kind` → `ValueError` listing allowed kinds;
   - unknown explicit `method`/`plot_type` → `ValueError` listing allowed methods (keeps legacy path honest);
   - remove the silent `.get(layout, "fig_pr_cell")` fallback — after validation, `.get` is unnecessary / use direct map.

4. **Docs**
   - `Collection.plot`: mention `kind=` (`line` / `film` / `spread`) alongside `layout=`.
   - Bullet in `plotting-collected.md`: unknown layout/kind raise; `layout="film"` → `kind="film"` (if Q1 accepted).

5. **Tests** — pure unit tests on `resolve_collected_layout_kind` (no figure / kaleido).

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | Alias + validate in `resolve_collected_layout_kind`; drop silent layout default |
| [`cellpy/collect/collection.py`](../../cellpy/collect/collection.py) | Docstring: `kind=` |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | Validation / film-alias note |
| `tests/test_resolve_collected_layout_kind.py` (new) | Valid / alias / raise cases; mark `essential` if cheap |

## Test strategy

```bash
MPLBACKEND=Agg uv run pytest tests/test_resolve_collected_layout_kind.py -q
MPLBACKEND=Agg uv run pytest -m essential -q
```

- Valid: `layout="per_cell"`, `kind="film"`, `method="fig_pr_cycle"`, `spread=True` → expected triples.
- Alias: `layout="film"` → `("per_cell", "film", "film")` (if Q1 yes).
- Raise: `layout="totally_bogus"`, `kind="nope"`, conflict `layout="film", kind="line"`.
- Regression: `kind="film"` unchanged; default (all None) still `per_cell` / `line` / `fig_pr_cell`.

## Open questions

1. **`layout="film"`** — **(A) alias → `kind="film"`** (recommend; matches issue suggestion 2 + `_METHOD_TO_LAYOUT`) vs **(B) raise** like any other unknown layout (strict; forces callers to use `kind=`)?
2. **Legacy `method=`** — validate unknown methods too (**recommend yes**) or only `layout`/`kind`?
