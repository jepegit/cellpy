# Issue #560 — plan

## Goal

Finish Stage 3.3: make `harmonize(parse())` the **default** single-file raw
ingestion path, with parity hardened beyond shared numeric columns, then retire
the dual-path safety net where it is no longer needed.

Most of the original issue body is already done on `master` (see Approach /
Done). What remains is the **Phase C** work named in PR #621.

## Constraints

- **No silent data loss on the ingestion path** (oracle / #580 rule): casts,
  drops, and renumbering must warn or fail, not invent wrong values quietly.
- **Default stays off until hardening is green.** `prms.Reader.use_harmonized_raw`
  ships `False` today; flipping it is the last step, not the first.
- **Parity oracle is the gate**, not “suite green with flag on.” Extend the
  oracle (aux + `data_point` / `datapoint_num` + row-count / dedup) so the
  regressions #621 found cannot regress again.
- **cellpycore pin** is already `==0.2.3` (energy mapping from cellpy-core#139).
  No re-pin required for this issue unless a new core release appears mid-work.
- **Tier-3 decisions** live primarily on #561; do not re-litigate park/port
  here. Exception locked for this issue: **`batmo_bdf` is hardened in C1**
  (it misconverts under the flip — #621) so default-on is safe for in-tree
  loaders that still load.
- **Multi-file merges** still go through legacy `_append` + `to_native`
  (`_maybe_use_harmonized_raw` skips `len(file_names) != 1`). Treat the native
  merge path as out of scope unless Open questions say otherwise.
- Plans / fixtures: loader plan in
  [`architecture-plan/cellpy2-loader-port-and-extraction-plan.md`](../../../architecture-plan/cellpy2-loader-port-and-extraction-plan.md);
  branching on `master` per
  [`cellpy-v2-branching.md`](../04-designs-and-guides/cellpy-v2-branching.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| `harmonize()` + identity stamp | [`cellpy/readers/instruments/harmonize.py`](../../cellpy/readers/instruments/harmonize.py) | **Extend** — preserve vendor `datapoint_num`; keep warn+drop for undeclared cols |
| `LoaderDeclarations.aux_map` | [`declarations.py`](../../cellpy/readers/instruments/declarations.py) | **Use** — currently unused by derivation |
| `declarations_from_configuration` | [`config_declarations.py`](../../cellpy/readers/instruments/config_declarations.py) | **Extend** — derive / attach `aux_map` (today always empty) |
| `AutoLoader.parse` / `declarations` | [`base.py`](../../cellpy/readers/instruments/base.py) | Reuse; TxtLoader family already has two-stage entry points |
| Hand-written two-stage ports | `arbin_res`, arbin_sql*, `pec_csv`, `biologics_mpr`, `neware_nda`, `maccor_txt_native` | Mirror their `parse`/`declarations` patterns for remaining gaps |
| Post hooks | [`hooks.py`](../../cellpy/readers/instruments/hooks.py) (`state_splitter`, `forward_fill`, `cycle_number_not_zero`, `drop_last_row_if_worse`) | Reuse; `UNPORTED_POST_PROCESSORS` is already `{}` |
| Opt-in flip | [`cellreader._maybe_use_harmonized_raw`](../../cellpy/readers/cellreader.py) + [`test_harmonized_raw_flip.py`](../../tests/test_harmonized_raw_flip.py) | **Migrate** — harden, then default-on |
| Value-parity oracle | [`tests/test_loader_port_parity.py`](../../tests/test_loader_port_parity.py) (+ synthetic / two-stage suites) | **Extend** — aux + datapoint + row-count |
| Conformance kit check 7 stub | [`testing.py`](../../cellpy/readers/instruments/testing.py) (comment only) | **Add** reset-granularity property once several loaders are default-path |
| Toolbox (`00-tools/`) | scan helpers for headers/prms | None applicable — skip |
| Graphify | absent | skipped |

## Approach

### Already done (do not redo)

Landed on `master` under #560 / deps (non-exhaustive):

1. Declarations derivation (#583); unknown-column warn+drop + Watt-hr→energy (#599).
2. Value-parity oracle + duration / `PER_STEP` fixes (#601); post-processors ported
   until the exception list is empty.
3. Two-stage entry points on `AutoLoader`; `custom` / configs covered via derivation.
4. Per-loader ports: `pec_csv`, `arbin_res`, arbin_sql family, `biologics_mpr`,
   `neware_nda`; epoch / naive-UTC decisions (#610/#611).
5. **Phase B** (#621): `use_harmonized_raw` opt-in (default **off**) after
   `to_native`, with fallback on failure / multi-file.

Issue-body items that are **superseded**: there is no `LegacyLoaderAdapter`
class; the remaining dual path is `loader()+to_native` vs
`_maybe_use_harmonized_raw`.

### Remaining — Phase C (this plan)

Split into stacked PRs on `560-port-tier12-loaders` (or short-lived follow-on
branches merged into it / `master`).

#### C1 — Harden the flip (default still off)

Address the four regressions #621 measured with the flag forced on:

1. **Aux columns**
   - Teach derivation (and/or hand-written `declarations()`) to populate
     `aux_map` from each loader’s existing `get_headers_aux` / wide-aux naming
     (`aux_<nick>_u_<unit>` today on Arbin).
   - Where the legacy name does not already match the
     `aux_<quantity>_<name>` scheme, map explicitly or document a deliberate
     `dropped` / release-note drop.
   - Prove with an oracle assertion: every aux column present on the legacy
     frame for a golden cell is present (or listed in `dropped`) on the
     harmonized frame.

2. **`data_point` / `datapoint_num` preservation**
   - Ensure vendor datapoint lands in `column_map` and survives rename so
     `_stamp_identity` does **not** synthesize `int_range` when the vendor
     already provided values (e.g. Arbin starting at `10000`).
   - Add an oracle check on `datapoint_num` vs legacy `data_point`.

3. **`batmo_bdf` (decision: harden in C1)**
   - Give it a real two-stage path: correct `declarations()` (and `parse()`
     override if the inherited TxtLoader parse mis-handles BDF), plus
     fixture or synthetic parity so `test_time` and other shared columns match
     legacy. Do **not** ship default-on with an allow-list that skips batmo.

4. **`arbin_sql_h5` dedup / row-count**
   - Characterize: 47 vs 34 rows with identical summary. Decide keep-more
     (document as intentional fix) vs match-legacy (restore dedup in parse /
     post-hook). Encode the decision in the oracle (row-count assertion or
     explicit allowed delta).

Deliverable: full suite green with `use_harmonized_raw=True` in a CI job or
local characterization run; flip tests expanded beyond biologics-only.

#### C2 — Flip the default

- Set `use_harmonized_raw: bool = True` in config models / `prms` / prm support
  table; keep the flag as an emergency off-switch.
- Run `uv run pytest -m essential` and full `uv run pytest`.
- Load-path benchmark smoke (existing benchmark suite / release-plan band) —
  no silent perf cliff.
- Release-note bullets for #572 (aux scheme, datapoint preservation, any
  intentional row-count change, default flip).

#### C3 — Retire the dual path (raw single-file)

Once C2 is default and green:

- Stop calling `to_native` **then** replacing raw for single-file loads that
  used the flip successfully (avoid double work / divergent intermediate
  state). Preferred shape: try `harmonize(parse())` first; fall back to
  `loader()+to_native` only when parse/declarations unavailable or fail.
- Leave `to_native` itself in place for **cellpy-file / merge / legacy-frame**
  boundaries — those are not this issue’s delete target.
- Add conformance kit **check 7** (reset-granularity property) into
  `check_loader` / a focused test module now that several loaders ride the
  default path.
- Update issue acceptance text mentally: “no `LegacyLoaderAdapter`” →
  “single-file raw ingestion does not depend on rename-via-`to_native`.”

### Explicit non-goals (unless Open questions override)

- Native multi-file `_append` / merge on harmonized frames.
- Deleting `maccor_txt_native` pilot vs folding into `maccor_txt` (cosmetic).
- Full `neware_xlsx` / `local_instrument` redesign (tier-2/3; #561 territory)
  beyond “safe under default-on.”
- Extraction / curves layer (loader plan Step 2 / G4).

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/readers/instruments/config_declarations.py` | Derive `aux_map` (and any datapoint edge cases) from configurations / aux header helpers |
| `cellpy/readers/instruments/harmonize.py` | Preserve vendor `datapoint_num`; only synthesize when absent |
| `cellpy/readers/instruments/*.py` (esp. `arbin_res`, arbin_sql*, `batmo_bdf`, maybe `neware_xlsx`) | Fill `aux_map` / `dropped` in hand-written `declarations()`; harden batmo |
| `cellpy/readers/cellreader.py` | C2 default; C3 try-harmonize-first ordering for single-file raw |
| `cellpy/config/models.py`, `cellpy/parameters/prms.py`, `tests/prms_support.py` | Default `use_harmonized_raw=True` |
| `tests/test_loader_port_parity.py` (+ flip / two-stage tests) | Aux, datapoint, row-count assertions; broader flip coverage |
| `cellpy/readers/instruments/testing.py` | Implement check 7 stub |
| `.issueflows/01-current-issues/issue560_status.md` | Track C1→C3 (created at `/iflow-start`) |

## Test strategy

Documented commands ([`testing-and-coverage.md`](../04-designs-and-guides/testing-and-coverage.md),
Cloud/`CONTRIBUTING`):

```bash
uv run pytest -m essential
uv run pytest tests/test_loader_port_parity.py tests/test_harmonized_raw_flip.py tests/test_loader_two_stage.py
uv run pytest   # full suite before C2 merge
```

Characterization for C1 (local / CI optional job): run the suite with
`use_harmonized_raw=True` and treat any new failure as a hardening bug, not a
skip.

New / extended tests:

- Aux + `datapoint_num` parity on at least `arbin_res` and one TxtLoader case.
- Flip-on coverage for ≥1 loader that previously lost aux / renumbered datapoints.
- Check 7 reset-granularity property once default path is real.
- Mutation-style: disabling aux_map / datapoint map must fail the new oracle.

## Decisions (locked)

1. **Default-on in this issue:** yes — C1→C2 closes #560; C3 stays in the
   same stacked series.
2. **Multi-file merges:** follow-up issue after #560; keep skip + legacy
   `_append` for now.
3. **`arbin_sql_h5` 47 vs 34 rows:** keep the extra rows (intentional fix);
   assert summaries still match; document in #572.
4. **`batmo_bdf`:** harden in C1 (real declarations/parity) — not an allow-list skip.
5. **Delivery:** stacked PRs under #560 (C1 → C2 → C3), no GitHub sub-issues.

## Open questions

- None — plan accepted 2026-07-22.
