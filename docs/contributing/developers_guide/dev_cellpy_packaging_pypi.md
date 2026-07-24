# Packaging for PyPI

Packaging is defined in `pyproject.toml` (hatchling). The package version comes
from the **git tag** via `uv-dynamic-versioning` — there is no hand-edited
version string. Tag `vX.Y.Z` → PyPI version `X.Y.Z`.

## Recommended: GitHub release → CI

Publishing a GitHub release runs `.github/workflows/release.yml`: validate the
tag against the branch → run essential tests → `uv build` → upload to PyPI with
trusted publishing (OIDC; no API token in CI).

| Tag pattern | Branch | Notes |
|-------------|--------|--------|
| `v1.x.y` (and 1.x pre-releases) | `v1.x` | 1.x maintenance |
| `v2.x.y` (and 2.x pre-releases) | `master` | v2 development |

Example (v2 pre-release from `master`):

```shell
git switch master && git pull --ff-only
git status   # must be clean — no untracked files either
gh release create v2.0.0a2 --target master --generate-notes
```

Example (1.x from `v1.x`):

```shell
git switch v1.x && git pull --ff-only
git status
gh release create v1.1.1 --target v1.x --generate-notes
```

!!! warning
    Releases tag whatever commit is at HEAD. Keep the tree clean before cutting
    a release — stray untracked files on that commit ship with it.

## Build locally

Check the sdist and wheel without publishing:

```shell
uv build
```

Optional Docker smoke test (clean install + `import cellpy` + CLI):

```shell
scripts/build_test.sh
```

Between tags, `uv build` yields a dev version such as
`2.0.0a1.post3.dev0+<hash>` — that is expected.

## Manual publish (fallback)

Prefer the GitHub release path. If you must publish by hand:

1. Tag the commit (`vX.Y.Z`) on the correct branch and push the tag.
2. `uv build`
3. `uv publish` (or twine) using your PyPI credentials / token.

Trusted publishing via the `pypi` GitHub environment is the normal path; API
tokens are only for exceptional manual uploads.
