# Issue #561 — plan

## Goal

Close the tier-3 loader decisions: confirm the settled port/park outcomes are
on `master`, fill any remaining acceptance gap (notably `check_loader` for the
two ports), and close #561. The supported-instrument matrix stays on #572.

## Constraints

- Decisions already recorded in
  [`architecture-plan/cellpy2-loader-port-and-extraction-plan.md`](../../../architecture-plan/cellpy2-loader-port-and-extraction-plan.md)
  §2.5–2.6 — do not re-debate.
- Maintainer comment (2026-07-20): ports ride with #560; `ext_nda_reader` /
  `local_instrument` done; matrix → #572; **close when the two ports land**.
- No new loader behaviour unless verification finds a real gap.
- Branch `561-tier3-loader-decisions` is **1 behind** `origin/master` — fast-forward
  before coding.

### Prior art

- `cellpy.readers.instruments.testing.check_loader` — full conformance helper;
  used in `tests/test_loader_contract.py` on synthetic loaders only (not on
  real instruments yet).
- `tests/test_loader_port_parity.py` — essential value-parity for
  `biologics_mpr` + `batmo_bdf` (and others).
- `tests/test_biologics_two_stage.py` — biologics `parse`/`declarations` pins.
- `tests/test_parked_loaders.py` — `ext_nda_reader` parked + pointer (#600).
- `cellpy/readers/instruments/ext_nda_reader.py` — parked stub raising
  `LoaderError`.
- `cellpy/readers/instruments/{biologics_mpr,batmo_bdf}.py` — two-stage ports
  already on `master` (#619, #623).
- Toolbox (`.issueflows/00-tools/`): no helper that runs `check_loader` across
  instruments — not needed for this close-out.

## Approach

**This is mostly a close-out, not a new port.**

1. **Fast-forward** the issue branch onto `origin/master`.
2. **Verify on master evidence** (already merged):
   - Port: `biologics_mpr` (#619), `batmo_bdf` decode-in-`parse` (#623).
   - Park: `ext_nda_reader` (#600) + `tests/test_parked_loaders.py`.
   - Record: architecture-plan §2.6; `local_instrument` confirmed, no code.
3. **Acceptance gap — `check_loader`:** parity proves value agreement; acceptance
   still says “ported loaders pass `check_loader`”. Add two thin **essential**
   tests that call `check_loader` on the real classes + in-repo fixtures
   (`testdata/data/biol.mpr`, `testdata/data/batmo_bdf.csv`). Prefer a small
   addition to an existing module (e.g. `test_biologics_two_stage.py` + a short
   batmo block, or one shared `test_tier3_check_loader.py`) over new scaffolding.
4. **Out of scope:** instrument matrix / release-note prose → #572 only
   (optional one-line pointer in the closing comment).
5. **Close #561** after green essential suite; leave #560 close as a separate
   maintainer/action (still OPEN on GitHub despite local Done).

## Files to touch

| Path | Change |
|------|--------|
| `tests/test_biologics_two_stage.py` (or new thin test module) | Add `check_loader(DataLoader, Path("testdata/data/biol.mpr"))` essential test |
| `tests/test_batmo.py` or same new module | Same for `batmo_bdf` + `testdata/data/batmo_bdf.csv` |
| `.issueflows/01-current-issues/issue561_status.md` | Written at `/iflow-start` / close — not in this plan step |

No production code expected unless `check_loader` fails and surfaces a real bug.

## Test strategy

```bash
uv run pytest -m essential
uv run pytest tests/test_parked_loaders.py tests/test_biologics_two_stage.py tests/test_batmo.py tests/test_loader_port_parity.py -q
```

New tests must carry `@pytest.mark.essential` so Tier 1 guards the contract.

## Open questions

1. **`check_loader` tests vs pure close?** Recommended: **add the two essential
   `check_loader` calls** so acceptance is literal. Alternative: close with
   parity + parked tests as sufficient evidence and skip new tests.
2. **Also close GitHub #560 in this flow?** Recommended: **no** — separate
   `/iflow-close` / comment on #560; this issue only closes #561.
3. **Architecture-plan edit?** Recommended: **none** — §2.6 already records
   decisions; only amend if verification finds something §2.6 got wrong.
