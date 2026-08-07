# Issue #837: perf(cli): cellpy info --version takes minutes on first run after conda-forge install

Source: https://github.com/jepegit/cellpy/issues/837

## Original issue text

## Context

After installing **cellpy 2.1.1.post6** from **conda-forge** into a fresh conda environment, the first CLI invocations appear frozen:

- `cellpy info --version`
- `cellpy setup -i`

Eventually they complete (not a hard hang). Observed:

| Run | Approx. time |
|---|---|
| First after install (cold) | **many minutes** |
| Second run (warm) | **~5 s** |

Warm ~5 s for a version print is still too slow. Cold multi-minute is a bad install/first-use experience (users give up).

**Not in Stage 5 / 2.2 scope** (see [#783](https://github.com/jepegit/cellpy/issues/783) / stage5 plan). Treat as a **v2.1.x patch-stream** UX/perf bug. Related principles already exist (no import-time config I/O / lazy config singleton) but the CLI entry path still eagerly pulls the heavy stack.

Filed from iterative session [#836](https://github.com/jepegit/cellpy/issues/836).

## Likely cause

`cellpy` console entry → `cellpy.cli` → `cellpy.cli_api` does `import cellpy` (and other heavy modules) at import time. `cellpy/__init__.py` eagerly imports readers / cellreader / etc., so even `info --version` pays the full scientific stack load. Cold cost amplified on Windows/conda by first-time DLL / filesystem / AV cache; warm path still ~5 s.

## Spec

Make light CLI commands (`info --version`, `--help`, and similar) avoid loading the full package graph until needed.

## Acceptance criteria

- [ ] Profile warm import path; identify top cost modules (document briefly in PR / issue comment).
- [ ] `cellpy info --version` does not import the full reader/stack path (lazy imports in `cli` / `cli_api` / package init as needed).
- [ ] Warm `cellpy info --version` is clearly faster than ~5 s on a typical dev machine (target: well under 1–2 s once OS cache is warm; exact budget TBD from profile).
- [ ] Cold first-run after fresh conda install is improved enough that it no longer looks hung for minutes (or docs call out expected first-import cost if residual is environmental).
- [ ] Existing CLI smoke / setup / info behaviors unchanged for heavier commands.
- [ ] Regression guard: smoke or timing note so `--version` cannot silently regress to full-stack import.

## Out of scope

- Stage 5 feature work (live/incremental, instruments, etc.).
- Broader scientific-import refactor beyond what the CLI light path needs.
