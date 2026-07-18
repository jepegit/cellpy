"""Native-schema core adapter for the V2-11 opt-in (issue #511).

``CellpyCell(native_schema=True)`` keeps the ``Data`` frames in **native**
cellpy-core column names (pandas containers) and runs the polars engine
directly — no legacy rename sandwich. The legacy path (``OldCellpyCellCore``)
stays the default; nothing changes unless the flag is set.

This adapter is the pandas ⇄ polars seam only: unlike the legacy bridge it
never renames columns. The frames attached to ``Data`` stay pandas (the polars
container flip is the Phase-3 runtime flip, native-headers plan), but every
column name is the native ``cellpycore.config`` schema name.

Scope (V2-11, deliberately narrow): the ``from_raw`` / ``load`` →
``make_step_table`` → ``make_summary`` → ``save`` (v9) pipeline. Legacy-named
consumers (``get_cap``, exporters, plotting, campaign merge) are not supported
on a native-schema cell yet.
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence, Union

from cellpycore.cell_core import CellpyCellCore
from cellpycore.cell_core import Data as CoreData

from cellpy.readers import externals

_module_logger = logging.getLogger(__name__)

# Legacy summary "cruft" column names cellpycore's curated native CycleCols
# deliberately omits (#552). No native schema equivalent — they resolve through
# the D6 shim as legacy-only (unchanged) names, so we add them under these exact
# strings. Values are pure cumsums over the native summary's own columns.
_SHIFTED_CHARGE = "shifted_charge_capacity"
_SHIFTED_DISCHARGE = "shifted_discharge_capacity"
_CUM_CE = "cumulated_coulombic_efficiency"
_CUM_RIC = "cumulated_ric"
_CUM_RIC_SEI = "cumulated_ric_sei"
_CUM_RIC_DISCONNECT = "cumulated_ric_disconnect"


def _summary_extras_block(s, cc_col, dc_col, ce_col):
    """Compute the legacy cruft columns on one (already per-test) summary block.

    Mirrors cellpycore's ``OldCellpyCellCore._legacy_summary_cruft_block`` so the
    native pipeline reproduces the same values (issue #552).
    """
    cc = s[cc_col]
    dc = s[dc_col]
    s[_CUM_CE] = s[ce_col].cumsum()
    s[_SHIFTED_CHARGE] = (cc - dc).cumsum()
    s[_SHIFTED_DISCHARGE] = s[_SHIFTED_CHARGE] + cc
    s[_CUM_RIC] = ((cc.shift(1) - dc) / dc.shift(1)).cumsum()
    s[_CUM_RIC_SEI] = ((cc - dc.shift(1)) / dc.shift(1)).cumsum()
    s[_CUM_RIC_DISCONNECT] = ((dc.shift(1) - dc) / dc.shift(1)).cumsum()
    return s


def _add_summary_extras(summary, schema):
    """Add the legacy-only cumulated-CE / shifted-capacity / RIC columns (#552).

    These have no native ``CycleCols`` equivalent; they are pure cumsums over the
    native summary's own ``charge_capacity`` / ``discharge_capacity`` /
    ``coulombic_efficiency`` columns. When ``test_id`` is present the cumsums are
    windowed per test so multi-test (campaign-merged) objects do not leak across
    tests (mirrors cellpycore #136).
    """
    cyc = schema.cycle
    cc_col, dc_col, ce_col = (
        cyc.charge_capacity,
        cyc.discharge_capacity,
        cyc.coulombic_efficiency,
    )
    if not {cc_col, dc_col, ce_col}.issubset(summary.columns):
        return summary

    test_id_col = getattr(cyc, "test_id", "test_id")
    if test_id_col in summary.columns:
        import pandas as pd

        parts = [
            _summary_extras_block(g.copy(), cc_col, dc_col, ce_col)
            for _, g in summary.groupby(test_id_col, sort=False)
        ]
        return pd.concat(parts).sort_index() if parts else summary
    return _summary_extras_block(summary, cc_col, dc_col, ce_col)


def _apply_spec_info(steps, step_specifications, schema, short):
    """Propagate the ``info`` column from step specifications to the step table.

    cellpycore's native step classifier reads ``step`` / ``cycle`` / ``type`` from
    the specifications but ignores the optional free-text ``info`` column; this
    fills it in (matched by step, or by (cycle, step) when not ``short``) under the
    legacy-only ``"info"`` name the D6 shim resolves ``headers_step_table.info``
    to. No-op when there are no specifications or no ``info`` column (#554).
    """
    if step_specifications is None:
        return steps
    if "info" not in getattr(step_specifications, "columns", []):
        return steps

    step_col = schema.step.step_num
    cycle_col = schema.step.cycle_num
    if short:
        info_by_step = {
            row.step: row.info for row in step_specifications.itertuples()
        }
        steps["info"] = steps[step_col].map(info_by_step)
    else:
        info_by_key = {
            (row.cycle, row.step): row.info
            for row in step_specifications.itertuples()
        }
        steps["info"] = [
            info_by_key.get((c, s))
            for c, s in zip(steps[cycle_col], steps[step_col])
        ]
    return steps


class NativeCellpyCellCore(CellpyCellCore):
    """Pandas ⇄ polars adapter around the native engine (no column renames).

    Accepts the same call signatures ``cellreader`` uses against the legacy
    bridge (``OldCellpyCellCore``) so ``CellpyCell.make_step_table`` /
    ``make_summary`` work unchanged under the ``native_schema`` flag. The
    legacy-only knobs (``find_end_voltage`` / ``select_columns``) are accepted
    and ignored: the native engine always emits the clean ``CycleCols`` subset
    including the end potentials.
    """

    def make_core_step_table(
        self,
        data,
        raw_limits: Optional[dict] = None,
        step_specifications=None,
        short: bool = False,
        override_step_types: Optional[dict] = None,
        override_raw_limits: Optional[dict] = None,
        usteps: bool = False,
        add_c_rate: bool = True,
        nom_cap: Optional[float] = None,
        skip_steps: Optional[Sequence] = None,
        sort_rows: bool = True,
        from_data_point: Optional[int] = None,
    ) -> Union[object, "externals.pandas.DataFrame"]:
        """Build the native step table (pandas in / pandas out, native names)."""
        import polars as pl

        from cellpycore import summarizers

        tmp = CoreData()
        tmp.raw = pl.from_pandas(data.raw)

        kwargs = dict(
            schema=self.schema,
            step_specifications=step_specifications,
            short=short,
            override_step_types=override_step_types,
            override_raw_limits=override_raw_limits,
            usteps=usteps,
            skip_steps=skip_steps,
            sort_rows=sort_rows,
            from_data_point=from_data_point,
        )
        if raw_limits is not None:
            kwargs["raw_limits"] = raw_limits

        result = summarizers.make_step_table(tmp, **kwargs)
        native_steps = result if from_data_point is not None else result.steps
        if add_c_rate:
            native_steps = native_steps.with_columns(
                summarizers._step_c_rate_expr(
                    self.schema.step, nom_cap if nom_cap is not None else 1.0
                )
            )
        if from_data_point is not None:
            return native_steps.to_pandas()
        data.steps = native_steps.to_pandas()
        # cellpycore's native classifier sets step_type from the specifications
        # but not the free-text `info` column; propagate it here so loading step
        # specifications works end to end (#554).
        _apply_spec_info(data.steps, step_specifications, self.schema, short)
        return data

    def make_core_summary(
        self,
        data,
        find_ir: bool = True,
        find_end_voltage=None,
        select_columns=None,
        final_data_points=None,
        current_conversion_factor: float = 1.0,
        ir_extractor=None,
        exclude_step_types=None,
    ):
        """Build the native summary (pandas in / pandas out, native names)."""
        import polars as pl

        if find_end_voltage is not None or select_columns is not None:
            _module_logger.debug(
                "native path: find_end_voltage / select_columns are legacy-only "
                "knobs and are ignored (end potentials are always included)"
            )

        tmp = CoreData()
        tmp.raw = pl.from_pandas(data.raw)
        tmp.steps = pl.from_pandas(data.steps)
        tmp.meta_test_dependent = data.meta_test_dependent

        tmp = super().make_core_summary(
            tmp,
            find_ir=find_ir,
            final_data_points=final_data_points,
            current_conversion_factor=current_conversion_factor,
            ir_extractor=ir_extractor,
            exclude_step_types=exclude_step_types,
        )
        summary = tmp.summary.to_pandas()
        data.summary = _add_summary_extras(summary, self.schema)
        return data

    def add_scaled_summary_columns(
        self,
        data,
        nom_cap_abs: float,
        normalization_cycles=None,
        step_txt: Optional[str] = None,
        specifics=None,
        specific_conversion_factors: Optional[dict] = None,
        cell_meta=None,
        *,
        specific_converters: Optional[dict] = None,
    ):
        """Add equivalent-cycle and specific columns (pandas in / pandas out)."""
        import polars as pl

        tmp = CoreData()
        tmp.summary = pl.from_pandas(data.summary)
        tmp.meta_test_dependent = data.meta_test_dependent

        tmp = super().add_scaled_summary_columns(
            tmp,
            nom_cap_abs,
            normalization_cycles,
            step_txt=step_txt,
            specifics=specifics,
            specific_conversion_factors=specific_conversion_factors,
            cell_meta=cell_meta,
            specific_converters=specific_converters,
        )
        data.summary = tmp.summary.to_pandas()
        return data
