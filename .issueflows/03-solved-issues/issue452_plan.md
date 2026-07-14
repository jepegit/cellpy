# Issue #452 — Plan

## Goal

Build the parallel `cellpy/config/` pydantic-settings stack (config plan Step 2) next to
today's `prms` system — typed models, layered TOML loader, provenance, `override()`,
and inventory parity against the #430 contract — **without** wiring any production import
paths yet (#453 handles the shim swap).

## Constraints

- **Behavior-preserving at the boundary** — no changes to `prms`, `prmreader`, or
  `cellpy/__init__.py` import-time init in this issue.
- **Stage 1 scope** — parallel build only; no `cellpy setup` rewrite (#454), no internal
  `prms.X` call-site migration (#453), no secrets consumer rewiring (#453 Step 6).
- **Depends on #430 + #446** — inventory parity test and constants purge are already
  landed; code dataclass defaults in `prms.py` remain authoritative for default values.
- **cellpy-core stays config-free** — `CellpyUnits` is imported for validation only;
  no file/env reads in core.
- **Fast PR gate** — mark inventory parity + one `override()` smoke test
  `@pytest.mark.essential`.
- **Plan doc authority** —
  [`architecture-plan/cellpy2-configuration-and-parameters-plan.md`](../../architecture-plan/cellpy2-configuration-and-parameters-plan.md)
  Steps 2 + §3.2–3.3.

### Prior art

| Hit | Module / file | Reuse |
|-----|---------------|--------|
| Inventory contract | [`tests/prms_support.py`](../../tests/prms_support.py), [`tests/test_prms.py`](../../tests/test_prms.py) `test_prms_inventory_parity` | **Mirror** — reuse `EXPECTED_PRMS_INVENTORY`, `assert_inventory_equal`, normalization helpers; add config-side collector + divergence table. |
| Stage 0 pattern | [`issue430_plan.md`](../03-solved-issues/issue430_plan.md) (solved) | **Mirror** — `*_support.py` + focused test module. |
| Prms dataclass defaults | [`cellpy/parameters/prms.py`](../../cellpy/parameters/prms.py) | **Reference** — field names, types, instrument seed dicts (`_Arbin`, …). |
| Path coercion | [`cellpy/parameters/prmreader.py`](../../cellpy/parameters/prmreader.py) `_convert_paths_to_dict`, [`cellpy/internals/connections.py`](../../cellpy/internals/connections.py) `OtherPath` | **Wrap** — pydantic `Annotated` validators, don't rewrite OtherPath. |
| Unit keys | [`cellpycore.units.CellpyUnits`](../../cellpy-core/src/cellpycore/units/spec.py) | **Validate** `units` section field names against this model. |
| Toolbox | [`.issueflows/00-tools/`](../../.issueflows/00-tools/) | No config helpers — new `tests/config_support.py` only. |
| Graph | `prms.py`, `prmreader.py` communities | Confirms surface area; no new graph pass required before start. |

## Approach

### 1. Dependencies

Add to `[project.dependencies]` in [`pyproject.toml`](../../pyproject.toml):

- `pydantic-settings>=2` (brings pydantic v2)
- `platformdirs>=4`

Regenerate lock with `UV_NO_SOURCES=1 uv lock`. Do **not** remove `ruamel.yaml` /
`python-box` yet (still used by legacy prms; #453+).

### 2. Package layout (`cellpy/config/`)

| Module | Responsibility |
|--------|----------------|
| `types.py` | `OtherPathField` / path `Annotated` validators (wrap existing `OtherPath`; posix serialize for tests); `LimitLoadedCycles` union type (`int \| tuple[int, int] \| list[int] \| None`). |
| `models.py` | Section models + root `CellpyConfig(BaseSettings)` with `validate_assignment=True`, `env_prefix="CELLPY_"`, `env_nested_delimiter="__"`. |
| `sources.py` | Custom pydantic-settings sources + provenance registry (`SourceLayer` enum: default, user_file, project_file, env, runtime). |
| `loader.py` | Resolve file paths (`platformdirs.user_config_dir("cellpy")/cellpy.toml`; project-local walk-up from `Path.cwd()`); layer merge order; `reload()`. |
| `migrate.py` | YAML (ruamel) → TOML (`tomllib` round-trip via dict) converter — library function only; CLI wiring is #454. |
| `session.py` | Module-level lazy singleton, `override()` context manager (stacked), `sources()` export. |
| `__init__.py` | PEP 562 lazy exports: section accessors (`config.reader`, …), `override`, `sources`, `reload`; **no import-time file I/O**. |

### 3. Model tree (maps to #430 inventory)

Root `CellpyConfig` sections (snake_case in TOML / env):

| New section | Legacy `prms` source | Notes |
|-------------|---------------------|-------|
| `paths` | `PathsClass` | `rawdatadir` / `cellpydatadir` as `OtherPathField`; plain `Path`/`str` for others. |
| `file_names` | `FileNamesClass` | Mechanical. |
| `reader` | `ReaderClass` | `limit_loaded_cycles`: fix to proper union (default `None` unchanged). |
| `db` | `DbClass` | Mechanical. |
| `db_cols` | `DbColsClass` | Top-level sibling (not nested) — keeps #430 triple names stable. |
| `batch` | `BatchClass` | Mechanical. |
| `instruments` | `InstrumentsClass` | Typed `ArbinConfig`, `MaccorConfig`, `NewareConfig`, `BatmoConfig` with `model_config = ConfigDict(extra="allow")`; `tester`, `custom_instrument_definitions_file` on parent. **Drop** `SQL_*` from `ArbinConfig` (→ `secrets`). |
| `defaults` | `CellInfoClass` + `MaterialsClass` | Nested `cell_info` + `materials` sub-models (`ScienceDefaults`); docstring: values in **cellpy units** by convention. |
| `units` | *(new)* | `Units` model mirroring `cellpycore.units.CellpyUnits` defaults; keys validated at model build. |
| `secrets` | env / `.env` only | `SecretStr` fields (`password`, `key_filename`, `host`, `user`, …); excluded from TOML dump and `model_dump` for files. |

`CellpyConfig` is **not** imported anywhere outside `cellpy/config/` and tests in this PR.

### 4. Layered loader + provenance

Load order (lowest → highest precedence):

1. Model field defaults
2. User `cellpy.toml` (`platformdirs.user_config_dir("cellpy")`)
3. Project-local `cellpy.toml` (walk up from cwd, stop at filesystem root)
4. Environment variables + `.env` (pydantic-settings; honour existing `.env_cellpy` path from `paths.env_file` when set at load time)
5. Runtime (`override()` / `reload(init_kwargs=…)`)

Each custom settings source records `(dotted_path → SourceLayer)` into a provenance map.
`sources()` returns a JSON-serializable dict answering “where did this value come from” for
at least one field per layer (acceptance asks for all four non-runtime layers; runtime
demonstrated via `override()` test).

### 5. `override()` + pytest fixture

```python
with cellpy.config.override(reader={"cycle_mode": "cathode"}):
    assert cellpy.config.reader.cycle_mode == "cathode"
# restored
```

- Stack nested overrides (LIFO restore).
- Add `isolated_config` fixture in [`tests/conftest.py`](../../tests/conftest.py) wrapping
  `override()` with empty or per-test kwargs.
- One essential test proves scoped mutation + restore without leaking to next test.

### 6. Inventory parity test

New [`tests/config_support.py`](../../tests/config_support.py):

- `collect_config_inventory()` — fresh `CellpyConfig` with paths rooted at fixed
  `INVENTORY_ROOT` (same constant as `prms_support.py`).
- `flatten_config_to_legacy_triples()` — map new sections back to #430 names
  (`defaults.cell_info.*` → `("CellInfo", field, value)`, etc.).
- `DELIBERATE_DIVERGENCES` — documented triples **intentionally** absent or changed:

  | Triple / area | Divergence |
  |---------------|------------|
  | `Instruments.Arbin.SQL_*` | Moved to `secrets` (env-only); not in file-backed inventory. |
  | `units.*` | New section; assert defaults match `CellpyUnits()` separately. |
  | `reader.limit_loaded_cycles` | Type widened to union; default stays `None`. |

New [`tests/test_config.py`](../../tests/test_config.py):

- `test_config_inventory_parity` (`@pytest.mark.essential`) — legacy triples match
  `EXPECTED_PRMS_INVENTORY` minus documented divergences; plus `test_units_defaults_match_cellpycore`.
- Loader tests (full suite): user file overrides default; project file overrides user;
  env `CELLPY_READER__CYCLE_MODE` wins over file; `sources()` reflects layers.
- `test_config_override_fixture` (`@pytest.mark.essential`) — `isolated_config` + direct `override()`.
- `test_yaml_to_toml_converter` — round-trip a minimal legacy YAML snippet through `migrate.py`.
- TOML serialize/deserialize smoke for one mutated section.

### 7. Implementation order (single PR, suite-green after each milestone)

1. Deps + empty package skeleton
2. `types.py` + `models.py` (models only, no I/O)
3. Inventory parity test green (models instantiated with defaults)
4. `sources.py` + `loader.py` + file-layer tests
5. `session.py` + `override()` / fixture
6. `migrate.py` + converter test
7. Document new module in `tests/README.md` (one subsection)

## Files to touch

| Path | Change |
|------|--------|
| `pyproject.toml` | Add `pydantic-settings`, `platformdirs`; lock regen. |
| `cellpy/config/__init__.py` | New — lazy public API. |
| `cellpy/config/types.py` | New — OtherPath + union types. |
| `cellpy/config/models.py` | New — all section models + `CellpyConfig`. |
| `cellpy/config/sources.py` | New — layered sources + provenance. |
| `cellpy/config/loader.py` | New — path discovery, `reload()`. |
| `cellpy/config/session.py` | New — singleton + `override()`. |
| `cellpy/config/migrate.py` | New — YAML→TOML helper. |
| `tests/config_support.py` | New — inventory collector + divergence table. |
| `tests/test_config.py` | New — parity, loader, override, migrate tests. |
| `tests/conftest.py` | Add `isolated_config` fixture. |
| `tests/README.md` | Short config-test subsection. |
| `uv.lock` | Regenerated. |

**Not in scope:** `cellpy/parameters/*`, `cellpy/__init__.py`, `cellpy/cli.py`, production
call sites.

## Test strategy

```bash
uv run pytest tests/test_config.py -m essential   # PR gate subset
uv run pytest tests/test_config.py              # full new module
uv run pytest -m essential                      # ensure no regressions in Tier 1
```

Existing `tests/test_prms.py` must remain green unchanged (legacy path untouched).

## Open questions

1. **Project `cellpy.toml` walk-up depth** — Recommend: stop at filesystem root (same as
   git discovery intent in plan §3.1); no `pyproject.toml` anchor required in v1.
2. **`Arbin.SQL_*` in parity** — Recommend: exclude from config inventory via
   `DELIBERATE_DIVERGENCES`; add separate essential test that `secrets` reads
   `CELLPY_*` env vars. Confirm?
3. **`units` default source** — Recommend: copy defaults from `cellpycore.units.CellpyUnits()`
   field values (not from legacy `internal_settings.cellpy_units` singleton) so core
   remains authoritative.
4. **User config filename during parallel phase** — Recommend: write/read `cellpy.toml`
   only in the new stack; legacy `.cellpy_prms_*.conf` untouched until #454 migrate.

---

**Next step after Accept:** `/iflow-start` on branch `452-pydantic-config-stack`.
