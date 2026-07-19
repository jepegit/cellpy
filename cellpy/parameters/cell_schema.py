"""The public column-name API for a cell (native-headers Phase 4, issue #558).

``CellpyCell.schema`` answers one question: *what is this column called on the
frames this cell is carrying?* It is the sanctioned replacement for the legacy
``headers_normal`` / ``headers_step_table`` / ``headers_summary`` attributes,
which are now a deprecation shim (``legacy_header_shim``, D6).

    >>> c = cellpy.get(...)                                    # doctest: +SKIP
    >>> c.data.raw[c.schema.raw.potential]                     # doctest: +SKIP
    >>> c.data.summary[c.schema.summary.charge_capacity]       # doctest: +SKIP

**Frame names follow the frames, not cellpy-core.** ``cellpycore.config.Schema``
spells its three frames ``raw`` / ``step`` / ``cycle``; the frames a user holds
are ``c.data.raw`` / ``c.data.steps`` / ``c.data.summary``. This wrapper closes
that gap — ``c.schema.summary`` sits next to ``c.data.summary`` — so there is
exactly one public spelling per frame. Internals that want the cellpy-core
object keep using ``c.core.schema``.

**You always spell the column the native way; the value tracks the runtime.**
``c.schema.raw.potential`` is how you ask for the potential column on *any*
cell. On the native runtime (the cellpy 2 default) it returns ``"potential"``.
On the legacy runtime (``native_schema=False``, the retiring v8/bridge
compatibility path) the frames still carry legacy column names, so the same
attribute returns ``"voltage"`` — the name that actually indexes that frame.
That uniformity is what lets cellpy's own internals, which must run on both
runtimes, be written once against the native vocabulary.

The contract in one line: whatever ``c.schema.<frame>.<column>`` returns is a
valid key into ``c.data.<frame>``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cellpycore.legacy import mapping

if TYPE_CHECKING:
    from cellpycore import config

# HeadersSummary specific-column postfixes (native and legacy names match).
_SPECIFIC_MODES = ("gravimetric", "areal", "absolute")

# native column name -> legacy attribute, per frame (the inverse of the D6
# mapping). Built once: the mapping is a module-level constant in cellpy-core.
_NATIVE_TO_LEGACY_ATTR = {
    frame: {native: legacy for legacy, native in attrs.items()}
    for frame, attrs in mapping.LEGACY_ATTR_TO_SCHEMA.items()
}


class _LegacySpellingAdapter:
    """Serve native column *attributes* off a legacy ``BaseHeaders`` object.

    Only used on the legacy runtime (``native_schema=False``). ``.potential``
    resolves through the inverted D6 mapping to the legacy ``voltage_txt``
    attribute and returns its value (``"voltage"``) — the name that actually
    indexes the legacy frame. Legacy attribute names still work directly, so
    code that has not migrated keeps resolving.
    """

    __slots__ = ("_legacy", "_frame")

    def __init__(self, legacy_cols: object, frame: str) -> None:
        object.__setattr__(self, "_legacy", legacy_cols)
        object.__setattr__(self, "_frame", frame)

    def _resolve(self, name: str) -> str:
        legacy = self._legacy

        # Native name -> legacy attribute -> the legacy column name.
        legacy_attr = _NATIVE_TO_LEGACY_ATTR.get(self._frame, {}).get(name)
        if legacy_attr is not None and hasattr(legacy, legacy_attr):
            return getattr(legacy, legacy_attr)

        # Summary specific columns: strip the postfix, resolve, re-attach.
        if self._frame == "cycle":
            for mode in _SPECIFIC_MODES:
                suffix = f"_{mode}"
                if name.endswith(suffix):
                    base = name[: -len(suffix)]
                    base_attr = _NATIVE_TO_LEGACY_ATTR["cycle"].get(base)
                    if base_attr is not None and hasattr(legacy, base_attr):
                        return f"{getattr(legacy, base_attr)}{suffix}"

        # Legacy spelling, or a column the flip never renamed.
        if not name.startswith("_") and hasattr(legacy, name):
            return getattr(legacy, name)

        raise AttributeError(
            f"{name!r} is not a column of the {self._frame!r} frame on the "
            f"legacy runtime (schema is native-spelled; see "
            f"cellpy.parameters.cell_schema)"
        )

    def __getattr__(self, name: str) -> str:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._resolve(name)

    def __getitem__(self, key: str) -> str:
        return self._resolve(key)


class CellSchema:
    """Column names for one cell's three frames.

    Args:
        core_schema: the ``Schema``-like object owned by the cell's core
            (``CellpyCell.core.schema``). Its ``raw`` / ``step`` / ``cycle``
            frames are re-exposed here as ``raw`` / ``steps`` / ``summary``.
        native: whether the cell's frames carry native column names. When
            False the frames are wrapped so native attribute spelling still
            resolves — to the legacy column names those frames actually use.
    """

    __slots__ = ("_raw", "_steps", "_summary")

    def __init__(self, core_schema: "config.Schema", native: bool = True) -> None:
        if native:
            raw, steps, summary = core_schema.raw, core_schema.step, core_schema.cycle
        else:
            raw = _LegacySpellingAdapter(core_schema.raw, "raw")
            steps = _LegacySpellingAdapter(core_schema.step, "step")
            summary = _LegacySpellingAdapter(core_schema.cycle, "cycle")
        object.__setattr__(self, "_raw", raw)
        object.__setattr__(self, "_steps", steps)
        object.__setattr__(self, "_summary", summary)

    @property
    def raw(self):
        """Column names of ``c.data.raw``."""
        return self._raw

    @property
    def steps(self):
        """Column names of ``c.data.steps``."""
        return self._steps

    @property
    def summary(self):
        """Column names of ``c.data.summary``."""
        return self._summary

    def __repr__(self) -> str:
        return "CellSchema(raw=…, steps=…, summary=…)"
