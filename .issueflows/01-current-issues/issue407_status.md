# Issue #407 — Status

- [ ] Done

## Locked decisions (from plan review)

- Windows GHA Python **3.13** (match `pytest_posix.yml`).
- **Do not** disable the AppVeyor.com project manually (repo still drops `appveyor.yml`).
- Cache the ACE installer via `actions/cache` (key tied to workflow file hash).

## What's done

- **`.github/workflows/pytest_win.yml`** — enabled on push/PR; ACE x64 install with `actions/cache`; Python 3.13; `github_actions_environment.yml`; ODBC driver check; CI-style pytest ignore.
- **Removed** `appveyor.yml` and `.github/workflows/test-win.yml`.
- **Docs** — dropped `appveyor.yml` from folder-structure listings.
- **`tests/test_batch.py`** — generic CI flaky skip reason.
- **`tests/test_filefinder.py`** — basename extraction via `pathlib.Path.name` (Windows backslash paths).

## Remaining work

- [ ] Confirm GHA Windows job green on PR (`/iflow-close`).
