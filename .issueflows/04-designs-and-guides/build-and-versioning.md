# Build and versioning

Context: issue #354 ("update build procedure").

## Decision
- Packaging is defined entirely in `pyproject.toml` using the **hatchling** build backend.
- The package **version is derived from the latest git tag** via `uv-dynamic-versioning`
  (`[tool.hatch.version] source = "uv-dynamic-versioning"`). There is no hand-edited
  version string anymore; `cellpy/_version.py` reads it back through
  `importlib.metadata.version("cellpy")` at runtime.
- Dependencies and the dev toolchain are managed with **uv** (`uv.lock`,
  `[project.dependencies]`, `[project.optional-dependencies]`, `[dependency-groups].dev`).
- A Docker-based build test (`docker/Dockerfile.build-test`, run via `scripts/build_test.sh`)
  builds the wheel in a clean container, installs it, and smoke-tests import + CLI.

## How to release
1. Tag the commit as `vX.Y.Z` (use this consistent prefix going forward).
2. `uv build` produces the sdist + wheel with the version taken from that tag.
3. Publish (e.g. `uv publish` / twine).

Between tags, `uv build` yields a dev version like `1.0.3a13.post5.dev0+<hash>` — expected.

## Notes / alternatives considered
- `bumpver` + a static `_version.py` was dropped in favour of tag-based versioning.
- Direct git dependency `cellpycore @ git+...` requires
  `[tool.hatch.metadata] allow-direct-references = true` until cellpy-core is on PyPI.
- Existing tags are inconsistent (`v.0.3.0`, `v0.4.2`, `1.0.3a13`); the
  `pattern = "default-unprefixed"` setting tolerates them. Standardize on `vX.Y.Z`.
- Out of scope for #354 (follow-up): migrating CI workflows to uv and retiring the
  conda env files (`environment*.yml`, `github_actions_environment.yml`) and
  `docs/requirements_doc.txt`.
