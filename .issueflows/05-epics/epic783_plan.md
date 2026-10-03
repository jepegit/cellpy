# Epic #783: cellpy 2.2 (Stage 5) — live refresh first

Anchor: https://github.com/jepegit/cellpy/issues/783
Status: confirmed

## Goal

Ship Epic L from the Stage 5 tracker: a cell loaded from a growing raw file
can `update()` so the result matches a full load of the finished file, and a
batch can refresh or poll on top of that.

Done for this planned slice when #779, #780, #164, #781, and #782 are closed
and `uv run pytest -m essential` is green on `master`. #778 (the golden
equality anchor) is already closed. **Epic L shipped 2026-09-26** (#1016,
#1100–#1104).

Revision 2026-09-26: Stage 4 added — the **Epic M read path** (#784, BatBase
metadata) is pulled forward because the maintainer wants to interact with
BatBase as soon as possible. Push/write-back stays in 2.3 (Stage 6 plan in
`cellpy-design-and-development/roadmap/stages/stage6-github-issues.md`).

## Constraints

- Children already exist on GitHub. Specs below record those numbers as
  `Published:` so `/iflow-epic publish` does not open duplicates.
- Cellpy-only for L. Do not put `SupportsIncrementalLoad` in cellpycore.
  Core `update_data` stays the merge primitive (overlap trimmed on
  `source_datapoint_num`).
- Design: [live-incremental](https://github.com/cellpy/architecture-plan/blob/main/cellpy2-live-incremental-design.md)
  and the Stage 5 list on #783. Sequencing from the anchor: L6 first
  (done), then L1 → L2 → L3 → L4 and L5.
- v2-migration bugfixes stay `v2.1.x` patches, not this epic.
- S1–S3 need a cellpy-core PR before a cellpy re-pin. They are not detailed
  stages here.
- None of the open L issues are yolo-fit (public protocol or loader/batch
  behavior). Cycle must stop rather than weaken that.

## Stage 1 — Golden equality anchor

The correctness test lands before any loader protocol. Already closed.

- Goal: incremental `update()` of a split file equals a full load.

### Issue: L6 golden equality test — incremental update() equals full load

- Spec: see #778. Load a truncated file, append the tail, assert `update()`
  matches a full load of the whole file (summary equality).
- Goal: the equality test is the anchor for later L work.
- Model: deep
- Depends on: none
- yolo: no — defines the contract for the epic
- Published: #778

## Stage 2 — Cell update from a marker

Protocol, then the cheap loaders, then `CellpyCell.update()`.

- Goal: `c.update()` appends only new raw data when the loader supports it,
  and falls back to a full reload when it does not.

### Issue: SupportsIncrementalLoad protocol and marker types

- Spec: see #779. In cellpy (not cellpycore), add a runtime-checkable
  `SupportsIncrementalLoad` with `load_since(source, marker) -> IncrementalChunk`,
  plus `LoadMarker` and `IncrementalChunk`. Loaders that cannot do a cheap
  partial read omit the protocol so `update()` can fall back.
- Goal: the protocol and types exist and are importable; no loader is
  required to implement them yet.
- Model: deep
- Depends on: #778
- yolo: no — public protocol
- Published: #779

### Issue: load_since for cheap-partial loaders

- Spec: see #780. Implement `load_since` for `arbin_res`, `arbin_sql`,
  `neware_txt`, and `maccor_txt`. Return native-schema rows since the marker
  (tail overlap allowed) and the new marker. Other loaders stay full-read.
- Goal: those four loaders return a chunk and a new marker; a loader without
  the protocol is unchanged.
- Model: deep
- Depends on: #779
- yolo: no — four loader behaviors
- Published: #780

### Issue: CellpyCell.update loads only new data

- Spec: see #164. After `cellpy.get`, `c.update()` finds the last loaded
  point, reads from there (protocol or full reload), and refreshes summaries
  from the first new step (or the last incomplete old step). Several raw
  files on one cell must merge, not clobber.
- Goal: `c.update()` on a grown raw file matches a full reload of that file
  for the #778 equality case.
- Model: deep
- Depends on: #780
- yolo: no — public `CellpyCell` behavior
- Published: #164

## Stage 3 — Poll and batch refresh

Both sit on `c.update()`. L5 does not need the L4 poll helper.

- Goal: one cell can be polled, and a batch can refresh or poll without a
  new core API.

### Issue: live.py poll loop and retire processor.py

- Spec: see #781. Replace the `utils/live.py` stub with
  `poll(cell_or_path, interval, on_update=, stop_when_complete=True)` calling
  `c.update()`. Delete `utils/processor.py` and fold its thread-pool
  `cellpy.get` fan-out into `batch.runner`'s executor. If
  `accessor_label.lstrip` is still in `batch_core`, switch it to
  `removeprefix` (the #783 note says this may already be gone).
- Goal: `poll` calls `update` on an interval; `processor.py` is gone; no
  `lstrip` prefix bug remains.
- Model: deep
- Depends on: #164
- yolo: no — deletes a module and changes the live loop
- Published: #781

### Issue: Batch live refresh

- Spec: see #782. `b.update(live=True)` calls `c.update()` for journal
  cells. `b.poll(interval=, until=)` repeats that and re-runs collectors /
  report each tick. No new core types.
- Goal: a batch refresh and a poll both pick up appended raw data through
  `c.update()`.
- Model: deep
- Depends on: #164
- yolo: no — public batch API
- Published: #782

## Stage 4 — BatBase read path (Epic M, cross-repo)

Prerequisites exist: BatBase OAuth2 client-credentials + self-service API
clients (ife-bat/batbase#390, #391 closed); `cellpy-connectors` shared base
(cellpy/cellpy-connectors#3, #4 closed).

- Goal: `cellpy.get(...)` / `batch.load(...)` can take cell/test metadata from
  BatBase through the `MetaResolver` JOURNAL/DB layer, read-only; an
  unreachable source degrades to an empty layer.

### Issue: M0 BatBaseClient and CLI passthrough

- Spec: see cellpy/cellpy-connectors#1. Client-credentials token fetch with
  in-memory expiry cache, one re-auth on 401, keyring/env credentials,
  `cellpy connectors configure batbase`, `scope="read"` default,
  `BatBaseAuthError`. Add `get(path, **params)` and
  `cellpy connectors batbase get <endpoint>` so the API can be explored at once.
- Goal: a configured user can call any BatBase read endpoint from Python or
  the CLI without handling tokens.
- Model: fast
- Depends on: none
- yolo: yes — well specified, on the shipped connector base, no cellpy change
- Published: cellpy/cellpy-connectors#1 (external repo)
- Status: shipped 2026-09-26 via cellpy/cellpy-connectors#8 (squash-merged).

### Issue: M1 MetadataSource protocol and resolver hook

- Spec: see #784 (read scope only). `MetadataSource` Protocol
  (`fetch(key) -> MetaRecord | None`), `cellpy.metadata_sources` entry-point
  registry, `MetaResolver` JOURNAL/DB-layer precedence with provenance naming
  the source, null-object on failure, `CellMeta.uuid` + `external_id` /
  `source_uri` back-link. No push.
- Goal: cellpy has a source-agnostic slot for external metadata; the BatBase
  adapter plugs in without importing a cellpy base class.
- Model: deep
- Depends on: none (M2 needs it)
- yolo: no — public Protocol and resolver precedence
- Published: #784

### Issue: M2 BatBase MetadataSource adapter

- Spec: see cellpy/cellpy-connectors#2. Map `/api/test-cellpy-tag/` (+ batch
  and cell rows) to `MetaRecord`; decide the query key (cellpy tag vs cell
  name); offline ⇒ empty layer; registered via the entry point.
- Goal: a BatBase-tagged cell loads with BatBase mass / area / nominal
  capacity / project without journal edits.
- Model: deep
- Depends on: M0, M1
- yolo: no — mapping decisions against an unsettled API
- Published: cellpy/cellpy-connectors#2 (external repo)

## Later (unstaged)

Not sequenced into issues here. The anchor already tracks them.

- Epic S — #313, #312, #359 are core-first (core PR, PyPI, cellpy re-pin).
  #888 (RPT filters) is cellpy-only.
- Epic I — #270, #338, #306, #761, #827.
- Epic R — #687, then #691.
- Deferred to 2.3 (Stage 6 draft): versioned headers, #73 GITT/PITT, #889
  Fredrik ICA, #206 phase 1, loader-shell retirement, Epic M push (M3).
