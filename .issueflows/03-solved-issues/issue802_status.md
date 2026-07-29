# Issue #802 — Status

- [x] Done

## What's done

- Plan accepted on `cursor/802-update-history-143c`.
- Backfilled `HISTORY.md`: `[2.1.1]` (2026-07-29) and `[2.1.0.post1]`
  (2026-07-28) from GitHub release notes; moved Unreleased `v2-docs-stable`
  retirement into post1 (#775); left `[2.1.0]` intact; Dependabot omitted.
- Stale-docs skim of `README.md` / `docs/`: no clear public falsehoods to fix.
- Close: promoted Unreleased → `[2.1.1.post1]`; planned tag `v2.1.1.post1`.
- Essential tests green (`uv run pytest -m essential`: 606 passed).

## Remaining work

- None (release tag created after merge).

## Notes

- PR: https://github.com/jepegit/cellpy/pull/803 (#803)
- Planned tag: `v2.1.1.post1` (git-tag derived; create on `master` after merge)
