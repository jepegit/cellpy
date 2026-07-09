# cellpy

## What this project is

TODO: Summarize the project in one short paragraph. Mention what it does, who it is for, and the main outcome it produces.

## Stack / runtime

- TODO: Primary language(s), runtime versions, package manager(s), and major frameworks.
- TODO: External services, CLIs, or local tools that agents should know about.

## How to run / test

```bash
uv sync
uv run pytest                              # full suite (default marker deselection in pyproject.toml)
uv run pytest -m essential                 # fast smoke — same subset as PR CI Tier 1
```

See also [testing-and-coverage.md](testing-and-coverage.md) and [ci-tiers.md](ci-tiers.md).

## Conventions

- **PR merge gate:** `.github/workflows/ci.yml` runs only `pytest -m essential` on Linux (`uv`).
  Full conda/platform matrix is in `ci-scheduled.yml` (weekly + manual).
- **`@pytest.mark.essential`:** Any test that must block a merge **must** carry this marker.
  Add it when the test guards read → step table → summary, cellpy-core parity, golden-fixture
  oracles, or other regressions you cannot leave to the scheduled run only. Keep the set
  small so Tier 1 stays fast. Document new suites in `tests/README.md` when they use goldens.
- TODO: Branch, commit, formatting, typing, or review conventions beyond the above.

## Entry points

- Main package: `cellpy/` (Python library).
- Issue-flow: `.issueflows/` (current issue under `01-current-issues/`).
- **cellpy 2 plans:** sibling repo `../architecture-plan/` (not `code-reviews/`).
- v2 epic: [cellpy-v2-epic.md](cellpy-v2-epic.md).
- cellpy-core integration: `../cellpy-core/.issueflows/04-designs-and-guides/`.

## Non-goals / known limitations

- TODO: Scope boundaries, known caveats, or things this project intentionally does not do.
