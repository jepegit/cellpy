"""Grouped summary collections: facet order, group labels, legend title (#923)."""

from __future__ import annotations

import polars as pl
import pytest

from cellpy.collect.collection import Collection, CollectionMeta

_COLUMNS = ("cap_charge", "cap_discharge", "ce")


def _grouped_collection(
    columns: tuple[str, ...] = _COLUMNS,
    *,
    labels: dict | None = None,
    extra_variable: str | None = None,
) -> Collection:
    """A group-averaged summary collection (the ``group_it=True`` long shape)."""
    variables = list(columns) + ([extra_variable] if extra_variable else [])
    rows = []
    for group in (1, 2):
        for cycle in (1, 2, 3):
            for variable in variables:
                rows.append(
                    {
                        "group": group,
                        "cycle_num": cycle,
                        "variable": variable,
                        "mean": 100.0 + cycle + group,
                        "std": 1.0,
                        "group_label": (labels or {}).get(group),
                    }
                )
    frame = pl.DataFrame(rows)
    if labels is None:
        frame = frame.drop("group_label")
    return Collection(
        data=frame,
        kind="summary",
        name="demo",
        meta=CollectionMeta(
            kind="summary", options={"columns": list(columns)}, grouped=True
        ),
    )


def _identity_mapper(*names: str) -> dict[str, str]:
    """A ``y_label_mapper`` that puts the variable name on the y-axis."""
    return {name: name for name in names}


def _facet_labels(fig) -> list[str]:
    """Y-axis titles read down the figure.

    Plotly puts the first facet row on top, so this is the order a reader sees
    and the order ``columns=`` is supposed to set.
    """
    axes = [
        (float(fig.layout[key].domain[1]), fig.layout[key].title.text)
        for key in fig.layout
        if str(key).startswith("yaxis") and fig.layout[key].domain
    ]
    return [title for _, title in sorted(axes, key=lambda item: -item[0])]


@pytest.mark.essential
def test_grouped_summary_facets_follow_the_collected_column_order():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    columns = ("cap_charge", "cap_discharge", "ce")
    fig = _grouped_collection(columns).plot(y_label_mapper=_identity_mapper(*columns))
    # The old frame was sorted by ``variable``, so the facets came out
    # alphabetically (cap_charge, cap_discharge, ce happens to differ from the
    # requested order below).
    assert _facet_labels(fig) == list(columns)


@pytest.mark.essential
def test_grouped_summary_facet_order_is_the_requested_one_not_alphabetical():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    columns = ("cap_charge", "ce", "cap_discharge")
    fig = _grouped_collection(columns).plot(y_label_mapper=_identity_mapper(*columns))
    assert _facet_labels(fig) == list(columns)


@pytest.mark.essential
def test_order_variables_keeps_variables_outside_the_requested_list():
    """A derived series (retention, CV split) must not lose its facet (#923)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    columns = ("cap_charge", "cap_discharge")
    collection = _grouped_collection(columns, extra_variable="cap_retention")
    fig = collection.plot(
        y_label_mapper=_identity_mapper(*columns, "cap_retention")
    )
    assert _facet_labels(fig) == ["cap_charge", "cap_discharge", "cap_retention"]


@pytest.mark.essential
def test_explicit_order_variables_wins_over_the_collected_columns():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = _grouped_collection().plot(
        order_variables=["ce", "cap_charge", "cap_discharge"],
        y_label_mapper=_identity_mapper(*_COLUMNS),
    )
    assert _facet_labels(fig) == ["ce", "cap_charge", "cap_discharge"]


@pytest.mark.essential
def test_custom_group_labels_are_the_legend_entries():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    collection = _grouped_collection(
        labels={1: "my_first_group", 2: "my_second_group"}
    )
    fig = collection.plot()
    assert {trace.name for trace in fig.data} == {
        "my_first_group",
        "my_second_group",
    }


@pytest.mark.essential
def test_unlabelled_groups_keep_their_id_in_the_legend():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = _grouped_collection(labels={1: "labelled"}).plot()
    assert {trace.name for trace in fig.data} == {"labelled", "2"}


@pytest.mark.essential
def test_grouped_summary_legend_title_is_group():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = _grouped_collection().plot()
    assert fig.layout.legend.title.text == "Group"


@pytest.mark.essential
def test_explicit_legend_title_still_wins_for_a_grouped_summary():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = _grouped_collection().plot(legend_title="Sample")
    assert fig.layout.legend.title.text == "Sample"


@pytest.mark.essential
def test_ungrouped_summary_legend_title_stays_cell():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    frame = pl.DataFrame(
        {
            "cell": ["a", "a", "b", "b"],
            "cycle_num": [1, 2, 1, 2],
            "group": [1, 1, 2, 2],
            "sub_group": [1, 1, 1, 1],
            "cap_charge": [100.0, 101.0, 90.0, 91.0],
        }
    )
    collection = Collection(
        data=frame, kind="summary", name="demo", meta=CollectionMeta(kind="summary")
    )
    fig = collection.plot(group_cells=False)
    assert fig.layout.legend.title.text == "Cell"


# --- collect side: label keys that are not the journal's dtype ------------


@pytest.mark.essential
@pytest.mark.parametrize("keys", [(1, 2), ("1", "2")], ids=["int", "str"])
def test_custom_group_labels_match_int_and_str_group_ids(keys):
    from types import SimpleNamespace

    from cellpy.batch import Batch, Journal
    from cellpy.batch.journal import FILENAME
    from cellpy.batch.store import CellStore
    from cellpy.collect import collect_summaries

    class _Cell:
        def __init__(self, scale):
            self.data = SimpleNamespace(
                summary=pl.DataFrame(
                    {"cycle_num": [1, 2], "cap_charge": [10.0 * scale, 20.0 * scale]}
                ),
                steps=None,
            )

    pages = pl.DataFrame(
        {FILENAME: ["a", "b", "c", "d"], "group": [1, 1, 2, 2], "sub_group": [1, 2, 1, 2]}
    )
    batch = Batch(Journal(name="b", project="p", pages=pages))
    batch._store = CellStore.from_cells(
        {"a": _Cell(1), "b": _Cell(1.1), "c": _Cell(0.9), "d": _Cell(1.2)}
    )

    first, second = keys
    collection = collect_summaries(
        batch,
        group_it=True,
        columns=("cap_charge",),
        custom_group_labels={first: "alpha", second: "beta"},
    )
    assert set(collection.data["group_label"].to_list()) == {"alpha", "beta"}
