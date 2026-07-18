"""Legacy-header attribute shim (native-headers flip, D6 / Stage 2).

After the flip renames the on-frame columns to the native ``cellpycore``
schema, code that still references headers **by legacy attribute** —
``headers_normal.voltage_txt``, ``hdr_steps.cycle``,
``hdr_summary["charge_capacity"]`` — must keep resolving to the (now native)
column name. This shim does that: it wraps a native ``config.Cols`` object for
one frame and, on a legacy attribute/key, returns the native column name and
emits a one-time ``DeprecationWarning``. Native-name access passes straight
through without warning.

All legacy→native knowledge lives in ``cellpycore.legacy.mapping`` — this
module only adapts it to attribute/subscript access and owns the warning. The
mapping already handles the ``discharge_capacity`` / ``discharge_capacity_raw``
shared-value pair and lists legacy-only attributes (raised here as a clear
error).

**Not wired into ``CellpyCell`` yet.** The flip (Stage 5) substitutes these
shims for the legacy ``Headers*`` objects; until then this module is inert,
tested infrastructure and changes no runtime behavior.

Scope note: statistic step columns composed by callers as ``f"{hdr.voltage}_avr"``
are *not* interceptable here (they are built strings, not attribute access) —
those callers migrate in Stage 3. Summary specific columns accessed by key
(``hdr_summary["charge_capacity_gravimetric"]``) *are* handled, via postfix
decomposition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cellpycore.legacy import mapping

from cellpy._deprecation import warn_once

if TYPE_CHECKING:
    from cellpycore import config

# HeadersSummary specific-column postfixes (native and legacy names match).
_SPECIFIC_MODES = ("gravimetric", "areal", "absolute")

# Frame label -> the attribute name a warning should mention.
_FRAME_LABEL = {
    "raw": "headers_normal",
    "step": "headers_step_table",
    "cycle": "headers_summary",
}


class LegacyHeaderShim:
    """Resolve legacy header attributes/keys to native column names, with a warning.

    Args:
        frame: The Schema frame this shim covers — ``"raw"``, ``"step"`` or
            ``"cycle"``.
        native_cols: The native ``config.Cols`` object for that frame; native
            attribute access passes through to it unchanged (no warning).
    """

    def __init__(self, frame: str, native_cols: "config.Cols") -> None:
        if frame not in mapping.LEGACY_ATTR_TO_SCHEMA:
            raise ValueError(
                f"unknown frame {frame!r}; expected one of "
                f"{sorted(mapping.LEGACY_ATTR_TO_SCHEMA)}"
            )
        # Set via __dict__ so __getattr__ never sees these.
        object.__setattr__(self, "_frame", frame)
        object.__setattr__(self, "_native", native_cols)

    # -- resolution -----------------------------------------------------------
    def _resolve(self, name: str) -> str:
        frame = self._frame
        native = self._native

        # Native attribute -> pass through, no warning.
        if not name.startswith("_") and hasattr(native, name):
            return getattr(native, name)

        # Direct legacy attribute -> native name (+ warning).
        try:
            native_name = mapping.legacy_attr_to_native(frame, name)
        except KeyError:
            native_name = None

        if native_name is not None:
            self._warn(name)
            return native_name

        # Summary specific column by key: strip the postfix, resolve the base,
        # re-attach the (identical) native postfix.
        if frame == "cycle":
            for mode in _SPECIFIC_MODES:
                suffix = f"_{mode}"
                if name.endswith(suffix):
                    base = name[: -len(suffix)]
                    try:
                        native_base = mapping.legacy_attr_to_native("cycle", base)
                    except KeyError:
                        break
                    self._warn(name)
                    return f"{native_base}{suffix}"

        raise KeyError(
            f"{_FRAME_LABEL[frame]}: {name!r} is not a native column and has no "
            f"legacy mapping (legacy-only or unknown attribute)."
        )

    def _warn(self, name: str) -> None:
        label = _FRAME_LABEL[self._frame]
        warn_once(
            f"{label}.{name}",
            "the native cellpycore schema column names",
            removal="2.1",
            introduced="2.0",
            stacklevel=4,
        )

    # -- access protocols -----------------------------------------------------
    def __getattr__(self, name: str) -> str:
        # __getattr__ only fires when normal attribute lookup fails, so the
        # real instance attributes (_frame/_native) never reach here.
        try:
            return self._resolve(name)
        except KeyError as exc:
            raise AttributeError(str(exc)) from None

    def __getitem__(self, key: str) -> str:
        return self._resolve(key)


def build_legacy_shims(schema: "config.Schema") -> dict[str, LegacyHeaderShim]:
    """Return the three legacy-header shims for a native ``config.Schema``.

    Keys are the ``CellpyCell`` header attribute names the flip (Stage 5) will
    point at these shims: ``headers_normal`` / ``headers_step_table`` /
    ``headers_summary``.
    """
    return {
        "headers_normal": LegacyHeaderShim("raw", schema.raw),
        "headers_step_table": LegacyHeaderShim("step", schema.step),
        "headers_summary": LegacyHeaderShim("cycle", schema.cycle),
    }
