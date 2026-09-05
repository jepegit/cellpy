# Issue #993 — plan

## Goal

Every `` See `name` `` cross-reference in `cellpy/` names its target by an
importable dotted path, and a test keeps it that way.

## Approach

24 bare references remain after #968, all thin delegates whose target module is
named in the same file's imports:

| where | target module |
|---|---|
| `cellpy/readers/cellreader.py` — split/drop delegates (11) | `cellpy.readers.slicing` |
| `cellpy/readers/cellreader.py` — export / to_csv / to_excel / cap_mod (8) | `cellpy.exporters.tabular` |
| `cellpy/readers/cellreader.py` — get_dcap / get_ccap / get_cap / _get_cap / get_ocv (5) | `cellpy.readers.capacity_curves` |
| `cellpy/plotting/registry.py` — `See \`families\`` (1) | `cellpy.plotting.registry` |

Rewrite each as `` See `cellpy.<module>.<name>` `` — the spelling already used by
the 16 references that kept their path, and one `test_no_sphinx_doc_roles.py`
allows (it bans `:role:` prefixes, not dotted names).

## Files to touch

- `cellpy/readers/cellreader.py`, `cellpy/plotting/registry.py`.
- `tests/test_doc_cross_references.py` (new) — the property test.

## Test strategy

New test scans `cellpy/**/*.py` for `` See `X` `` and asserts each `X` is dotted
and resolves: import the module part, then walk the remaining attributes. A bare
name fails (nothing to import), which is exactly the regression #968 introduced.
Mark `essential` — it is cheap and it is the only guard on the targets.

## Constraints

Only the reference text changes; no behaviour, no docstring rewrites beyond the
dotted path. Where a bare name has no single obvious target, leave it and note
it (none of the 24 are ambiguous — each sits one line above its delegate call).
