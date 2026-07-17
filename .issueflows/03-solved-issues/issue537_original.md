# Issue #537: v2 pre-flip: replace hardcoded journal-page column literals with HeadersJournal

Source: https://github.com/jepegit/cellpy/issues/537

## Original issue text

## Context

Phase-3 flip prerequisite (native-headers plan Phase 0, item 2; hardcoded-column-headers-report Â§8 priority 1). Audited 2026-07-17 with `.issueflows/00-tools/scan_hardcoded_headers.py`; remaining `HeadersJournal`-family findings:

| File | Findings (all families) |
|---|---|
| `cellpy/utils/batch_tools/batch_plotters.py` | 32 |
| `cellpy/utils/helpers.py` | 34 (journal subset only in this issue) |
| `cellpy/utils/collectors.py` | 16 (journal subset) |
| `cellpy/utils/batch_tools/batch_journals.py` | 1 |
| `cellpy/utils/batch.py` | 0 â€” already clean, keep it that way |

## Work

Mechanical 1:1: each literal flagged as `HeadersJournal` by the scan tool becomes an attribute access on the already-imported `hdr_journal` / `get_headers_journal()`. No behavior change. Leave non-journal findings in the same files for the sibling issue (steps/raw/summary literals).

## Acceptance

- [ ] Scan tool reports **zero `HeadersJournal` findings** for the files above
- [ ] Full suite green (behavior unchanged â€” this is a pure rename-to-lookup)

ðŸ¤– Generated with [Claude Code](https://claude.com/claude-code)
