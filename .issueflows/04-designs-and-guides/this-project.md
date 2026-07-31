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
- **Paths in tests (cross-platform):** CI runs on Linux; local dev is often Windows. When
  tests or committed golden artifacts store file paths (e.g. `metrics.json` `source` fields),
  normalize to **forward slashes** — use `pathlib.Path(...).as_posix()` or
  `path.replace("\\", "/")`, not raw `str(path)` on Windows. Parquet/frame comparisons are
  unaffected; string metadata in JSON is where `\` vs `/` bites (see #433).
- **Agent usage docs (#682):** When a change alters the public `cellpy.get` /
  `CellpyCell` / `schema` / CLI surface that app-building agents rely on, update
  [`docs/getting_started/agents.md`](../../docs/getting_started/agents.md) and the
  short **Using cellpy (for agents)** section in root `AGENTS.md` in the same PR.
  Do not put long recipes inside the managed issue-flow block of `AGENTS.md`.
- TODO: Branch, commit, formatting, typing, or review conventions beyond the above.

## Entry points

- Main package: `cellpy/` (Python library).
- Issue-flow: `.issueflows/` (current issue under `01-current-issues/`).
- **cellpy 2 plans:** sibling repo `../cellpy-design-and-development/` (start at `CURRENT.md`; not `code-reviews/`).
- v2 epic: [cellpy-v2-epic.md](cellpy-v2-epic.md).
- cellpy-core integration: `../cellpy-core/.issueflows/04-designs-and-guides/`.

## Documentation

- Edit docs on **`master`** (same PRs as code). Do **not** use `v2-docs-stable`
  — that branch is retired (#768). See [docs-on-master.md](docs-on-master.md).
- Local preview: `uv run --group docs zensical serve` (more in
  `docs/contributing/developers_guide/dev_docs.md`).
- Read the Docs: **latest** ← `master`; **stable** ← latest release tag
  (e.g. `v2.1.0`).

## Release & version bump

**Strategy: git-tag derived** via `uv-dynamic-versioning` (see
[build-and-versioning.md](build-and-versioning.md) and
[release-procedure.md](release-procedure.md)).

- Do **not** edit a version into `pyproject.toml`.
- Latest tag → next pre-release on the same channel by default
  (e.g. after alphas, plan `v2.0.0rc1`; after soak, `v2.0.0`).
- Day-to-day cutter: source `.aliases`, then `release` (prints **last tag** +
  planned next post) or `release post` / `release patch` / `release vX.Y.Z…`.
- Create the tag **after** HISTORY is promoted and the tree is clean on
  `master` (prefer a PR for HISTORY; then cut the release):

```bash
git switch master && git pull --ff-only
# after HISTORY.md is merged:
gh release create v2.1.1.post4 --target master --generate-notes
# or: source .aliases && release post
```

- `/iflow-close bump` only **plans** the tag (records it in the status file);
  `/iflow-cleanup` (or a yolo close after merge) creates it on `master`.

## Non-goals / known limitations

- TODO: Scope boundaries, known caveats, or things this project intentionally does not do.
