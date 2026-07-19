"""Layered metadata resolution with provenance (metadata plan Step 3, #562).

Metadata about a cell arrives from four places at once — what the user passed
in, what the batch journal or database says, what the instrument wrote into the
file, and what the configuration defaults to. Until now they were merged
ad hoc at whichever call site happened to run first, which is why *"why is my
mass 1.0?"* was not answerable without reading the code.

The precedence is fixed and boring, most specific first::

    kwargs  >  journal / db  >  raw file  >  config defaults

and every resolved field records **which layer won**. That record is the point:
a batch run that silently used a default mass for one cell out of forty is
otherwise invisible until the capacities look strange.

A layer only contributes a field if it actually has a value for it — ``None``
means "I don't know", not "make it None". So a journal that knows the mass but
not the nominal capacity lets the file's nominal capacity through.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import IntEnum
from typing import Any, Iterable, Mapping


class Layer(IntEnum):
    """Where a metadata value came from. Higher wins."""

    CONFIG_DEFAULT = 0
    RAW_FILE = 1
    JOURNAL = 2
    KWARGS = 3

    @property
    def label(self) -> str:
        return {
            Layer.CONFIG_DEFAULT: "config default",
            Layer.RAW_FILE: "raw file",
            Layer.JOURNAL: "journal/db",
            Layer.KWARGS: "user argument",
        }[self]


@dataclass
class Resolution:
    """The outcome of resolving one metadata object."""

    #: field name -> the layer that supplied the winning value
    sources: dict[str, Layer] = field(default_factory=dict)

    def source_of(self, name: str) -> Layer | None:
        """Which layer supplied ``name``, or None if nothing did."""
        return self.sources.get(name)

    def fields_from(self, layer: Layer) -> tuple[str, ...]:
        """Every field this layer won."""
        return tuple(
            sorted(name for name, won in self.sources.items() if won is layer)
        )

    def explain(self) -> str:
        """Human-readable per-field provenance, for logs and debugging."""
        if not self.sources:
            return "no metadata resolved"
        lines = [
            f"  {name}: {layer.label}"
            for name, layer in sorted(self.sources.items(), key=lambda kv: kv[0])
        ]
        return "resolved metadata:\n" + "\n".join(lines)


def _as_mapping(source: Any) -> Mapping[str, Any]:
    """Read a layer as a plain field→value mapping.

    Layers arrive as dataclasses (a draft ``TestMeta``), pydantic models
    (config defaults) or plain dicts (kwargs, journal rows); normalise them
    rather than making every caller do it.
    """
    if source is None:
        return {}
    if isinstance(source, Mapping):
        return source
    if is_dataclass(source):
        return {f.name: getattr(source, f.name) for f in fields(source)}
    dump = getattr(source, "model_dump", None)
    if callable(dump):
        return dump()
    return {
        name: getattr(source, name)
        for name in dir(source)
        if not name.startswith("_") and not callable(getattr(source, name, None))
    }


class MetaResolver:
    """Merge metadata layers into one object, remembering who won.

    Args:
        target_fields: the field names the result may carry. Anything a layer
            offers that is not in here is ignored — a journal column that
            happens to share a name with nothing in particular should not
            invent a metadata field.
    """

    def __init__(self, target_fields: Iterable[str]) -> None:
        self._target_fields = tuple(target_fields)

    def resolve(
        self,
        *,
        kwargs: Any = None,
        journal: Any = None,
        raw_file: Any = None,
        config_defaults: Any = None,
        into: Any = None,
    ) -> tuple[Any, Resolution]:
        """Resolve the layers onto ``into``.

        Args:
            kwargs: what the user passed explicitly. Wins over everything.
            journal: batch journal or database row.
            raw_file: the loader's draft — what the instrument file knew.
            config_defaults: the session's ``ScienceDefaults``-style values.
            into: the object to populate (mutated and returned). Required.

        Returns:
            ``(into, resolution)``.
        """
        if into is None:
            raise ValueError("resolve() needs an object to populate (into=)")

        layers = (
            (Layer.CONFIG_DEFAULT, _as_mapping(config_defaults)),
            (Layer.RAW_FILE, _as_mapping(raw_file)),
            (Layer.JOURNAL, _as_mapping(journal)),
            (Layer.KWARGS, _as_mapping(kwargs)),
        )

        resolution = Resolution()
        for layer, values in layers:
            for name in self._target_fields:
                if name not in values:
                    continue
                value = values[name]
                # None means "this layer has nothing to say", not "set None" —
                # otherwise a journal with blank columns would erase what the
                # instrument file knew.
                if value is None:
                    continue
                setattr(into, name, value)
                resolution.sources[name] = layer

        return into, resolution


def resolve_cell_meta(
    cell_meta: Any,
    *,
    kwargs: Mapping[str, Any] | None = None,
    journal: Any = None,
    draft: Any = None,
    config_defaults: Any = None,
) -> tuple[Any, Resolution]:
    """Resolve a ``CellMeta``: the cell's own properties (mass, area, …)."""
    resolver = MetaResolver(_field_names(cell_meta))
    return resolver.resolve(
        kwargs=kwargs,
        journal=journal,
        raw_file=draft,
        config_defaults=config_defaults,
        into=cell_meta,
    )


def resolve_test_meta(
    test_meta: Any,
    *,
    kwargs: Mapping[str, Any] | None = None,
    journal: Any = None,
    draft: Any = None,
    config_defaults: Any = None,
) -> tuple[Any, Resolution]:
    """Resolve a ``TestMeta``: what this particular run was."""
    resolver = MetaResolver(_field_names(test_meta))
    return resolver.resolve(
        kwargs=kwargs,
        journal=journal,
        raw_file=draft,
        config_defaults=config_defaults,
        into=test_meta,
    )


def _field_names(obj: Any) -> tuple[str, ...]:
    if is_dataclass(obj):
        return tuple(f.name for f in fields(obj))
    return tuple(_as_mapping(obj))


def science_defaults_for_cell(defaults: Any) -> dict[str, Any]:
    """Map the config's ``ScienceDefaults`` onto ``CellMeta`` field names.

    The configuration spells them ``default_mass`` / ``default_nom_cap``
    (historically ``prms.Materials.*``); the metadata model spells them ``mass``
    / ``nom_cap``. Translating here keeps the resolver ignorant of both.
    """
    if defaults is None:
        return {}

    materials = getattr(defaults, "materials", None)
    cell_info = getattr(defaults, "cell_info", None)

    mapped: dict[str, Any] = {}
    if materials is not None:
        mapped.update(
            {
                "mass": getattr(materials, "default_mass", None),
                "nom_cap": getattr(materials, "default_nom_cap", None),
                "nom_cap_specifics": getattr(
                    materials, "default_nom_cap_specifics", None
                ),
                "material": getattr(materials, "default_material", None),
            }
        )
    if cell_info is not None:
        for name in (
            "active_electrode_area",
            "active_electrode_thickness",
            "active_electrode_loading",
            "electrolyte_volume",
            "electrolyte_type",
            "active_electrode_type",
            "counter_electrode_type",
            "reference_electrode_type",
            "experiment_type",
            "cell_type",
        ):
            mapped[name] = getattr(cell_info, name, None)

    return {name: value for name, value in mapped.items() if value is not None}


def resolve_from_loader_result(
    result: Any,
    *,
    source: Any,
    source_type: str,
    kwargs: Mapping[str, Any] | None = None,
    journal: Any = None,
    config_defaults: Any = None,
) -> tuple[Any, Any, Resolution, Resolution]:
    """Turn a loader's drafts into populated metadata, with provenance.

    This is the ingestion-side entry point: it takes what the loader learned
    from the file, resolves it against the other layers, and stamps the
    provenance the loader is not allowed to fill itself.

    Args:
        result: a ``LoaderResult`` carrying draft ``test_meta``/``cell_meta``.
        source: the file the result came from.
        source_type: the loader/instrument name.
        kwargs: explicit user values.
        journal: batch journal or database row.
        config_defaults: session ``ScienceDefaults``.

    Returns:
        ``(cell_meta, test_meta, cell_resolution, test_resolution)``.
    """
    from cellpycore.metadata.models import CellMeta

    from cellpy.readers.provenance import stamp_provenance

    cell_draft = getattr(result, "cell_meta", None)
    test_draft = getattr(result, "test_meta", None)

    cell_meta, cell_resolution = resolve_cell_meta(
        CellMeta(),
        kwargs=kwargs,
        journal=journal,
        draft=cell_draft,
        config_defaults=config_defaults,
    )

    test_meta, test_resolution = resolve_test_meta(
        type(test_draft)() if test_draft is not None else None,
        kwargs=kwargs,
        journal=journal,
        draft=test_draft,
        config_defaults=None,
    )

    if test_meta is not None:
        # Provenance last, and unconditionally: it is the framework's to state,
        # and must not be something a layer can talk it out of.
        stamp_provenance(test_meta, source=source, source_type=source_type)

    return cell_meta, test_meta, cell_resolution, test_resolution
