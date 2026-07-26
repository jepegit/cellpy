"""Tests for batch v3 policy: LoadPolicy/CellSpec + resolve_specs (#699)."""

import polars as pl

from cellpy.batch import (
    CellSpec,
    LoadPolicy,
    SourcePreference,
    parse_argument,
    read_journal,
    resolve_specs,
)
from cellpy.batch.journal import FILENAME, Journal


# ---- argument parsing (matches legacy coercion) -------------------------


def test_parse_argument_string_form():
    got = parse_argument("recalc=False;data_points=(1, 10000)")
    assert got == {"recalc": False, "data_points": (1, 10000)}


def test_parse_argument_dict_form_coerces():
    assert parse_argument({"recalc": "TRUE", "keep": "none"}) == {
        "recalc": True,
        "keep": None,
    }


def test_parse_argument_empty_and_null():
    assert parse_argument(None) == {}
    assert parse_argument("") == {}
    assert parse_argument(float("nan")) == {}


# ---- resolve_specs precedence: journal < policy < per-cell --------------


def _journal(**columns):
    columns.setdefault(FILENAME, ["a"])
    return Journal(name="t", project="p", pages=pl.DataFrame(columns))


def test_resolve_specs_journal_only():
    j = _journal(mass=[1.0], instrument=["arbin_res"], argument=["recalc=False"])
    (spec,) = resolve_specs(j)
    assert isinstance(spec, CellSpec)
    assert spec.label == "a"
    assert spec.mass == 1.0
    assert spec.instrument == "arbin_res"
    assert spec.overrides["recalc"] is False


def test_resolve_specs_policy_overrides_journal():
    j = _journal(mass=[1.0], argument=["recalc=False"])
    policy = LoadPolicy(overrides={"mass": 2.0, "recalc": True})
    (spec,) = resolve_specs(j, policy=policy)
    assert spec.mass == 2.0  # policy beats journal
    assert spec.overrides["recalc"] is True  # policy beats journal argument


def test_resolve_specs_per_cell_wins():
    j = _journal(mass=[1.0], argument=["recalc=False"])
    policy = LoadPolicy(overrides={"mass": 2.0})
    (spec,) = resolve_specs(j, policy=policy, per_cell={"a": {"mass": 3.0}})
    assert spec.mass == 3.0  # per-cell beats policy beats journal


def test_resolve_specs_cell_type_is_cycle_mode_fallback():
    j = _journal(cell_type=["anode"])
    (spec,) = resolve_specs(j)
    assert spec.cycle_mode == "anode"


def test_resolve_specs_real_journal(parameters):
    j = read_journal(parameters.journal_file_json_path)
    specs = resolve_specs(j)
    assert len(specs) == len(j)
    assert all(isinstance(s, CellSpec) for s in specs)
    assert {s.label for s in specs} == set(j.cell_names)
    # the argument column ("recalc=...") lands in overrides, not a spec field
    assert any("recalc" in s.overrides for s in specs)


def test_loadpolicy_defaults():
    p = LoadPolicy()
    assert p.source is SourcePreference.AUTO
    assert p.recalc is False
    assert p.accept_errors is True
    assert p.loader_kwargs == {} and p.overrides == {}
