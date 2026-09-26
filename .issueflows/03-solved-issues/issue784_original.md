# Issue #784: Pluggable external metadata sources (query an API for cell/test metadata)

Source: https://github.com/jepegit/cellpy/issues/784
Labels: enhancement, v2, cellpy2-stage5
Captured: 2026-09-26 (Epic M / M1, stage 4 of #783; read scope only)

---

Let cellpy **pull (and optionally push) cell/test metadata from an external source** — starting
with **BatBase** (our in-house Django + PostgreSQL app, HTTP API) — but **source-agnostic**: a
pluggable contract so other labs' stores work too. First transport assumption: an **HTTP API**
(GET to read, POST/PUT to write).

Realizes the deferred **metadata-plan Step 7** ("DB/API transport — keep the door open"). Full
design: **[cellpy2-metadata-source-integration.md](https://github.com/cellpy/architecture-plan/blob/main/cellpy2-metadata-source-integration.md)**.

**Approach (mirrors the loader contract):**
- `MetadataSource` **Protocol** + `cellpy.metadata_sources` entry-point registry — third
  parties plug in without importing a cellpy base class.
- Feeds the existing **`MetaResolver` JOURNAL/DB layer** (authoritative lab metadata already
  outranks raw-file values; provenance extended to name the source).
- **Anti-corruption boundary**: cellpy pins the Protocol + `MetaRecord`; the **BatBase adapter
  absorbs API churn** (BatBase API isn't settled yet — adapter can even be a separate plugin
  package, keeping the HTTP dep out of cellpy core).
- Adds **`CellMeta.uuid`** + per-source `external_id`/`source_uri` back-link (the identity
  parking item, metadata-plan OQ6); vocabulary normalization toward **BattINFO** (OQ4).
- Null-object: an unreachable/unknown source ⇒ empty layer, cell still loads. Push is
  side-effecting → **explicit opt-in only**, never automatic. Auth via env-only `SecretStr`.

**Scope:** read path first (Protocol + `fetch` + resolver + BatBase GET adapter); push a later
opt-in follow-on. **Post-2.2 (2.3+)** — additive, gates nothing in 2.2.

Adjacent: #243 (dbreader refactor). See design doc for the work breakdown + open questions
(query key, adapter placement, cache/offline, push permission, multi-source precedence).
