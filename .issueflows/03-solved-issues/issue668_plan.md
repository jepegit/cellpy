# Issue #668 — Plan

## Goal

Fix two 1.x batch-workflow crashes from the loader notebook: `b.plot(...)`
failing when the summary cycle index is unnamed, and `make_summary()` failing
when `cycle_mode` is still list-shaped. Confirm what (if anything) still needs
work on the v2/`master` line and track that separately.

## Constraints

- **Target branch:** `v1.x` (label `v1x`). PR against `v1.x`, not `master`.
- **Worktree:** `../cellpy-v1x` on `668-batch-bugs` (main `cellpy` checkout stays on other work).
- **Fixes-only** on `v1.x` — no refactors, no dependency churn beyond what a fix needs
  (`cellpycore==0.2.1` pin stays unless a core patch release is required and agreed).
- Prefer the smallest backport that matches known-good `master` behaviour over a
  new design.
- Do not change public batch API surface.

### Prior art

- **`master` #658** — deleted `batch_plotters.py`, moved frame prep to
  [`cellpy/plotting/batch_summary.py`](../../../../cellpy/cellpy/plotting/batch_summary.py).
  Explicit fix: name unnamed summary index to `cycle_index` before `reset_index`
  (see `issue658_status.md`). **Mirror this into v1.x `batch_plotters.py`.**
- **`master` load unwrap** — [`cellpy/readers/cellpy_file/read.py`](../../../../cellpy/cellpy/readers/cellpy_file/read.py)
  + recursive `test_meta._unwrap` (and tests in `tests/test_test_meta_collection.py`)
  for double-nested `cycle_mode` (e.g. `[['anode']]`). **Port a minimal unwrap to v1.x.**
- **`cellpycore.OldCellpyCellCore.cycle_mode`** — one-level `m[0]` getter; setter
  keeps lists as lists; `_cycle_mode_to_test_mode` assumes `str` and calls `.strip()`.
  Shared by both lines; still fragile even when consumer unwraps on load.
- Toolbox (`00-tools/`): nothing for batch plots / cycle_mode. Graphify: absent in this worktree.

### v2 / master impact check (done during planning)

| Symptom | On `master`? | Action |
|---------|--------------|--------|
| A. `b.plot` / `cycle_index` KeyError → `NoneType.show` | **No** — fixed in #658 (`batch_summary.py` names index; old `batch_plotters.py` deleted) | No v2 issue |
| B. `make_summary` / `cycle_mode` list → `.strip()` | **Partly mitigated** on consumer load path; **still fragile in `cellpycore`** | Opened [cellpy/cellpy-core#142](https://github.com/cellpy/cellpy-core/issues/142) |

## Approach

### 0. Inform v2 / core (tracking issue)

**Done:** [cellpy/cellpy-core#142](https://github.com/cellpy/cellpy-core/issues/142) — harden:

1. `OldCellpyCellCore.cycle_mode` getter: recursively unwrap 1-element lists/tuples to a scalar (same semantics as cellpy `test_meta._unwrap`).
2. Setter: store a **scalar** (unwrap first), not a list of lowered strings.
3. `_cycle_mode_to_test_mode`: accept list/tuple by unwrapping before `.strip()`; keep current string behaviour.
4. Tests: nested `[['anode']]`, `['anode']`, scalar `'anode'`, `None`.

Note on the cellpy #668 thread once the core issue number exists. No change required
to master’s batch plotter path for symptom A.

### 1. Fix A — `b.plot` / summary frame (v1.x only)

In [`cellpy/utils/batch_tools/batch_plotters.py`](../../cellpy/utils/batch_tools/batch_plotters.py)
`generate_summary_frame_for_plotting`:

- After `pd.concat(...)`, if `summaries.index.name is None`, set it to
  `hdr_summary["cycle_index"]` (same as master `batch_summary.py`).
- In `summary_plotting_engine`, only call `canvas.show()` when `canvas is not None`
  (secondary crash after failed frame prep).

### 2. Fix B — `cycle_mode` list on `make_summary` (v1.x consumer)

Without waiting for a core release:

- Add a tiny recursive `_unwrap` helper on v1.x (either a few lines next to the
  load site, or a minimal shared helper — prefer one place used by load + property).
- After `meta_test_dependent.update(as_list=True, ...)` in
  [`cellpy/readers/cellpy_file/read.py`](../../cellpy/readers/cellpy_file/read.py)
  (and `legacy_read.py` if it has the same path), assign
  `cycle_mode = _unwrap(...)`.
- Harden [`CellpyCell.cycle_mode`](../../cellpy/readers/cellreader.py) getter to
  recursively unwrap (current code only does one level — insufficient for
  `[['anode']]`).

Do **not** bump `cellpycore` in this PR unless we decide the consumer-only fix is
insufficient for the reported notebook path after tests.

### 3. Ordering

1. Core tracking issue (step 0).
2. Fix A + tests.
3. Fix B + tests.
4. Run essential suite on the worktree.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/utils/batch_tools/batch_plotters.py` | Name cycle index before `reset_index`; guard `canvas.show()` |
| `cellpy/readers/cellpy_file/read.py` | Unwrap `cycle_mode` after list-shaped meta load |
| `cellpy/readers/cellpy_file/legacy_read.py` | Same unwrap if applicable |
| `cellpy/readers/cellreader.py` | Recursive unwrap in `cycle_mode` getter |
| `tests/…` (new or extend existing batch / meta tests) | Regression for A + B |
| `.issueflows/01-current-issues/issue668_status.md` | Status after build |

Out of scope for this PR: deleting `batch_plotters.py`, porting #658 plotting package, core release/pin bump (follow-up via the new core issue).

## Test strategy

In `cellpy-v1x` worktree:

```bash
uv sync
uv run pytest -m essential
```

Plus focused tests:

- **A:** Build a multi-cell summary concat with unnamed index; assert frame prep
  yields a `cycle_index` column (or call the plot helper with `plotly_show=False`
  and assert no `AttributeError`). Prefer unit-level frame prep if full batch
  fixtures are heavy.
- **B:** Meta / cell with `cycle_mode` as `['anode']` and `[['anode']]`;
  `make_summary()` must not raise `AttributeError` on `.strip()`.

Mark merge-gate tests `@pytest.mark.essential` only if they stay fast and stable.

## Open questions

1. **Core issue home:** create under `cellpy/cellpy-core` (recommended) vs only a
   `jepegit/cellpy` `master`/`v2` reminder issue. Default: **core**.
2. **Pin bump:** if consumer unwrap alone is enough for the notebook, leave
   `cellpycore==0.2.1` and let the core issue ship later. Agree?
3. **Scope of B:** unwrap only `cycle_mode`, or also other list-boxed meta fields
   on load (master unwraps via a helper used more broadly)? Default: **cycle_mode
   only** on v1.x to keep the PR small.
