"""Config session singleton and scoped overrides."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from typing import Any, Iterator

from cellpy.config.loader import LoadOptions, LoadResult, load_config
from cellpy.config.models import CellpyConfig
from cellpy.config.sources import ProvenanceRegistry

_session: LoadResult | None = None
_load_options: LoadOptions | None = None

# Per-thread / per-async-task override state. The process-global ``_session``
# stays the unloaded base; ``override()`` must not mutate it or concurrent
# workers cross-talk (#850).
_override_stack_var: ContextVar[tuple[dict[str, Any], ...]] = ContextVar(
    "cellpy_config_override_stack", default=()
)
_override_config_var: ContextVar[CellpyConfig | None] = ContextVar(
    "cellpy_config_override_config", default=None
)


def _get_session() -> LoadResult:
    global _session
    if _session is None:
        reload()
    return _session


def get_config() -> CellpyConfig:
    overridden = _override_config_var.get()
    if overridden is not None:
        return overridden
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
    """Explicit (re)load from layered sources into the process-global session.

    Runtime ``override()`` layers are context-local and are not baked into the
    global session. If called while an ``override()`` block is active in this
    context, the context-local config is rebuilt on top of the new session.
    """

    global _session, _load_options
    if options is not None:
        _load_options = options
    opts = _load_options or LoadOptions()
    _session = load_config(overrides, opts)
    stack = _override_stack_var.get()
    if stack:
        _override_config_var.set(_config_with_overrides(stack))
    return get_config()


def reset_session() -> None:
    """Clear cached config (tests)."""

    global _session, _load_options
    _session = None
    _load_options = None
    _override_stack_var.set(())
    _override_config_var.set(None)


def set_load_options(options: LoadOptions | None) -> None:
    global _load_options
    _load_options = options


@contextmanager
def override(**sections: Any) -> Iterator[CellpyConfig]:
    """Scoped runtime overrides (stacked, LIFO restore).

    Isolation is per thread and per asyncio task via ``contextvars``. Nested
    ``override()`` blocks in the same context still stack. Concurrent threads
    each see only their own layers.

    Note:
        ``reload()`` and ``set_load_options()`` remain process-global.
    """

    payload = {key: value for key, value in sections.items() if value is not None}
    stack = _override_stack_var.get() + (payload,)
    token_stack = _override_stack_var.set(stack)
    cfg = _config_with_overrides(stack)
    token_cfg = _override_config_var.set(cfg)
    try:
        yield cfg
    finally:
        _override_config_var.reset(token_cfg)
        _override_stack_var.reset(token_stack)


def _config_with_overrides(stack: tuple[dict[str, Any], ...]) -> CellpyConfig:
    """Build a CellpyConfig from the session base plus context override layers."""

    data = _get_session().config.model_dump(mode="python")
    for layer in stack:
        data = _merge_dicts(data, layer)
    return CellpyConfig.model_validate(data)


def _merge_dicts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
