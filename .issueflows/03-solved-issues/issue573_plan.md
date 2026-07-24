# Issue #573 — plan

## Goal

Lock the cellpy **2.0 file-format support matrix** in one essential, parametrized
suite (and align default `load` with that matrix), so #574’s release checklist can
assert a test — not a sentence.

## Constraints

- **Plan of record:** [architecture-plan/cellpy2-release-and-branching-plan.md](../../../architecture-plan/cellpy2-release-and-branching-plan.md) §1;
  architecture plan §2 / §6 row 3.1; Stage-3 sequencing: **#573 before #574**.
- **Promised 2.x matrix:** read **v8 + v9**, write **v9** (default) and **v8** via
  `save(... cellpy_file_format="v8"|".h5")`; **v&lt;8** → typed error that names
  `cellpy convert` on **1.x**.
- **Already shipped (do not re-implement):** `cellpy convert --to v9|v8` and
  destination inference ([`cli_api.convert`](../../cellpy/cli_api.py), CLI wiring in
  [`cli.py`](../../cellpy/cli.py), essential coverage in
  [`tests/test_cli_api.py`](../../tests/test_cli_api.py)) from #569 / #568.
- **Parity helpers already exist:** reuse
  [`tests/cellpy_file_support.py`](../../tests/cellpy_file_support.py)
  (`assert_data_frames_equal`, meta/fid helpers, `snapshot_cell_state`) — do not
  invent a second oracle.
- **Fixtures:** `testdata/hdf5/20160805_test001_45_cc_v{0,4,5,6,7,8,8_with_fids}.h5`
  already cover the versions the matrix needs.
- **CI:** Tier-1 is `uv run pytest -m essential` ([ci-tiers.md](../04-designs-and-guides/ci-tiers.md)).
  Matrix cells that guard the release promise get `@pytest.mark.essential`; no new
  workflow.
- **Docs drift:** [migration_v1_to_v2.md](../../docs/getting_started/migration_v1_to_v2.md)
  currently says 2.x still loads v4–v8; freeze must update that table in the same PR.
- **KISS:** one new test module + small load-path / message change. No new package
  layer.

### Prior art

| Hit | Module | Convention |
|---|---|---|
| `cli_api.convert` / `CONVERT_TARGETS` | [`cellpy/cli_api.py`](../../cellpy/cli_api.py) | **Reuse** — already implements `--to` + suffix inference; convert keeps `accept_old=True`. |
| v8→v9 value round-trip | [`tests/test_cellpy_file_v9.py`](../../tests/test_cellpy_file_v9.py) | **Mirror** into matrix row (same helpers / fixture). |
| v8 HDF5 round-trip + legacy v4–v7 shapes | [`tests/test_cellpy_file_roundtrip.py`](../../tests/test_cellpy_file_roundtrip.py) | **Coexist** — leave characterization tests; matrix is the release contract. |
| Version gate | [`cellpy/readers/cellpy_file/read.py`](../../cellpy/readers/cellpy_file/read.py) | **Migrate** — today’s `accept_old=False` message says `Try loading setting accept_old=True`; freeze message must name convert on 1.x. |
| `CellpyCell.load(..., accept_old=True)` default | [`cellpy/readers/cellreader.py`](../../cellpy/readers/cellreader.py) | **Migrate** — default still permissive; contradicts release §1. |
| Parity helpers | [`tests/cellpy_file_support.py`](../../tests/cellpy_file_support.py) | **Reuse**. |
| Toolbox (`00-tools/`) | — | None relevant. |
| Graph communities | cellpy_file / convert / WrongFileVersion / CLI | Confirms same hotspots; no extra modules. |

## Approach

### 1. Decide freeze semantics (product)

**Recommended (matches issue + release §1):**

1. Change `CellpyCell.load` default to `accept_old=False`.
2. On `version < 8` with `accept_old=False`, raise `WrongFileVersion` whose message
   **names `cellpy convert` on cellpy 1.x** (and, briefly, that 2.x `cellpy convert`
   can also rewrite if they already upgraded). Drop the
   `Try loading setting accept_old=True` as the primary instruction — keep
   `accept_old=True` as a documented escape for tests / advanced use, not the
   user-facing remedy.
3. Leave `cli_api.convert(..., accept_old=True)` so 2.0 CLI convert still upgrades
   v4–v7 → v9/v8 (already covered by `test_convert_really_upgrades_a_legacy_file`).
4. Update migration guide support-matrix row to: 2.x default `load` = **v8 + v9
   only**; pre-v8 → convert (1.x preferred; 2.x `cellpy convert` also works).

**Note:** v1.x today still uses the old `accept_old=True` message — the “promised”
1.x deprecation text was never landed as a distinct string. Craft the 2.0 freeze
message from release §1 / migration guide; optionally open a small v1.x follow-up
to warn — **out of scope** unless you want it in this PR (see Open questions).

### 2. One parametrized matrix suite

Add [`tests/test_file_format_compat_matrix.py`](../../tests/test_file_format_compat_matrix.py)
with one row per matrix cell (all `@pytest.mark.essential` unless a cell is
fixture-missing → `pytest.skip`):

| Cell | Assert |
|---|---|
| read v8 | `load(v8_with_fids)` succeeds; non-empty raw/steps/summary |
| read v9 | v8 → `save(.cellpy)` → `load`; zip sniff + tables |
| write v9 (default) | `save(tmp.cellpy)` → `is_zip_cellpy` + `cellpy_file_version == 9` |
| write v8 | `save(tmp.h5)` or `cellpy_file_format="v8"` → HDF5 keys, not zip |
| read v&lt;8 (default) | v5 (and optionally v4/v7) → `WrongFileVersion` matching convert/1.x |
| read v&lt;8 (`accept_old=True`) | still loads (escape; not the user path) |
| convert → v9 / v8 | thin wrap or import of existing CLI-api real-file test pattern (v5 fixture) |
| v8 round-trip parity | v8 → v9 → load; raw/steps/summary via `assert_data_frames_equal` (same as `test_v8_to_v9_to_read_roundtrip`) |
| v8 → save v8 → load parity | optional second parity row if cheap |

Do **not** delete `test_cellpy_file_v9.py` / `test_cellpy_file_roundtrip.py` /
`test_cli_api.py` convert tests — matrix is the release contract; those stay as
characterization depth.

### 3. Retarget existing tests that assume permissive default

- [`tests/test_cellpy_file_roundtrip.py`](../../tests/test_cellpy_file_roundtrip.py)
  legacy parametrize already passes `accept_old=True` — keep.
- Grep for bare `load(` / `CellpyCell().load(` on v4–v7 fixtures without
  `accept_old=True` and fix those call sites.
- Any test expecting the old “Try loading setting accept_old=True” string must
  match the new freeze message.

### 4. CI

No workflow edits if the new suite is `essential` — Tier 1 already runs it.
Mention the suite name in `tests/README.md` in one line if that file already
indexes essential file-IO suites.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/readers/cellreader.py` | `load(..., accept_old=False)` default + docstring |
| `cellpy/readers/cellpy_file/read.py` | Freeze `WrongFileVersion` message for `version < HDF5_FILE_VERSION` when not `accept_old` |
| `tests/test_file_format_compat_matrix.py` | **New** — parametrized matrix (essential) |
| `tests/test_cellpy_file_*.py` / other loaders | Only if grep finds callers broken by default flip |
| `docs/getting_started/migration_v1_to_v2.md` | Support-matrix row aligned with freeze |
| `tests/README.md` | One-line pointer to the matrix suite (if index exists) |

**Out of scope:** implementing `convert --to` (done); v1.x backport of the warning
(unless you opt in); #574 release checklist; rewriting characterization suites.

## Test strategy

```bash
uv run pytest -m essential
uv run pytest tests/test_file_format_compat_matrix.py tests/test_cli_api.py -k convert tests/test_cellpy_file_v9.py tests/test_cellpy_file_roundtrip.py -q
```

(Project toolchain: `uv run pytest`; conda `cellpy_dev_313` also fine locally.)

## Open questions

_Resolved on Accept (2026-07-24) — recommended answers locked:_

1. **Freeze default:** flip `accept_old` default to `False` in this PR.
2. **2.x convert escape:** keep `cli_api.convert` able to rewrite v&lt;8 (`accept_old=True`).
3. **Freeze message copy:** use
   `File format too old (v{n}): use cellpy 1.x \`cellpy convert\` to rewrite to v8+, then open in 2.x`
   (tweak only if wording is awkward in the raise site).
4. **v1.x warning:** out of scope — follow-up later if needed.

## Scope check

One cohesive PR (matrix + freeze + migration-doc sync). Not an epic. If you reject
the freeze (Q1 = keep permissive), shrink to tests + docs-only and mark the release
matrix row as “still reads v4–v7 via accept_old default” — that is a **plan revise**,
not silent scope cut.
