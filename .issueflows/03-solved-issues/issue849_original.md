# Issue #849: config: model_dump_for_file() writes legacy Arbin SQL credentials in plaintext

Source: https://github.com/jepegit/cellpy/issues/849

## Original issue text

**cellpy version:** 2.1.2a2

## Summary

`CellpyConfig.model_dump_for_file()` is documented as *"Dump config suitable for TOML persistence (secrets excluded)"*, and it does drop the `[secrets]` section. But `ArbinConfig` (and the other instrument models) are `model_config = ConfigDict(extra="allow")`, so the **legacy** Arbin SQL credentials — `SQL_PWD`, `SQL_UID` — pass straight through and get written to `cellpy.toml` in plaintext.

The asymmetry is the dangerous part: a hand-written `[secrets]` block is correctly rejected on load, but the same credential smuggled in under `[instruments.Arbin]` is written **and** silently accepted on reload.

## Reproduction

```python
import tempfile
from pathlib import Path
from cellpy.config.models import CellpyConfig
from cellpy.config.loader import write_toml, load_config, LoadOptions

tmp = Path(tempfile.mkdtemp())
toml_path = tmp / "cellpy.toml"

cfg = CellpyConfig.model_validate(
    {"instruments": {"Arbin": {"SQL_PWD": "hunter2", "SQL_UID": "jepe"}}}
)

write_toml(toml_path, cfg.model_dump_for_file())      # the "secrets excluded" dump
print("hunter2" in toml_path.read_text())             # -> True

res = load_config(None, LoadOptions(user_config_file=toml_path, skip_env=True))
print(res.config.instruments.Arbin.SQL_PWD)           # -> hunter2   (no error)
```

Output:

```
written TOML contains plaintext password: True
['SQL_PWD = "hunter2"', 'SQL_UID = "jepe"']
reload accepted the file (no ConfigurationError)
value round-tripped: hunter2
[secrets] correctly rejected: ConfigurationError
```

## Why this bites app developers

This is on the realistic migration path, not a contrived one:

1. A user has a legacy `.cellpy_prms_*.conf` with a real `Instruments.Arbin.SQL_PWD`.
2. The legacy loader merges it (`_drop_legacy_secrets` only pops the top-level `secrets` key, so `instruments.Arbin.SQL_PWD` survives).
3. Any app offering a **Settings → Save** button calls the documented secrets-safe dump…
4. …and writes the user's database password to `%LOCALAPPDATA%\cellpy\cellpy\cellpy.toml` — a file they'd reasonably share, sync, or commit alongside a project.

We hit this while designing a settings UI for [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui); we now have to scrub `instruments.*.SQL_*` ourselves before writing, which is exactly the kind of thing the `model_dump_for_file()` contract should be handling.

## Suggested fixes (any one would do)

- **Map on legacy load** — translate `Instruments.Arbin.SQL_PWD`/`SQL_UID`/`SQL_server` into the `secrets` section during YAML migration, so they land in the one place that already knows they're credentials.
- **Scrub on dump** — strip known credential-ish keys (`*PWD*`, `*UID*`, `*password*`) from instrument sections in `model_dump_for_file()`.
- **Type them** — declare `SQL_PWD` on `ArbinConfig` as `SecretStr | None` with `exclude=True` rather than letting it ride in on `extra="allow"`.
- **Symmetric guard** — have `_reject_secrets_from_file` (or a warning) also catch credential keys in instrument sections, so a file that does contain one is not silently honoured.

Happy to send a PR if you have a preference on which route.
