# Issue #662 status

- [x] Done

## What's done

- Root cause: after #453, `load_config` put `.env` into `config.secrets` via `dotenv_values` but left `os.environ` empty; v1.x `OtherPath` still reads `CELLPY_*` via `os.getenv`.
- Fix in `cellpy/config/loader.py`: resolve env file (cwd, then home by basename) and `load_dotenv` on collect.
- Regression: `test_lazy_config_env_file_reaches_otherpath` (`essential`); essential suite green.
- Master check: already OK via `cellpy.config.credentials` — no second PR.
- HISTORY `[Unreleased]` bullet added; closing via `/iflow-close` (PR → `v1.x`).

## Remaining work

- None.
