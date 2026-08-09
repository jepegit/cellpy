# Plan: #849 scrub instrument credentials from file dump

## Goal

Honour `model_dump_for_file()` contract: never write legacy Arbin `SQL_PWD` /
`SQL_UID` (or other credential-ish instrument keys) to `cellpy.toml`, and stop
silently accepting them on TOML load.

## Constraints

- Env-only secrets stay the rule (existing `[secrets]` rejection).
- Legacy YAML migration: drop instrument credential keys with a warning (do
  not strand users), same spirit as `_drop_legacy_secrets`.
- KISS: scrub/reject known keys; do not redesign `ArbinConfig` as SecretStr in
  this issue.

### Prior art

- `CellpyConfig.model_dump_for_file` — pops `[secrets]` only today.
- `_reject_secrets_from_file` / `_drop_legacy_secrets` in `loader.py`.
- `tests/test_config_secrets.py` — essential suite for this contract.

## Approach

1. Shared helper listing credential-ish instrument keys (`SQL_PWD`, `SQL_UID`,
   `*PASSWORD*`, `*_PWD` / `PWD` suffixes).
2. `model_dump_for_file`: deep-scrub instruments before return.
3. TOML load: reject those keys with `ConfigurationError` (symmetric to
   `[secrets]`).
4. Legacy YAML: pop + warn.
5. Extend `test_config_secrets.py` with the issue reproduction.

## Files to touch

- `cellpy/config/models.py` — scrub in dump
- `cellpy/config/loader.py` — reject / drop on load
- `tests/test_config_secrets.py` — new essential cases
- issue tracking + HISTORY

## Test strategy

`uv run pytest tests/test_config_secrets.py -q` then `uv run pytest -m essential -q`.

## Open questions

None.
