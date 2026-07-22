# Issue #628: Iterative fixes — update conda yaml files

Interactive `/iflow-fix` session. Fixes logged below; landed via `/iflow-close`.

- [x] Done

## Iterative fixes log

- **2026-07-22** — Sync conda YAMLs with `pyproject.toml`: bump `cellpycore` `0.2.1`→`0.2.3`; add `pyyaml`, `paramiko >= 5.0.0`, `universal-pathlib >= 0.3.10` to `environment.yml`, `environment_dev.yml`, `github_actions_environment.yml`.
- **2026-07-22** — Drop obsolete `fabric` from the three conda YAMLs (replaced by `universal-pathlib` + `paramiko`).
- **2026-07-22** — Move `cellpycore ==0.2.3` from pip to conda-forge deps in all three YAMLs (package now on forge).
