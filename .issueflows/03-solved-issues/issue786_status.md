# Issue #786 — status

- [x] Done

## What's done

- Plan accepted; build on `cursor/786-list-instruments-warnings-5e1f`.
- `InstrumentFactory.create_all(quiet=...)`: expected discovery skips → DEBUG on module logger; unexpected failures → WARNING on module logger (not root).
- `list_instruments()` uses `create_all(quiet=True)` (removed ineffective `cellpy` logger bump).
- Caplog quiet regression + `@pytest.mark.essential`; agents.md quiet-contract note.
- Verified: `list_instruments()` emits 0 "Could not create loader" WARNINGs; `instrument_configurations()` only warns for real env failures (e.g. missing ODBC).
- HISTORY promoted to `[2.1.1.post3]`; planned release tag `v2.1.1.post3` on `master` after merge.
- PR: https://github.com/jepegit/cellpy/pull/807 (#807)

## Remaining work

- None.

## Release

- Planned tag: `v2.1.1.post3` (git-tag derived; `post` bump from `v2.1.1.post2`)
- Cut from `master` via `gh release create v2.1.1.post3 --target master --generate-notes` after squash-merge.
