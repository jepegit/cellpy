"""Reusable vendor post hooks for ``harmonize()`` (issue #560).

Post hooks are the escape valve for quirks no declaration can express. Most are
one vendor's problem, but *state splitting* is not: several testers write one
signed or shared column plus a state flag (``C``/``D``/``R``) and expect the
reader to separate the directions. The legacy path did this with
``post_processors._state_splitter``; this is the same operation for the
two-stage design.

Two differences from the legacy version, both structural rather than semantic:

- **Hooks run before renaming**, so these work on *vendor* column names. A hook
  that synthesises a column gives it a vendor-side name which the declarations
  then map like any other (the ``maccor_txt_native`` pilot established the
  pattern).
- **Polars, expression-based**, so the per-cycle Python loop is gone.

The semantics are deliberately a faithful port, quirks included — see
:func:`state_splitter`. Improving them is a separate, release-noted decision;
doing it inside a port is how a refactor silently changes someone's data.
"""

from __future__ import annotations

from typing import Callable, Sequence

import polars as pl

from cellpy.exceptions import LoaderError


def state_splitter(
    *,
    base_column: str,
    state_column: str,
    cycle_column: str,
    datapoint_column: str,
    charge_keys: Sequence[str],
    discharge_keys: Sequence[str],
    charge_output: str,
    discharge_output: str,
    n_charge: float = 1.0,
    n_discharge: float = 1.0,
    propagate: bool = True,
) -> Callable[[pl.DataFrame], pl.DataFrame]:
    """Build a hook that splits one column by the vendor's state flag.

    Args:
        base_column: the vendor column holding both directions.
        state_column: the vendor column holding the state flag.
        cycle_column: vendor cycle column — propagation is per cycle.
        datapoint_column: vendor datapoint column, used to order within a cycle.
        charge_keys/discharge_keys: state values meaning each direction.
        charge_output/discharge_output: names for the results. **Passing the
            same name for both** produces one combined column (what
            ``split_current`` does: charge positive, discharge negated).
        n_charge/n_discharge: sign applied to each direction.
        propagate: hold each direction's final value for the remainder of the
            cycle. See the note on its exact meaning below.

    Returns:
        A callable suitable for ``LoaderDeclarations.post_hooks``.

    **On ``propagate``.** It is *not* a forward fill, though it looks like one.
    The legacy rule is: a direction's rows carry their own value; rows after
    that direction's **last** row in the cycle carry its final value; everything
    else is zero. A rest *between* two charge rows therefore reads 0, not the
    preceding charge value — which a forward fill would give. That is arguably
    wrong physically, but it is what 1.x produced, and the port's job is to not
    change numbers. Reproduced exactly, and pinned by a test.
    """
    if not charge_keys and not discharge_keys:
        raise LoaderError(
            "state_splitter needs at least one of charge_keys/discharge_keys"
        )

    combined = charge_output == discharge_output

    def _directional(keys: Sequence[str], sign: float) -> pl.Expr:
        """Value on this direction's rows, null elsewhere."""
        return (
            pl.when(pl.col(state_column).is_in(list(keys)))
            .then(pl.col(base_column).cast(pl.Float64, strict=False) * sign)
            .otherwise(None)
        )

    def _resolved(keys: Sequence[str], sign: float) -> pl.Expr:
        own = _directional(keys, sign)
        if not propagate:
            return own.fill_null(0.0)
        # The direction's final value in this cycle, and the datapoint it sat
        # on. `forward_fill().last()` is the last non-null, i.e. the final
        # value the direction reached; null when the direction never occurs.
        last_value = own.forward_fill().last().over(cycle_column)
        last_datapoint = (
            pl.when(pl.col(state_column).is_in(list(keys)))
            .then(pl.col(datapoint_column))
            .otherwise(None)
            .max()
            .over(cycle_column)
        )
        return (
            pl.when(pl.col(state_column).is_in(list(keys)))
            .then(own)
            .when(pl.col(datapoint_column) > last_datapoint)
            .then(last_value)
            .otherwise(0.0)
            .fill_null(0.0)
        )

    def hook(frame: pl.DataFrame) -> pl.DataFrame:
        required = {base_column, state_column, cycle_column, datapoint_column}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise LoaderError(
                f"state splitting needs vendor column(s) {missing}, which the "
                f"parsed frame does not have; it has {sorted(frame.columns)}"
            )

        if combined:
            # One output: charge positive, discharge negated, rest zero.
            expression = (
                pl.when(pl.col(state_column).is_in(list(charge_keys)))
                .then(pl.col(base_column).cast(pl.Float64, strict=False) * n_charge)
                .when(pl.col(state_column).is_in(list(discharge_keys)))
                .then(pl.col(base_column).cast(pl.Float64, strict=False) * n_discharge)
                .otherwise(0.0)
                .fill_null(0.0)
                .alias(charge_output)
            )
            return frame.with_columns(expression)

        return frame.with_columns(
            _resolved(charge_keys, n_charge).alias(charge_output),
            _resolved(discharge_keys, n_discharge).alias(discharge_output),
        )

    hook.__name__ = f"state_splitter[{base_column}]"
    return hook
