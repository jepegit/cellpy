"""Per-cell frame header resolution for plotting (#567 / #647).

Replaces module-level ``get_headers_*()`` singletons that always answered with
legacy names after the native-headers flip.
"""

from __future__ import annotations

from cellpycore.legacy import mapping

#: cellpy-core mapping key per frame.
_MAPPING_FRAME = {"raw": "raw", "steps": "step", "summary": "cycle"}


class LiveHeaders:
    """Column names for *this cell's* frames, keyed by the 1.x attribute names.

    Resolution goes through the cell's own schema, so this is correct on both
    runtimes: on the legacy runtime ``schema.raw.potential`` still answers
    ``"voltage"``.

    Both spellings the old singletons supported are kept, because call sites
    use both: ``hdr["voltage_txt"]`` and ``hdr.voltage_txt``.
    """

    __slots__ = ("_schema", "_frame", "_attrs")

    def __init__(self, c, frame: str):
        self._frame = frame
        self._schema = getattr(c.schema, frame)
        self._attrs = mapping.LEGACY_ATTR_TO_SCHEMA[_MAPPING_FRAME[frame]]

    def _resolve(self, legacy_attr: str) -> str:
        native = self._attrs.get(legacy_attr)
        if native is None:
            try:
                return getattr(self._schema, legacy_attr)
            except AttributeError:
                raise KeyError(
                    f"no {self._frame} column named {legacy_attr!r} on this cell"
                ) from None
        return getattr(self._schema, native)

    def base(self, legacy_attr: str) -> str:
        """The native *stem* of a step-table statistic family.

        Step-table columns are ``<stem>_<statistic>`` (``potential_delta``,
        ``current_min``). The schema exposes the composed columns, not the
        stem, so this reads the stem straight off the mapping — and falls back
        to the legacy spelling on the legacy runtime, where the stem is what
        the frame already uses.
        """
        native = self._attrs.get(legacy_attr)
        if native is None:
            return legacy_attr
        try:
            return getattr(self._schema, native)
        except AttributeError:
            return native

    def stat(self, legacy_attr: str, statistic: str) -> str:
        """``stat("voltage", "delta")`` -> ``"potential_delta"`` (native)."""
        return f"{self.base(legacy_attr)}_{statistic}"

    def __getitem__(self, legacy_attr: str) -> str:
        return self._resolve(legacy_attr)

    def __getattr__(self, legacy_attr: str) -> str:
        return self._resolve(legacy_attr)


# Historical private name used by plotutils / tests (#567).
_LiveHeaders = LiveHeaders
