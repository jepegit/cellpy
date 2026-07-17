# Issue #537 plan — journal-page column literals → HeadersJournal

## Goal

Remove the hard-coded journal column-name string literals flagged by
`.issueflows/00-tools/scan_hardcoded_headers.py` as `HeadersJournal`, so a
later header rename touches the header class only (native-headers Phase-0
prerequisite).

## Scope (verified with the scan tool, 2026-07-17)

Only **6 findings, on 3 lines** — all are string-keyed subscripts into the
already-imported `hdr_journal` object (the §6 "semi-sanctioned" pattern):

- `cellpy/utils/batch_tools/batch_plotters.py:53` — `hdr_journal["mass"]`,
  `["loading"]`, `["label"]`
- `cellpy/utils/batch_tools/batch_plotters.py:76` — `hdr_journal["group"]`,
  `["sub_group"]`
- `cellpy/utils/helpers.py:278` — `hdr_journal["loading"]`

Non-journal (raw/steps/summary) literals in the same files are **out of
scope** — they belong to #538.

## Approach

Mechanical `hdr_journal["<name>"]` → `hdr_journal.<name>`. Verified all five
attribute values equal their subscript values (`HeadersJournal` is a dataclass
exposing both), so behavior is byte-identical.

## Files to touch

- `cellpy/utils/batch_tools/batch_plotters.py`
- `cellpy/utils/helpers.py`

## Test strategy

Behavior-preserving rename-to-lookup; the full suite is the oracle. Confirm
the scan tool reports **zero `HeadersJournal` findings** for both files after.
