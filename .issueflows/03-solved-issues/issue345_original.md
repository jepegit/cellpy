# Issue #345: batch - read custom json

Source: https://github.com/jepegit/cellpy/issues/345

## Original issue text

The batch utility should be able to get info from other JSON files than the currently supported ones.

We also need to allow for file searching after reading the JSON file.

## Comments (curated summary)

- **Additional tasks**:
  - Support BatBase-exported JSON as a first-class journal source (user story: download from BatBase → point batch at the file → populate journal pages → filefinder fills raw/cellpy paths as usual). Optional `filetype` / reader kwarg (e.g. `batbase_v1` / `custom_json_reader`).
  - Wire **file-search-after-read** on the blessed `cellpy.batch` path (not only the legacy db-reader path).
- **Clarifications / constraints**:
  - User story centers on BatBase JSON download → `batch.load(...)` (or equivalent); file-name indicators drive filefinder afterwards.
  - Folded into batch v3 A2 (#698) historically; readers + post-read search belong in `cellpy/batch/journal.py` / db engine — improve patterns and align with recent BatBase changes.
  - Milestone **v.2.1.2** (2026-07-28): self-contained patch; must not block v2.1.0 (already shipped).
- **Superseded / retracted**:
  - Closing solely via Stage-4 A2 / #698 — #345 was moved to **v.2.1.2** as a follow-up patch instead.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 4, last comment by @jepegit on 2026-07-28._
