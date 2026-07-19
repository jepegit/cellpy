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
shared-value pair. **Legacy-only** attributes (columns the flip does not rename)
resolve to their unchanged legacy name via the legacy ``BaseHeaders`` object —
``to_native`` passes those columns through untouched, so the native frame still
carries them under that name (e.g. ``headers_normal.datetime_txt`` → ``date_time``,
``headers_normal.test_id_txt`` → ``test_id``).

**Wired into ``CellpyCell`` at the flip (Stage 5a).** When the runtime is native,
``CellpyCell`` substitutes these shims for the legacy ``Headers*`` objects so
legacy attribute access keeps resolving to the native column names.

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

# Frame label -> the public replacement frame on ``CellpyCell.schema`` (#558).
# Note the frames are spelled as they are on ``c.data`` (raw/steps/summary),
# not as cellpy-core spells them (raw/step/cycle).
_SCHEMA_FRAME = {
    "raw": "raw",
    "step": "steps",
    "cycle": "summary",
}


class LegacyHeaderShim:
    """Resolve legacy header attributes/keys to native column names, with a warning.

    Args:
        frame: The Schema frame this shim covers — ``"raw"``, ``"step"`` or
            ``"cycle"``.
        native_cols: The native ``config.Cols`` object for that frame; native
            attribute access passes through to it unchanged (no warning).
        legacy_cols: The legacy ``BaseHeaders`` object for that frame
            (``HeadersNormal`` / ``HeadersStepTable`` / ``HeadersSummary``).
            Used to resolve **legacy-only** attributes: columns the flip does
            not rename (``to_native`` passes them through unchanged), so the
            native frame still carries them under their legacy name — the shim
            returns that name rather than raising.
    """

    def __init__(
        self,
        frame: str,
        native_cols: "config.Cols",
        legacy_cols: object | None = None,
    ) -> None:
        if frame not in mapping.LEGACY_ATTR_TO_SCHEMA:
            raise ValueError(
                f"unknown frame {frame!r}; expected one of "
                f"{sorted(mapping.LEGACY_ATTR_TO_SCHEMA)}"
            )
        # Set via __dict__ so __getattr__ never sees these.
        object.__setattr__(self, "_frame", frame)
        object.__setattr__(self, "_native", native_cols)
        object.__setattr__(self, "_legacy", legacy_cols)

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
            self._warn(name, native_name)
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
                    self._warn(name, f"{native_base}{suffix}")
                    return f"{native_base}{suffix}"

        # Legacy-only attribute: the flip does not rename this column, so the
        # native frame carries it under its (unchanged) legacy name. Return that
        # name — no warning, because there is no native name to migrate to.
        legacy = self._legacy
        if legacy is not None and not name.startswith("_") and hasattr(legacy, name):
            return getattr(legacy, name)

        raise KeyError(
            f"{_FRAME_LABEL[frame]}: {name!r} is not a native column and has no "
            f"legacy mapping (unknown attribute)."
        )

    def _warn(self, name: str, native_name: str) -> None:
        label = _FRAME_LABEL[self._frame]
        # Name the exact replacement, not just the concept: the user needs the
        # attribute they should type, and we know it here (conventions plan §3).
        replacement = f"c.schema.{_SCHEMA_FRAME[self._frame]}.{native_name}"
        warn_once(
            f"{label}.{name}",
            replacement,
            removal="2.1",
            introduced="2.0",
            stacklevel=4,
        )

    # -- access protocols -----------------------------------------------------
    def __getattr__(self, name: str) -> str:
        # Never resolve dunder/private names: no legacy header attribute starts
        # with "_", and resolving them would recurse on the shim's own private
        # attrs (_frame/_native/_legacy) before they exist during copy/pickle
        # reconstruction. Raising AttributeError lets copy/deepcopy fall back to
        # the default reconstruction path.
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._resolve(name)
        except KeyError as exc:
            raise AttributeError(str(exc)) from None

    def __getitem__(self, key: str) -> str:
        return self._resolve(key)


def build_legacy_shims(schema: "config.Schema") -> dict[str, LegacyHeaderShim]:
    """Return the three legacy-header shims for a native ``config.Schema``.

    Keys are the ``CellpyCell`` header attribute names the flip (Stage 5) points
    at these shims: ``headers_normal`` / ``headers_step_table`` /
    ``headers_summary``. Each shim also gets the matching legacy ``BaseHeaders``
    object so legacy-only (un-renamed) columns keep resolving to their name.
    """
    from cellpy.parameters.internal_settings import (
        get_headers_normal,
        get_headers_step_table,
        get_headers_summary,
    )

    return {
        "headers_normal": LegacyHeaderShim("raw", schema.raw, get_headers_normal()),
        "headers_step_table": LegacyHeaderShim(
            "step", schema.step, get_headers_step_table()
        ),
        "headers_summary": LegacyHeaderShim(
            "cycle", schema.cycle, get_headers_summary()
        ),
    }
