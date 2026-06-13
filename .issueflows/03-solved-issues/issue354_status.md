# Issue #354 status: update build procedure

- [x] Done

## What was done
- Rewrote `pyproject.toml` as the single build definition: hatchling backend,
  `[project]` metadata + dependencies, `batch`/`fit`/`all` extras, `cellpy` script
  entry point, `[dependency-groups].dev`, hatch wheel/sdist targets,
  `allow-direct-references` (for the cellpy-core git dep), and
  `uv-dynamic-versioning` (git-tag based). Dropped `[tool.bumpver]`.
- Switched runtime version to `importlib.metadata` (`cellpy/_version.py`), and updated
  `docs/conf.py` and `tasks.py` accordingly.
- Removed `setup.py`, `requirements.txt`, `requirements_dev.txt`, `MANIFEST.in`.
- Regenerated `uv.lock` (`uv lock` + `uv sync`).
- Added a Docker-based local build test (`docker/Dockerfile.build-test`,
  `.dockerignore`, `scripts/build_test.sh`) and documented build/dev usage in
  `CONTRIBUTING.md`.
- Recorded the design decision in `.issueflows/04-designs-and-guides/build-and-versioning.md`.

## Verification
- `uv lock` / `uv sync` — OK.
- `uv build` — sdist + wheel, version `1.0.3a13.post5.dev0+acd06d4c` (from git tag).
- `uv run pytest --ignore=tests/test_plotutils_summary_plot.py` — 447 passed, 17 skipped, 13 xfailed.
- `cellpy --help` + `import cellpy` — OK.
- Docker build test — `BUILD TEST OK` (`cellpy 1.0.3a13.post5.dev0+acd06d4c`).

## Follow-up (separate issue)
- Migrate CI workflows to uv; retire conda env files and `docs/requirements_doc.txt`.
- Standardize git tags on `vX.Y.Z`.
