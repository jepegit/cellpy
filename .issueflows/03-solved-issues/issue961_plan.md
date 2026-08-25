# Issue #961 plan

## Goal

When an `env_file` from `cellpy.toml` is missing, `OtherPath` remote auth must
say so. Today the user only sees `UnderDefined` about `CELLPY_PASSWORD` /
`CELLPY_KEY_FILENAME`.

## Constraints

- Do not change env-file *resolution* (no silent home fallback). Messages only.
- Keep the existing `UnderDefined` exception type.
- Relative `env_file` values stay cwd-relative; the message names the resolved
  path and, if present, a same-named file under the home directory.

### Prior art

- `cellpy.internals.otherpath._credentials_from_env` — raises `UnderDefined`.
- `cellpy.internals.connections.check_connection` — prints the same text.
- `cellpy.config.loader._collect_env_overrides` — skips a missing file silently.
- `cellpy.parameters.prmreader._load_env_file` — debug-only "No .env file found";
  already tries `home / name` as a fallback (legacy path only).

## Approach

1. Shared helper that builds the credential-missing message plus an env-file
   hint (configured path, resolved absolute, exists?, home-named sibling).
2. Use it in `_credentials_from_env` and the `check_connection` print.
3. `logging.warning` in `_collect_env_overrides` when the configured file is
   absent (load-time, before any remote access).

## Files to touch

- `cellpy/internals/otherpath.py` — helper + richer `UnderDefined`.
- `cellpy/internals/connections.py` — same message text.
- `cellpy/config/loader.py` — warn when env file missing.
- `tests/test_otherpaths.py` or `tests/test_config.py` — cover the hint.
- `.issueflows/04-designs-and-guides/test-registry.md` — new essential row.

## Test strategy

`uv run pytest -m essential` (PR gate). New unit tests for the missing-file
hint and the loader warning. Mark the hint test essential.

## Open questions

None — yolo-fit, messages only.
