"""Contract tests guarding header/unit/limit parity between cellpy and cellpy-core.

``cellpy-core`` keeps verbatim copies of cellpy's authoritative settings classes
(``HeadersNormal``, ``HeadersSummary``, ``HeadersStepTable``, ``CellpyUnits``,
``CellpyLimits``) in ``cellpycore.legacy`` so the integration seam (issue #377)
produces identical column names, units, and step-type detection thresholds. These
tests assert the copies stay field-for-field identical to
``cellpy.parameters.internal_settings`` so drift in one repo fails loudly instead of
silently mismatching columns/units/limits. See issue #378.

The whole module is skipped when ``cellpy-core`` is not installed.
"""

import dataclasses

import pytest

cellpycore_legacy = pytest.importorskip("cellpycore.legacy")

from cellpy.parameters import internal_settings as cellpy_settings

# Classes that cellpy-core copies verbatim and must stay in sync with cellpy.
# ``CellpyLimits`` (step-type detection thresholds) was ported to cellpy-core as part
# of STEP-08 and is now guarded here too.
SHARED_CLASSES = [
    "HeadersNormal",
    "HeadersSummary",
    "HeadersStepTable",
    "CellpyUnits",
    "CellpyLimits",
]


def _field_map(cls) -> dict:
    """Map dataclass field name -> default value (ignores properties/class attrs)."""
    return {f.name: f.default for f in dataclasses.fields(cls)}


def _drift_report(name: str, cellpy_map: dict, core_map: dict) -> str:
    only_cellpy = sorted(set(cellpy_map) - set(core_map))
    only_core = sorted(set(core_map) - set(cellpy_map))
    changed = sorted(
        k
        for k in set(cellpy_map) & set(core_map)
        if cellpy_map[k] != core_map[k]
    )
    lines = [f"Settings drift in {name} between cellpy and cellpy-core:"]
    if only_cellpy:
        lines.append(f"  fields only in cellpy: {only_cellpy}")
    if only_core:
        lines.append(f"  fields only in cellpy-core: {only_core}")
    for k in changed:
        lines.append(
            f"  field {k!r}: cellpy={cellpy_map[k]!r} vs cellpy-core={core_map[k]!r}"
        )
    return "\n".join(lines)


@pytest.mark.essential
@pytest.mark.parametrize("name", SHARED_CLASSES)
def test_settings_parity(name):
    cellpy_cls = getattr(cellpy_settings, name)
    core_cls = getattr(cellpycore_legacy, name)
    cellpy_map = _field_map(cellpy_cls)
    core_map = _field_map(core_cls)
    assert cellpy_map == core_map, _drift_report(name, cellpy_map, core_map)
