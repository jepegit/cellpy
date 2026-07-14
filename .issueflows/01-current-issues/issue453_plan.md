# Issue #453 — Plan

## Goal

Wire production code onto the #452 `cellpy/config/` stack: a deprecated `prms` shim for
external/notebook callers, mechanical migration of internal `prms.*` sites to
`cellpy.config.*`, and removal of import-time `prmreader.initialize()` so
`import cellpy` performs zero file I/O.

## Constraints

- **Behavior-preserving Stage 1** — full suite green after each milestone; #430 inventory
  parity and #452 config parity tests unchanged except documented divergences.
- **Depends on #452 (merged) and #456 (`warn_once`)** — shim warnings use
  [`cellpy/_deprecation.py`](../../cellpy/_deprecation.py).
- **Out of scope (#454)** — `cellpy setup` UX rewrite, interactive migrate command,
  `cellpy info --config` provenance CLI. Keep `cellpy setup` working via a thin YAML
  export adapter, not a full CLI rewrite.
- **Out of scope (issue Step 6 / later)** — rewiring `connections.py` / `otherpath.py` to
  stop using raw `os.getenv`; secrets stay env-backed in the new model.
- **Constants stay on `prms`** — `_cellpyfile_*`, `_github_*`, loader dev flags, etc. are
  not config; shim must not intercept them.
- **Fast PR gate** — new import-io + shim smoke tests marked `@pytest.mark.essential`.

### Prior art

| Hit | Module / file | Reuse |
|-----|---------------|--------|
| New config stack | [`cellpy/config/`](../../cellpy/config/) (#452) | **Engine** — `session.reload()`, `override()`, models, loader. |
| YAML → dict | [`cellpy/config/migrate.py`](../../cellpy/config/migrate.py) | **Legacy ingest** — `convert_yaml_to_toml_dict` for `.cellpy_prms_*.conf`. |
| Inventory / parity | [`tests/prms_support.py`](../../tests/prms_support.py), [`tests/test_config.py`](../../tests/test_config.py) | **Guardrails** — keep green; extend only if shim changes observable defaults. |
| Deprecation helper | [`cellpy/_deprecation.py`](../../cellpy/_deprecation.py) | **Shim warnings** — `warn_once("prms.Reader", "cellpy.config.reader")` per access pattern. |
| Architecture authority | [`architecture-plan/cellpy2-configuration-and-parameters-plan.md`](../../architecture-plan/cellpy2-configuration-and-parameters-plan.md) Steps 3–4, §3.5 | Section mapping, sequencing. |
| #452 plan (solved) | [`issue452_plan.md`](../03-solved-issues/issue452_plan.md) | Deliberate divergences (SQL→secrets, `units`, `defaults` nesting). |
| Toolbox | [`.issueflows/00-tools/`](../../.issueflows/00-tools/) | No migration helper yet — optional one-shot codemod script (see Approach). |
| Graph | — | No `graphify-out/`; grep-only. |

## Approach

Deliver in **three suite-green milestones** (one issue, ordered commits).

### Milestone 1 — Shim + legacy load path (Step 3)

**1a. Legacy config layer** — new [`cellpy/config/legacy.py`](../../cellpy/config/legacy.py):

- Port `_get_prm_file` discovery (user-dir glob for `.cellpy_prms*.conf`) from
  [`prmreader.py`](../../cellpy/parameters/prmreader.py) — single home for legacy path lookup.
- `load_legacy_yaml(path) -> dict` via `migrate.convert_yaml_to_toml_dict`.
- Extend [`loader.py`](../../cellpy/config/loader.py): when `skip_files` is false and
  **no** `cellpy.toml` exists at user or project layer, fall back to discovered legacy YAML
  (record provenance layer `USER_FILE` / tag as legacy in tests). TOML still wins when present.

**1b. `prmreader` slim-down** (keep public API for CLI/tests):

- `initialize()` → `cellpy.config.reload()` (+ load `.env` via existing loader env path).
- Delete `_update_prms` and inline glob discovery (delegate to `legacy.py` + loader).
- Replace `_pack_prms` with `export_legacy_yaml_dict()` reading **from** `get_config()` —
  inverse of migrate mapping (CLI `cellpy setup` write path stays YAML until #454).
- `_read_prm_file` → legacy load + `reload(overrides=…)`.

**1c. `prms` shim** — new [`cellpy/parameters/_shim.py`](../../cellpy/parameters/_shim.py):

- `_SECTION_MAP`: legacy export name → config accessor
  (`Paths`→`paths`, `FileNames`→`file_names`, `Reader`→`reader`, `Db`→`db`,
  `DbCols`→`db_cols`, `Batch`→`batch`, `Instruments`→`instruments`,
  `CellInfo`→`defaults.cell_info`, `Materials`→`defaults.materials`).
- `_SectionProxy`: attribute get/set forwards to pydantic section;
  `warn_once` on first touch per call site (reads **and** writes).
- Module-level `prms.__getattr__` for mapped sections; unmapped names unchanged
  (constants, `*Class` type aliases kept for typing until v2.1).
- **Instrument compat:** proxy `__getitem__` for `Arbin["SQL_server"]` etc. reads/writes
  `config.secrets` with deprecation (SQL fields removed from `ArbinConfig` in #452).
- Remove eager singleton instances (`Paths = PathsClass()`, …) for mapped sections;
  keep dataclass **classes** as deprecated type aliases.

**1d. Tests (Milestone 1)**

- `test_import_cellpy_no_file_io` — monkeypatch `builtins.open` / `Path.read_text`; import
  `cellpy`; assert zero config-path reads.
- `test_prms_shim_forwards_and_warns` — mutation + read via `prms.Reader` hits `config.reader`.
- `test_legacy_yaml_fallback_loads` — temp `.cellpy_prms_<user>.conf` overrides default.
- Existing `tests/test_prms.py` green (shim preserves user-facing behavior).

Suite gate: `uv run pytest -m essential`.

### Milestone 2 — Internal call-site migration (Step 4)

Mechanical rewrite **`prms.<Section>.<field>` → `cellpy.config.<section>.<field>`** in
production code under `cellpy/` (~35 files, ~350 occurrences). Suggested batch order:

| Batch | Paths | Notes |
|-------|-------|-------|
| A | `parameters/internal_settings.py`, `parameters/prmreader.py` | Highest coupling; fix dataclass defaults that bind `prms.CellInfo.*` at class body — use `None` + lazy read from `config.defaults` in factories, or read at use site. |
| B | `readers/**` (incl. `arbin_*.py`, `filefinder.py`, `cellreader.py`) | Fix **module-level** `SQL_* = prms.Instruments.Arbin[...]` — move to lazy functions or read inside methods; map to `config.secrets` where applicable. |
| C | `utils/**`, `cli.py`, `log.py`, `internals/connections.py` | `cli.py` may keep `prms` re-exports temporarily for setup UX; prefer `config` for reads. |

**Mapping table** (mechanical):

| Legacy | New |
|--------|-----|
| `prms.Paths` | `cellpy.config.paths` |
| `prms.FileNames` | `cellpy.config.file_names` |
| `prms.Reader` | `cellpy.config.reader` |
| `prms.Db` | `cellpy.config.db` |
| `prms.DbCols` | `cellpy.config.db_cols` |
| `prms.Batch` | `cellpy.config.batch` |
| `prms.Instruments` | `cellpy.config.instruments` |
| `prms.CellInfo` | `cellpy.config.defaults.cell_info` |
| `prms.Materials` | `cellpy.config.defaults.materials` |

Import style: `import cellpy.config as config` (or `from cellpy import config` if added to
public API) — avoid `from cellpy.config import reader` churn across 350 sites unless a
follow-up cleanup prefers it.

Optional helper: `.issueflows/00-tools/migrate_prms_calls.py` (stdlib + regex) for
bulk replace + manual review of instrument/SQL/module-level edge cases.

Tests: full suite; spot-check `tests/test_prms.py` still exercises shim for external API.

### Milestone 3 — Kill import-time init

- [`cellpy/__init__.py`](../../cellpy/__init__.py): remove `init()` call and `init` from
  `__all__`; keep `from cellpy.parameters import prms` for backward compat.
- Document lazy init in module docstring / HISTORY stub (full entry at `/iflow-close`).
- Update [`cellpy/config/__init__.py`](../../cellpy/config/__init__.py) module docstring
  (no longer “nothing imports this”).
- Ensure first config touch in tests that relied on import-time load still passes
  (`test_prms.py` calls `prmreader.initialize()` explicitly where needed — keep that).

Suite gate: `uv run pytest -m essential` then `uv run pytest`.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/config/legacy.py` | **New** — legacy YAML discovery + load. |
| `cellpy/config/loader.py` | Legacy YAML fallback layer. |
| `cellpy/parameters/_shim.py` | **New** — section proxies + `__getitem__` compat. |
| `cellpy/parameters/prms.py` | Drop eager section singletons; wire shim; keep constants/classes. |
| `cellpy/parameters/prmreader.py` | Delegate to config; delete `_update_prms`; YAML export adapter. |
| `cellpy/__init__.py` | Remove import-time `initialize()`. |
| `cellpy/config/__init__.py` | Docstring only. |
| `cellpy/readers/**`, `cellpy/utils/**`, `cellpy/cli.py`, … | Mechanical `prms` → `config` (~35 files). |
| `tests/test_prms_shim.py` or extend `tests/test_config.py` | Import-io, shim, legacy fallback tests. |
| `tests/conftest.py` | If needed: autouse `reset_session()` ordering with legacy tests. |
| `.issueflows/00-tools/migrate_prms_calls.py` | **Optional** codemod + README index row. |

**Not in scope:** `cellpy/cli.py` setup rewrite (#454), TOML-first UX, secrets consumer cleanup.

## Test strategy

```bash
uv run pytest tests/test_config.py tests/test_prms.py -m essential  # parity + legacy
uv run pytest -m essential                                          # Tier-1 gate
uv run pytest                                                       # full suite before close
```

New essential tests:

1. **`test_import_cellpy_no_file_io`** — acceptance criterion from issue body.
2. **`test_prms_shim_warns_once`** — DeprecationWarning per call site, not per attribute.
3. **`test_legacy_yaml_fallback_loads`** — user YAML without `cellpy.toml` applies overrides.

Regression focus: `test_prms.py` round-trip, CLI setup tests (`test_cellpy_cmd.py`),
instrument readers (Arbin SQL module-level constants), batch tools.

## Open questions

1. **Legacy YAML fallback until #454** — Recommend **yes** (Milestone 1): users with only
   `.cellpy_prms_*.conf` keep working; TOML takes precedence when present. Confirm?

2. **SQL credentials on instrument dict access** — Recommend shim + migrated call sites route
   `Instruments.Arbin["SQL_*"]` to `config.secrets` with deprecation (matches #452 divergence).
   `easyplot` mutation of SQL fields becomes secrets/env mutation. Confirm?

3. **`internal_settings` dataclass defaults** — Recommend replace import-time
   `prms.CellInfo.*` field defaults with lazy resolution (factory or `@property` on parent
   config object) so lazy init does not freeze wrong values. Acceptable behavior change if
   defaults now reflect first config load, not import-time file read?

4. **Codemod script in `00-tools/`** — Recommend add small helper for bulk replace; still
   manual pass on `arbin_*` / `easyplot` / module-level bindings. Want it, or pure manual?

---

**Next step after Accept:** `/iflow-start` on branch `453-prms-shim-swap`.
