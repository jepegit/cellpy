# Issue #682 plan: chapter for agents

## Goal

Give coding agents a discoverable, example-heavy guide for **using cellpy as a library** (primary persona: researcher building a small app/GUI), plus a maintenance hook so future API work updates that guide.

## Constraints

- Keep root `AGENTS.md` lean: do not edit the managed issue-flow block; add a short pointer section after `<!-- END issue-flow (managed) -->`.
- Prefer progressive disclosure (agents.md convention): essentials + link to a fuller chapter, not a 500-line dump in `AGENTS.md`.
- Docs-only change; no API / behaviour changes.
- Match existing MkDocs style under `docs/getting_started/`.

### Prior art

- Root [`AGENTS.md`](../../../AGENTS.md) — issue-flow managed block + Cursor Cloud notes; natural discoverability hook.
- [`docs/getting_started/basic_usage.md`](../../../docs/getting_started/basic_usage.md) — human-oriented load/inspect examples (reuse patterns, don’t duplicate wholesale).
- [`docs/fundamentals/data_structure.md`](../../../docs/fundamentals/data_structure.md) — `CellpyCell` / `schema` / frames.
- [`cellpy/utils/example_data.py`](../../../cellpy/utils/example_data.py) — `raw_file()`, `cellpy_file()` for offline-friendly agent demos.
- [`.issueflows/04-designs-and-guides/this-project.md`](../04-designs-and-guides/this-project.md) — place for “update agent docs when …” rule.
- Web convention ([agents.md](https://agents.md/)): root `AGENTS.md`, keep ≤~150 lines of actionable guidance, link out for depth.

## Approach

1. Add `docs/getting_started/agents.md` — agent chapter: product shape, install/run, core objects, load → schema → export recipes, GUI/app skeleton tips, pitfalls, links.
2. Wire into `docs/getting_started/index.md` (and a one-line mention on developers guide if useful).
3. Add a short **Using cellpy (for agents)** section in root `AGENTS.md` after the managed block that points at that page and lists 5–10 copy-paste commands / API bullets.
4. Update `this-project.md` Conventions: when public load/get/save/schema/CLI surface changes, update `docs/getting_started/agents.md` (+ the `AGENTS.md` pointer if commands change).

## Files to touch

| Path | Change |
| --- | --- |
| `docs/getting_started/agents.md` | **New** — full agent chapter |
| `docs/getting_started/index.md` | Link the new page |
| `AGENTS.md` | Short discoverability section after managed block |
| `.issueflows/04-designs-and-guides/this-project.md` | Maintenance rule for agent docs |
| `.issueflows/01-current-issues/issue682_status.md` | Status |

## Test strategy

- Docs-only: no new pytest.
- Preflight already green: `uv run pytest -m essential`.
- Spot-check that example snippets match current v2 APIs (`cellpy.get`, `c.schema`, `c.data.*`, `example_data`).

## Open questions

- None for yolo scope — fuller Sphinx/MkDocs nav nesting or nested `AGENTS.md` deferred.
