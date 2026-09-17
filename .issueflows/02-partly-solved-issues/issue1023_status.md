# Issue #1023 — status

- [ ] Done

Issue stays open. Iteration 11 (glossary) ships in this PR (`Refs #1023`).

## What's done

- Captured #1023; plan accepted (iteration 11 = glossary).
- `docs/fundamentals/glossary.md` — lab term → cellpy name → link.
  Names checked against `c.schema` / `example_data.raw_file()`.
- Nav + links: `zensical.toml`, `docs/fundamentals/index.md`,
  `docs/how_do_i.md`, `docs/fundamentals/data_structure.md`,
  `docs/guides/units.md`.
- Snippet executed. `uv run --group docs zensical build` — No issues found.
- `uv run pytest -m essential` — 861 passed, 70 skipped.
- HISTORY Unreleased bullet.

## Remaining work

- Later iterations on this open issue: tutorial-notebook pass;
  experienced-Python pass (typing / extending / plugins).
- Essential review: no tests added or changed.
