# Issue #454 — Stage 1.9: Config — `cellpy setup` rewrite and migration UX

GitHub: https://github.com/jepegit/cellpy/issues/454
Labels: cellpy2-stage1

## Goal

Config plan Step 5: `cellpy setup` generates `cellpy.toml` from the models
(single source of truth — docs render from the same models); detects an existing
`.cellpy_prms_<user>.conf` and offers `cellpy setup migrate` (one-time YAML→TOML
conversion); folder-creation logic unchanged; `cellpy info --config` prints resolved
values with provenance.

## Acceptance

- `cellpy setup` on a clean machine produces a valid, commented `cellpy.toml`;
  `migrate` converts the test fixture conf losslessly (parity vs #430 round-trip).
- CLI tests migrated with the CLI.
