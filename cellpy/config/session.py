"""Config session singleton and scoped overrides."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Iterator

from cellpy.config.loader import LoadOptions, LoadResult, load_config
from cellpy.config.models import CellpyConfig
from cellpy.config.sources import ProvenanceRegistry

_session: LoadResult | None = None
_override_stack: list[dict[str, Any]] = []
_load_options: LoadOptions | None = None


def _get_session() -> LoadResult:
    global _session
    if _session is None:
        reload()
    return _session


def get_config() -> CellpyConfig:
    return _get_session().config


def get_provenance() -> ProvenanceRegistry:
    return _get_session().provenance


def sources() -> dict[str, str]:
    return get_provenance().as_dict()


def reload(
    overrides: dict[str, Any] | None = None,
    *,
    options: LoadOptions | None = None,
) -> CellpyConfig:
    """Explicit (re)load from layered sources."""

    global _session, _load_options
    if options is not None:
        _load_options = options
    opts = _load_options or LoadOptions()
    merged_overrides: dict[str, Any] = {}
    for layer in _override_stack:
        merged_overrides = _merge_dicts(merged_overrides, layer)
    if overrides:
        merged_overrides = _merge_dicts(merged_overrides, overrides)
    _session = load_config(merged_overrides or None, opts)
    return _session.config


def reset_session() -> None:
    """Clear cached config (tests)."""

    global _session, _override_stack, _load_options
    _session = None
    _override_stack = []
    _load_options = None


def set_load_options(options: LoadOptions | None) -> None:
    global _load_options
    _load_options = options


@contextmanager
def override(**sections: Any) -> Iterator[CellpyConfig]:
    """Scoped runtime overrides (stacked, LIFO restore)."""

    payload = {key: value for key, value in sections.items() if value is not None}
    _override_stack.append(payload)
    try:
        reload()
        yield get_config()
    finally:
        _override_stack.pop()
        reload()


def _merge_dicts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
