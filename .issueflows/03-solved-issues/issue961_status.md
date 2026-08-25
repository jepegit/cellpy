# Issue #961 status

- [x] Done

## What's done

- `credentials.describe_env_file` / `missing_remote_credentials_message` name
  the configured env file (resolved path, home-named sibling when present).
- `OtherPath._credentials_from_env` and `check_connection` use that text.
- Loader warns at load time when the configured env file is missing.
- Essential tests in `tests/test_config_secrets.py`; registry updated.

## Remaining work

None.
