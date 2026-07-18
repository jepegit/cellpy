"""Contract test: instrument-config renaming dicts stay in sync with HeadersNormal.

Native-headers flip, Stage 4 (#539). The instrument loaders are already
flip-safe: every cellpy-side raw column name is sourced from ``HeadersNormal``
(the config ``normal_headers_renaming_dict`` is keyed by header **attribute
names**, and ``post_processors.rename_headers`` resolves the final column via
``headers_normal[key]``). So a header rename at the flip touches the header
class only -- *provided* every renaming-dict key is a real ``HeadersNormal``
field.

The one fragility this guards: ``rename_headers`` applies a key only
``if key in headers_normal`` (post_processors.py), so a key that no longer
matches a ``HeadersNormal`` field is **silently skipped** -- the vendor column
would just not be renamed. This test turns that silent skip into a loud
failure: if someone renames a ``HeadersNormal`` field without updating the
configs, the desynced config keys are reported here.

Intentional exceptions are keys for signals cellpy maps from the instrument but
does not (yet) carry as first-class ``HeadersNormal`` columns.
"""

from __future__ import annotations

import dataclasses
import importlib
import pathlib

import pytest

from cellpy.parameters.internal_settings import HeadersNormal

# Keys that are deliberately not HeadersNormal fields: signals some instruments
# expose that cellpy maps but does not carry as a first-class raw column. If a
# new such key is added to a config, list it here (with the reason in review).
KNOWN_NON_HEADER_KEYS = frozenset({"dq_dv_txt", "dv_dq_txt", "acr_txt"})

_HEADER_FIELDS = frozenset(f.name for f in dataclasses.fields(HeadersNormal))


def _config_modules():
    import cellpy.readers.instruments.configurations as configurations

    cfg_dir = pathlib.Path(configurations.__file__).parent
    for path in sorted(cfg_dir.glob("*.py")):
        if path.stem.startswith("__"):
            continue
        module = importlib.import_module(
            f"cellpy.readers.instruments.configurations.{path.stem}"
        )
        if getattr(module, "normal_headers_renaming_dict", None) is not None:
            yield pytest.param(module, id=path.stem)


@pytest.mark.parametrize("module", list(_config_modules()))
def test_config_renaming_keys_are_header_fields(module):
    """Every renaming-dict key is a HeadersNormal field or a known exception."""
    keys = set(module.normal_headers_renaming_dict)
    desynced = keys - _HEADER_FIELDS - KNOWN_NON_HEADER_KEYS
    assert not desynced, (
        f"{module.__name__}: renaming-dict keys are not HeadersNormal fields: "
        f"{sorted(desynced)}. Either the header field was renamed (update the "
        f"config) or add the key to KNOWN_NON_HEADER_KEYS with a reason."
    )


def test_known_non_header_keys_are_all_used():
    """The allowlist stays minimal: every exempted key is actually in some config."""
    used = set()
    for param in _config_modules():
        module = param.values[0]
        used |= set(module.normal_headers_renaming_dict)
    stale = KNOWN_NON_HEADER_KEYS - used
    assert not stale, (
        f"KNOWN_NON_HEADER_KEYS has unused entries {sorted(stale)}; remove them."
    )
