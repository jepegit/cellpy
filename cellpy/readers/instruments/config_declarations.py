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

from cellpy.exceptions import LoaderError
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.declarations import (
    LoaderDeclarations,
    ResetGranularity,
)
from cellpy.readers.instruments.hooks import (
    cycle_number_not_zero,
    drop_last_row_if_worse,
    state_splitter,
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


def substitute_unit_templates(renaming: dict[str, str], config: Any) -> dict[str, str]:
    """Resolve ``{{ unit }}`` placeholders in vendor column names.

    Neware spells its columns with the unit baked in — ``Current({{ current }})``
    becomes ``Current(A)``. The legacy ``update_headers_with_units``
    post-processor did this by **mutating** ``config_params`` in place at load
    time, which makes the substitution a side effect of having loaded something.

    That side effect does not reach the configuration *module*: a
    ``ModelParameters`` instance carries its own copy. So deriving declarations
    from a module yielded seven neware vendor names still spelled
    ``Current({{ current }})`` — names no file contains, so those columns were
    silently unmapped, while deriving from a post-load ``config_params`` worked.
    Same configuration, different answer depending on what had run first.

    Doing it here makes the derivation self-contained and order-independent.

    Args:
        renaming: ``legacy_attr -> vendor column``; not mutated.
        config: the configuration, for ``unit_labels`` / ``raw_units``.

    Returns:
        A new dict with placeholders resolved.

    Raises:
        LoaderError: if a placeholder names a unit the configuration does not
            define. Legacy substituted the string ``"None"``, producing a column
            name that matches nothing — a silent unmapped column rather than an
            error.
    """
    labels = getattr(config, "unit_labels", None) or getattr(config, "raw_units", None)
    labels = labels or {}

    resolved: dict[str, str] = {}
    for legacy_attr, vendor in renaming.items():
        if not isinstance(vendor, str) or "{{" not in vendor:
            resolved[legacy_attr] = vendor
            continue

        name = vendor
        # Legacy only substituted keys that appear in headers_normal; this
        # substitutes every entry. That can only ever fix a name, never break
        # one — an unsubstituted template matched no vendor column anyway.
        for fragment in vendor.split("{{")[1:]:
            placeholder = fragment.split("}}")[0]
            unit = labels.get(placeholder.strip())
            if unit is None:
                raise LoaderError(
                    f"{_config_name(config)} spells {legacy_attr!r} as "
                    f"{vendor!r}, but defines no unit named "
                    f"{placeholder.strip()!r}; the column name would be "
                    f"unmatchable. Known units: {sorted(labels)}."
                )
            name = name.replace(f"{{{{{placeholder}}}}}", f"{unit}")
        resolved[legacy_attr] = name

    return resolved


def _config_name(config: Any) -> str:
    """A name for messages, for either shape of configuration.

    Derivation accepts both a ``configurations.*`` **module** (what the shipped
    configurations are) and a live :class:`ModelParameters` **instance** (what a
    loader carries as ``config_params``, including the ones assembled at runtime
    from a YAML file). The two spell their name differently.
    """
    return getattr(config, "__name__", None) or getattr(config, "name", "<configuration>")


#: Names the capacity-splitting hook synthesises. They are vendor-side names —
#: hooks run before renaming — so they must not collide with a real vendor
#: column; the leading underscore is not a convention any tester uses.
_SPLIT_CHARGE = "_split_charge_capacity"
_SPLIT_DISCHARGE = "_split_discharge_capacity"


def _state_splitting(
    config: Any,
    post_processors: dict,
    column_map: dict[str, str],
    renaming: dict[str, str],
) -> tuple[tuple, tuple[str, ...]]:
    """Derive the state-splitting hooks, reshaping ``column_map`` in place.

    ``split_capacity`` is the one post-processor that changes the *shape* of the
    mapping rather than the values in it: one vendor column ("Amp-hr") becomes
    two native columns. So the vendor column stops being mapped directly, the
    hook synthesises two columns under vendor-side names, and those get mapped
    instead.

    ``split_current`` rewrites its column in place, so the mapping is untouched.

    Returns:
        ``(post_hooks, dropped)`` — the hooks to run, and vendor columns now
        consumed by them (so they do not trip the unrecognised-column warning).
    """
    states = getattr(config, "states", None) or {}
    wants_capacity = bool(post_processors.get("split_capacity"))
    wants_current = bool(post_processors.get("split_current"))
    wants_cycle_shift = bool(post_processors.get("set_cycle_number_not_zero"))

    # Independent of state splitting: it needs only the cycle column.
    cycle_hooks: tuple = ()
    if wants_cycle_shift:
        cycle_vendor = renaming.get("cycle_index_txt")
        if not cycle_vendor:
            raise LoaderError(
                f"{_config_name(config)} enables set_cycle_number_not_zero but "
                f"maps no cycle_index_txt; there is no column to shift."
            )
        cycle_hooks = (cycle_number_not_zero(cycle_column=cycle_vendor),)

    if not (wants_capacity or wants_current):
        return cycle_hooks, ()

    if not states:
        raise LoaderError(
            f"{_config_name(config)} enables state splitting but declares no "
            f"`states`; the splitter cannot know which flag means charge."
        )

    schema_raw = mapping.LEGACY_ATTR_TO_SCHEMA["raw"]
    state_column = states["column_name"]
    cycle_column = renaming.get("cycle_index_txt")
    datapoint_column = renaming.get("data_point_txt")
    if not cycle_column or not datapoint_column:
        raise LoaderError(
            f"{_config_name(config)} enables state splitting but does not map "
            f"cycle_index_txt and data_point_txt; splitting is per cycle and "
            f"ordered by datapoint, so both are required."
        )

    common = dict(
        state_column=state_column,
        cycle_column=cycle_column,
        datapoint_column=datapoint_column,
        charge_keys=states.get("charge_keys", ()),
        discharge_keys=states.get("discharge_keys", ()),
    )

    hooks: list = []
    dropped: list[str] = [state_column]

    if wants_capacity:
        base = renaming.get("charge_capacity_txt")
        if not base:
            raise LoaderError(
                f"{_config_name(config)} enables split_capacity but maps no "
                f"charge_capacity_txt; there is nothing to split."
            )
        hooks.append(
            state_splitter(
                base_column=base,
                charge_output=_SPLIT_CHARGE,
                discharge_output=_SPLIT_DISCHARGE,
                n_charge=1.0,
                n_discharge=1.0,
                propagate=True,
                **common,
            )
        )
        # The shared vendor column stops being mapped; its two halves take over.
        column_map.pop(base, None)
        dropped.append(base)

        charge_target = schema_raw["charge_capacity_txt"]
        discharge_target = schema_raw["discharge_capacity_txt"]

        # Any *other* vendor column claiming those targets loses. This mirrors
        # 1.x rather than inventing a rule: `split_capacity` is not in
        # ORDERED_POST_PROCESSING_STEPS, so it runs after `rename_headers` and
        # overwrites whatever the rename produced. `maccor_txt_one` is the live
        # case — it declares a `Discharge_Capacity(Ah)` column under a "not
        # observed yet" comment, which the split would have overwritten had the
        # file carried it. Without this, the declarations fail validation for
        # mapping two vendor columns onto one native column.
        for vendor, target in list(column_map.items()):
            if target in (charge_target, discharge_target):
                logging.debug(
                    "split_capacity supersedes the direct mapping %r -> %r "
                    "(the legacy post-processor overwrote it too)",
                    vendor,
                    target,
                )
                column_map.pop(vendor)
                dropped.append(vendor)

        column_map[_SPLIT_CHARGE] = charge_target
        column_map[_SPLIT_DISCHARGE] = discharge_target

    if wants_current:
        base = renaming.get("current_txt")
        if not base:
            raise LoaderError(
                f"{_config_name(config)} enables split_current but maps no "
                f"current_txt; there is nothing to split."
            )
        # One output column: charge positive, discharge negated, rest zero.
        hooks.append(
            state_splitter(
                base_column=base,
                charge_output=base,
                discharge_output=base,
                n_charge=1.0,
                n_discharge=-1.0,
                propagate=False,
                **common,
            )
        )

    # Cycle shift last, mirroring 1.x: the unordered post-processor pass runs in
    # configuration-declaration order, and every splitting configuration lists
    # set_cycle_number_not_zero after the splits. A uniform +1 cannot change the
    # per-cycle grouping either way, but matching the order costs nothing.
    return tuple(hooks) + cycle_hooks, tuple(dropped)


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

    # Before anything reads the renaming: resolve `{{ unit }}` placeholders, so
    # the derivation gives the same answer from a module as from a post-load
    # config_params. Everything downstream — the column map, the splitting
    # hooks' vendor column names — depends on these being real names.
    renaming = substitute_unit_templates(renaming, config)

    column_map, passthrough, unknown = derive_column_maps(renaming)
    if unknown:
        logging.debug(
            "%s declares legacy attributes with no native or legacy column: %s",
            _config_name(config),
            sorted(unknown),
        )

    post_processors = getattr(config, "post_processors", None) or {}
    hooks, dropped = _state_splitting(
        config, post_processors, column_map, renaming
    )

    # Last, and only now: `remove_last_if_bad` counts missing values over the
    # columns cellpy *keeps*, which is only known once the column map is final
    # (state splitting can add and remove entries). It also has to run after the
    # splitters, as it did in 1.x, so a row the splitters filled is judged on
    # its filled state.
    if post_processors.get("remove_last_if_bad"):
        hooks += (
            drop_last_row_if_worse(
                columns=tuple(column_map) + tuple(passthrough),
            ),
        )

    hooks += tuple(post_hooks)

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

    # A configuration that runs ``convert_date_time_to_datetime`` writes its
    # absolute timestamp as a wall-clock *string* (the post-processor is
    # ``pd.to_datetime``). Declaring it lets ``harmonize()`` derive the required
    # ``epoch_time_utc`` from the ``date_time`` passthrough. Keyed on the
    # passthrough carrying the datetime column, so it is a no-op for a
    # configuration that has no datetime.
    date_time_header = _legacy_column_name("datetime_txt")
    datetime_kind = None
    if (
        post_processors.get("convert_date_time_to_datetime")
        and date_time_header in passthrough.values()
    ):
        datetime_kind = "string"

    return LoaderDeclarations(
        column_map=column_map,
        raw_units=_units_from_configuration(config),
        timezone=timezone,
        reset_granularity=granularity,
        duration_columns=durations,
        passthrough=passthrough,
        post_hooks=hooks,
        dropped=dropped,
        datetime_kind=datetime_kind,
    )
