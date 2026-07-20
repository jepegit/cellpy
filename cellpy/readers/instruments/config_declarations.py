"""Derive loader declarations from the existing configurations (issue #560).

Every ``configurations/*`` module already says how its vendor columns map to
the *legacy* header attributes, and cellpy-core already says how legacy
attributes map to *native* columns. Composing the two gives vendor → native
without anyone retyping sixteen column maps::

    config: legacy_attr -> vendor        (normal_headers_renaming_dict)
    core:   legacy_attr -> native        (mapping.LEGACY_ATTR_TO_SCHEMA)
    ------------------------------------------------------------------
    derived: vendor -> native

Deriving beats transcribing for the obvious reason — a hand-copied map is a
place for silent typos, and a wrong column mapping produces plausible numbers
rather than an error. It also makes the port self-updating: a legacy attribute
with no native counterpart lands in ``passthrough`` today and moves into
``column_map`` by itself the moment cellpy-core adds the entry (the live case
is the energy columns, cellpy-core#139).

This module does **not** change how anything loads. It builds declarations so
they can be compared against the legacy path (see
``tests/test_derived_declarations.py``); switching ingestion over is separate.
"""

from __future__ import annotations

import logging
from types import ModuleType
from typing import Any

from cellpycore.legacy import mapping
from cellpycore.units import CellpyUnits

from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.declarations import (
    LoaderDeclarations,
    ResetGranularity,
)

#: Native columns whose reset granularity a vendor could plausibly differ on.
#: Defaulted to the harmonized-raw target (cycle-cumulative per direction);
#: a configuration that knows better overrides it explicitly.
_CUMULATIVE_DEFAULTS = (
    "cumulative_charge_capacity",
    "cumulative_discharge_capacity",
    "cumulative_charge_energy",
    "cumulative_discharge_energy",
)

#: Capacity columns the legacy ``cumulate_capacity_within_cycle`` post-processor
#: acts on. It touches only the capacities, never the energies.
_CUMULATED_CAPACITIES = (
    "cumulative_charge_capacity",
    "cumulative_discharge_capacity",
)

#: Legacy post-processor → the native column it parses from a duration string.
_DURATION_POST_PROCESSORS = {
    "convert_step_time_to_timedelta": "step_time",
    "convert_test_time_to_timedelta": "test_time",
}

#: Legacy attributes that must not reach the raw frame at all.
#:
#: The vendor's own test identifier is *provenance*, not a measurement: it
#: belongs on ``TestMeta`` (issue #508 routes it to
#: ``meta_test_dependent.test_ID``). Passing it through would also collide with
#: the native ``test_id``, which is the framework-assigned grouping key for
#: merged tests — two different meanings, one name, and the vendor's value
#: would quietly win.
_PROVENANCE_ATTRS = frozenset({"test_id_txt"})


def _legacy_column_name(legacy_attr: str) -> str | None:
    """The column name the legacy path would have used for this attribute."""
    return getattr(get_headers_normal(), legacy_attr, None)


def derive_column_maps(
    renaming: dict[str, str],
) -> tuple[dict[str, str], dict[str, str], list[str]]:
    """Split a configuration's renaming dict into native, passthrough, unknown.

    Args:
        renaming: ``legacy_attr -> vendor column``, as the configurations
            declare it.

    Returns:
        ``(column_map, passthrough, unknown)`` where ``column_map`` is
        vendor → native for attributes cellpy-core can map, ``passthrough`` is
        vendor → legacy column name for real data with no native column yet,
        and ``unknown`` lists attributes that are neither — a configuration
        naming something no longer recognised anywhere.

    A vendor column claimed by more than one legacy attribute is **ambiguous**:
    only one target can win, and the other is silently lost. ``maccor_txt_one``
    does this today, mapping ``Watt-hr`` to both ``power_txt`` and
    ``charge_energy_txt``. The first declaration wins here, matching what the
    legacy path is observed to produce, and the collision is logged rather than
    resolved silently.
    """
    raw_mapping = mapping.LEGACY_ATTR_TO_SCHEMA["raw"]

    column_map: dict[str, str] = {}
    passthrough: dict[str, str] = {}
    unknown: list[str] = []
    claimed: dict[str, str] = {}

    for legacy_attr, vendor in renaming.items():
        if legacy_attr in _PROVENANCE_ATTRS:
            continue

        if vendor in claimed:
            logging.warning(
                "vendor column %r is claimed by both %r and %r; keeping %r "
                "(the first declaration) — the configuration should name one",
                vendor,
                claimed[vendor],
                legacy_attr,
                claimed[vendor],
            )
            continue
        claimed[vendor] = legacy_attr

        native = raw_mapping.get(legacy_attr)
        if native is not None:
            column_map[vendor] = native
            continue
        legacy_name = _legacy_column_name(legacy_attr)
        if legacy_name is not None:
            passthrough[vendor] = legacy_name
            continue
        unknown.append(legacy_attr)

    return column_map, passthrough, unknown


def _config_name(config: Any) -> str:
    """A name for messages, for either shape of configuration.

    Derivation accepts both a ``configurations.*`` **module** (what the shipped
    configurations are) and a live :class:`ModelParameters` **instance** (what a
    loader carries as ``config_params``, including the ones assembled at runtime
    from a YAML file). The two spell their name differently.
    """
    return getattr(config, "__name__", None) or getattr(config, "name", "<configuration>")


def _units_from_configuration(config: ModuleType) -> CellpyUnits:
    raw_units: dict[str, Any] | None = getattr(config, "raw_units", None)
    if not raw_units:
        return CellpyUnits()
    known = {
        key: value
        for key, value in raw_units.items()
        if hasattr(CellpyUnits(), key) and isinstance(value, str)
    }
    return CellpyUnits(**known)


def declarations_from_configuration(
    config: ModuleType | Any,
    *,
    reset_granularity: dict[str, ResetGranularity] | None = None,
    post_hooks: tuple = (),
    timezone: str | None = None,
) -> LoaderDeclarations:
    """Build validated declarations from an existing configuration module.

    Args:
        config: a ``cellpy.readers.instruments.configurations.*`` module, or a
            live ``ModelParameters`` instance (a loader's ``config_params``).
            Both expose the same attribute names, which is what lets the port
            derive declarations from a loader that is already running.
        reset_granularity: overrides for columns whose vendor granularity is
            not the harmonized-raw default. **Read the vendor's data before
            setting one** — a wrong value here silently rescales capacities.
        post_hooks: vendor-quirk callables (e.g. capacity splitting).
        timezone: IANA zone for naive vendor timestamps.

    Returns:
        A validated :class:`LoaderDeclarations`.

    Raises:
        LoaderError: if the derived declarations do not validate — which is the
            point: it happens at import of the configuration, not mid-load.
    """
    renaming = getattr(config, "normal_headers_renaming_dict", None)
    if not renaming:
        raise ValueError(
            f"{_config_name(config)} has no normal_headers_renaming_dict; "
            f"nothing to derive"
        )

    column_map, passthrough, unknown = derive_column_maps(renaming)
    if unknown:
        logging.debug(
            "%s declares legacy attributes with no native or legacy column: %s",
            _config_name(config),
            sorted(unknown),
        )

    targets = set(column_map.values())
    granularity: dict[str, ResetGranularity] = {
        column: ResetGranularity.PER_CYCLE
        for column in _CUMULATIVE_DEFAULTS
        if column in targets
    }

    # A configuration that runs ``cumulate_capacity_within_cycle`` is *stating*
    # that its vendor capacities reset every step: the post-processor offsets
    # each step by the running total of the cycle's completed steps, which is
    # exactly what ``ResetGranularity.PER_STEP`` means. Reading it here is the
    # difference between deriving the granularity and guessing it — and a wrong
    # guess rescales capacities silently.
    post_processors = getattr(config, "post_processors", None) or {}
    if post_processors.get("cumulate_capacity_within_cycle"):
        granularity.update(
            {
                column: ResetGranularity.PER_STEP
                for column in _CUMULATED_CAPACITIES
                if column in targets
            }
        )

    if reset_granularity:
        granularity.update(reset_granularity)

    # Same trick as the granularity above: a configuration that runs
    # ``convert_*_to_timedelta`` is saying its vendor writes that column as an
    # elapsed-time string. The legacy post-processor tolerates both spellings,
    # so declaring it when the vendor already writes seconds costs nothing —
    # ``harmonize()`` only converts string columns.
    durations = tuple(
        column
        for processor, column in _DURATION_POST_PROCESSORS.items()
        if post_processors.get(processor) and column in targets
    )

    return LoaderDeclarations(
        column_map=column_map,
        raw_units=_units_from_configuration(config),
        timezone=timezone,
        reset_granularity=granularity,
        duration_columns=durations,
        passthrough=passthrough,
        post_hooks=post_hooks,
    )
