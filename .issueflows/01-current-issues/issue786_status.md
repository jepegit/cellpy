# Issue #786 — status

- [ ] Done

## What's done

- Plan accepted; build on `cursor/786-list-instruments-warnings-5e1f`.
- `InstrumentFactory.create_all(quiet=...)`: expected discovery skips → DEBUG on module logger; unexpected failures → WARNING on module logger (not root).
- `list_instruments()` uses `create_all(quiet=True)` (removed ineffective `cellpy` logger bump).
- Caplog quiet regression + `@pytest.mark.essential`; agents.md quiet-contract note.
- Verified: `list_instruments()` emits 0 "Could not create loader" WARNINGs; `instrument_configurations()` only warns for real env failures (e.g. missing ODBC).

## Remaining work

- HISTORY Unreleased bullet + `/iflow-close`.
