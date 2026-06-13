# Plan for issue #354: update build procedure

## Goal
Replace `setup.py` + `requirements*.txt` + `MANIFEST.in` with one complete `pyproject.toml` (hatchling backend, git-tag dynamic versioning), manage everything through `uv`, and provide a Docker-based way to test the build locally. CI/conda migration is deliberately deferred to a follow-up.

## Decisions (confirmed)
- Build backend: `hatchling`.
- Versioning: git-tag dynamic via `uv-dynamic-versioning` (replaces `bumpver` + static `_version.py`).
- Scope: `pyproject.toml` + `uv` only (remove `setup.py`/`requirements*.txt`/`MANIFEST.in`) **plus** a Docker build test. Leave CI workflows and conda env files unchanged for a later issue.

## Approach
1. Rewrite `pyproject.toml` into a full project definition:
   - `[build-system]` -> hatchling + uv-dynamic-versioning.
   - `[project]` -> name, `dynamic = ["version"]`, description, readme, `requires-python = ">=3.13"`, license, authors, keywords, classifiers, and `dependencies` from the old `setup.py` (incl. `cellpycore @ git+...` and platform-marked `sqlalchemy-access`).
   - `[project.optional-dependencies]` -> `batch`, `fit`, `all`.
   - `[project.scripts]` -> `cellpy = "cellpy.cli:cli"`.
   - `[project.urls]`.
   - `[dependency-groups]` -> `dev` from old `requirements_dev.txt`.
   - `[tool.hatch.metadata] allow-direct-references = true` (for the git dep).
   - `[tool.hatch.version] source = "uv-dynamic-versioning"`; wheel `packages = ["cellpy"]`; sdist excludes mirroring the old `MANIFEST.in` prunes.
   - `[tool.uv-dynamic-versioning]` tolerant tag pattern (`default-unprefixed`) + fallback.
   - Keep `[tool.pytest.ini_options]`, `[tool.black]`, `[tool.coverage.*]`; drop `[tool.bumpver]`.
   - Package data (`*.conf`, `logging.json`, instrument configs, `utils/data/*.h5`) is picked up automatically by hatchling, so `MANIFEST.in` is dropped.
2. Runtime version: `cellpy/_version.py` derives `__version__` via `importlib.metadata`; `docs/conf.py` and `tasks.py` updated to match.
3. Regenerate `uv.lock` (`uv lock` + `uv sync`).
4. Docker local build test: `docker/Dockerfile.build-test` + `scripts/build_test.sh` build the wheel in a clean container, install it, and smoke-test import/CLI. `.dockerignore` keeps the context small but keeps `.git` (needed for versioning). Dev/build instructions added to `CONTRIBUTING.md`.
5. Remove legacy files: `setup.py`, `requirements.txt`, `requirements_dev.txt`, `MANIFEST.in`.

## Files touched
- `pyproject.toml` - full rewrite.
- `cellpy/_version.py` - version from installed metadata.
- `docs/conf.py`, `tasks.py` - version read via importlib.metadata.
- `docker/Dockerfile.build-test`, `.dockerignore`, `scripts/build_test.sh` - new local build test.
- `CONTRIBUTING.md` - uv-based dev setup + build instructions.
- Deleted: `setup.py`, `requirements.txt`, `requirements_dev.txt`, `MANIFEST.in`.
- `uv.lock` - regenerated.

## Test strategy / results
- `uv lock` + `uv sync` -> populated lockfile, environment installed. PASS.
- `uv build` -> sdist + wheel, version `1.0.3a13.post5.dev0+...` (derived from latest tag). PASS.
- `uv run python -c "import cellpy; print(cellpy.__version__)"` -> works. PASS.
- `uv run cellpy --help` -> entry point intact. PASS.
- `uv run pytest tests/test_prms.py` -> 6 passed; pytest reads config from `pyproject.toml`. PASS.
- Docker build test -> not run here (Docker daemon not running locally); Dockerfile/script provided for the user to run.

## Open questions / follow-ups
- Tag hygiene: existing tags are inconsistent (`v.0.3.0`, `v0.4.2`, `1.0.3a13`); standardize on `vX.Y.Z` going forward. The `default-unprefixed` pattern tolerates the old ones.
- Release flow becomes "tag, then `uv build`/publish" (update `invoke`/`tasks.py` release helpers in the CI follow-up).
- CI workflows + conda env files (`environment*.yml`, `github_actions_environment.yml`) and `docs/requirements_doc.txt` left as-is for a follow-up issue.

- [ ] Done
