# Issue #1109 plan: use src layout

## Goal

Move the installable package from `cellpy/` to `src/cellpy/` so the repo
matches the src convention (same shape as cellpy-core). Import path
`cellpy` and the CLI entry point stay the same.

## Constraints

- Public API and `cellpy = "cellpy.cli:cli"` do not change.
- Toolchain stays **uv** + hatchling + git-tag version
  ([this-project.md](../04-designs-and-guides/this-project.md)).
- Tests keep importing `cellpy` via the editable install (`uv sync`). Do not
  add `sys.path` hacks.
- Non-Python package data must still ship:
  `logging.json`, `parameters/.cellpy_prms_default.conf`,
  `readers/instruments/SQL Table IDs.txt`.
- Do not mix behaviour changes with the move.
- One PR is enough: this is one layout change, not several features.
  `/iflow-split` / `/iflow-epic` only if you want docs/CI follow-ups later.

### Prior art

- cellpy-core hatch wheel: `packages = ["src/cellpycore"]` in
  `../cellpy-core/pyproject.toml` — **mirror**.
- Current wheel: `packages = ["cellpy"]` in
  [`pyproject.toml`](../../pyproject.toml) — **replace**.
- Coverage omit uses `cellpy/libs/*` etc. — **update** to `src/cellpy/...`.
- Toolbox: nothing for a tree move (`00-tools/` is AST scanners).
- Graph: no `graphify-out/` in this worktree checkout.

## Approach

1. **`git mv cellpy src/cellpy`.** Keep history. Create `src/` only for this
   package (do not move `tests/`, `docs/`, `examples/`).
2. **Hatch.** Set
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/cellpy"]
   ```
   Confirm `uv build` / `uv sync` still installs `import cellpy` and
   `cellpy --help`. If hatchling drops the data files, add a
   `force-include` for the three files above.
3. **Tool paths.** Update `[tool.coverage.run]` `source` / `omit` to
   `src/cellpy`. Grep workflows, scripts, and Cursor Cloud notes for
   `flake8 cellpy`, `black … cellpy`, and path filters `cellpy/**`
   (known: `.github/workflows/benchmarks.yml`) and point them at
   `src/cellpy`.
4. **Docs / brief.** `this-project.md` entry point line
   (`Main package: cellpy/`) → `src/cellpy/`. Short CONTRIBUTING /
   developers_guide mention if they describe the tree. Do not rewrite
   GitHub URLs that are not filesystem paths.
5. **Sanity.** `uv sync` then `uv run pytest -m essential`. If that is
   green, run the full `uv run pytest` before close.
6. **Design note** (during build):
   `.issueflows/04-designs-and-guides/src-layout.md` — hatch stanza,
   data files, why tests stay at repo-root `tests/`.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/` → `src/cellpy/` | `git mv` |
| `pyproject.toml` | hatch `packages`, coverage paths |
| `.github/workflows/benchmarks.yml` | path filters `src/cellpy/**` |
| other CI / lint path hits from grep | same |
| `.issueflows/04-designs-and-guides/this-project.md` | package path |
| `.issueflows/04-designs-and-guides/src-layout.md` | **New.** |
| CONTRIBUTING / `docs/contributing/…` | tree description if present |

## Test strategy

```bash
uv sync
uv run pytest -m essential
uv run pytest
```

No new behavioural tests. Optional: one assert that
`importlib.resources` (or `files("cellpy")`) can open
`.cellpy_prms_default.conf` after the move.

## Open questions

None. Default: hatch `packages = ["src/cellpy"]` like cellpy-core, not
a second top-level name.
