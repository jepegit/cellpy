# Status: issue #768 — Release v2.1

- [x] Done

## What's done

- Plan accepted; open questions locked (2026-07-28).
- **Phase A+B:** host-local Arbin goldens + HISTORY fold → PR
  https://github.com/jepegit/cellpy/pull/769 (merged; CI green on master
  https://github.com/jepegit/cellpy/actions/runs/30377063098).
- **Phase C:** local `pytest -m essential` green on master tip; Tier 2
  `workflow_dispatch` failed (conda/pip matrix noise; not blocking).
- **Phase D:** GitHub release
  https://github.com/jepegit/cellpy/releases/tag/v2.1.0 — `release.yml`
  success https://github.com/jepegit/cellpy/actions/runs/30377967644 —
  PyPI `cellpy==2.1.0` live.
- **Phase E:** docs PR https://github.com/jepegit/cellpy/pull/772 merged
  (batch/collect sources brought onto `v2-docs-stable` for mkdocstrings).
- **Phase F:** feedstock
  https://github.com/conda-forge/cellpy-feedstock/pull/60 merged; conda-forge
  `cellpy` latest **2.1.0**.
- GitHub issue #768 closed.

## Remaining work

- None. Run `/iflow-cleanup` for local branch hygiene.
