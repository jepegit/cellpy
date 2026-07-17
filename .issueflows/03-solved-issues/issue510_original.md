# Issue #510: v2: cellpy file format v2 + metadata persistence + release (V2-13/14/15)

Source: https://github.com/jepegit/cellpy/issues/510

## Original issue text

**v2 Phase 4 — persistence and release** (epic #402: themes V2-13, V2-14, V2-15).
Target branch: `master`. Depends on: Phases 1-3. Gates the v2.0 tag.

## Work

- **V2-13** cellpy file format v2 (HDF5 layer): version bump; serialize
  `TestMetaCollection`; migration from v1 files. Done when the v1-to-v2-to-read
  round-trip test passes.
- **V2-14** Metadata persistence policy (cellpy-owned; core stubs stay stubs):
  implement the real `save_archive` / load paths cellpy needs so a user can
  save merged campaign metadata.
- **V2-15** Release discipline: pin exact `cellpycore==...` in the release
  commit; follow `release-procedure.md`; publish the v1-to-v2 migration guide.

## Refs

Epic #402 / `cellpy-v2-epic.md` Phase 4; breaking-changes policy section.
