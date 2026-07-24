# Issue #574: Stage 3.17: cellpy 2.0.0 release checklist (benchmark acceptance, gates, tag)

Source: https://github.com/jepegit/cellpy/issues/574

## Original issue text

## Goal

The 2.0 release checklist: benchmark acceptance, final gates, tag and publish.

## Why

The release plan set a hard acceptance bar — **no metric slower than 1.x**, and the flip
(bridge removal + parquet) is *expected* to win on load and summary; if it doesn't, that
is a signal to investigate before shipping, not after.

Plan: `architecture-plan/cellpy2-release-and-branching-plan.md` §4 and §6;
architecture plan §6 row 3.6.

## Gates

- [ ] Benchmarks vs the GHA-captured v1.x baselines: no metric slower; load and summary
      show the expected bridge-removal win (tiered gate per #476).
- [ ] Value-parity oracle green on all golden cells, with the exception list explicit
      and named (no silently widened tolerances).
- [ ] Full CI suite green — `essential (linux / uv)` **and** `full (linux / uv)`.
- [ ] `DEPRECATIONS.md` complete; migration guide published.
- [ ] Dependency budget applied; `cellpycore` pinned to an exact released version.
- [ ] Docs build published.
- [ ] Every other Stage-3 sub-issue closed.

## Then

- [ ] Tag `v2.0.0`, publish to PyPI, update the conda feedstock.
- [ ] Confirm the `v1.x` branch state and start the 12-month bugfix-only window
      (decision #438-6) from this date.

## Comments (curated summary)

- **Additional tasks**:
  - Check alignment with guiding docs under `.issueflows/04-designs-and-guides`; update those docs if needed.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-23._
