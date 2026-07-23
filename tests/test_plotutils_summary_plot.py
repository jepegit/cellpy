"""Comprehensive test suite for summary_plot function.

This test suite covers all plot types, configurations, and edge cases
for the summary_plot function to ensure refactoring maintains functionality.
"""

import importlib
import logging
import pytest
import pandas as pd
from cellpy.exceptions import NoDataFound

# Set matplotlib to use non-interactive backend for testing
# This must be done before importing anything that uses matplotlib
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

from cellpy.utils.plotutils import summary_plot

# Check if plotly and seaborn are available
plotly_available = importlib.util.find_spec("plotly") is not None
seaborn_available = importlib.util.find_spec("seaborn") is not None

log = logging.getLogger(__name__)


@pytest.mark.skipif(
    not seaborn_available,
    reason="seaborn not available",
)
class TestSummaryPlotBasic:
    """Test basic functionality of summary_plot with different plot types."""

    @pytest.mark.parametrize(
        "y_param",
        [
            "voltages",
            "capacities_gravimetric",
            "capacities_areal",
            "capacities_absolute",
            "capacities_gravimetric_coulombic_efficiency",
            "capacities_areal_coulombic_efficiency",
            "capacities_absolute_coulombic_efficiency",
        ],
    )
    def test_basic_plot_types(self, cell, y_param):
        """Test that all basic plot types can be created."""
        fig = summary_plot(cell, y=y_param, backend="matplotlib", show_formation=False)
        assert fig is not None
        # For seaborn, should return matplotlib figure
        assert hasattr(fig, "get_axes") or hasattr(fig, "show")

    @pytest.mark.parametrize(
        "y_param",
        [
            "capacities_gravimetric_split_constant_voltage",
            "capacities_areal_split_constant_voltage",
        ],
    )
    def test_cv_split_plot_types(self, cell, y_param):
        """Test CV split plot types."""
        fig = summary_plot(cell, y=y_param, backend="matplotlib", show_formation=False)
        assert fig is not None

    @pytest.mark.parametrize(
        "y_param",
        [
            "fullcell_standard_gravimetric",
            "fullcell_standard_areal",
            "fullcell_standard_absolute",
        ],
    )
    def test_fullcell_standard_plot_types(self, cell, y_param):
        """Test fullcell standard plot types."""
        fig = summary_plot(cell, y=y_param, backend="matplotlib", show_formation=False)
        assert fig is not None


@pytest.mark.skipif(
    not plotly_available,
    reason="Plotly not available",
)
class TestSummaryPlotInteractive:
    """Test interactive (Plotly) mode."""

    def test_interactive_mode(self, cell):
        """Test interactive plotting with Plotly."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric_coulombic_efficiency",
            backend="plotly",
            show_formation=False,
        )
        assert fig is not None
        # Plotly figure should have show method
        assert hasattr(fig, "show")

    def test_interactive_with_formation(self, cell):
        """Test interactive plotting with formation cycles."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="plotly",
            show_formation=True,
            formation_cycles=3,
        )
        assert fig is not None


@pytest.mark.skipif(
    not seaborn_available,
    reason="Seaborn not available",
)
class TestSummaryPlotSeaborn:
    """Test non-interactive (Seaborn) mode."""

    def test_seaborn_mode(self, cell):
        """Test seaborn plotting."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            show_formation=False,
        )
        assert fig is not None
        # Seaborn returns matplotlib figure
        assert hasattr(fig, "get_axes")

    def test_formation_cycles_seaborn(self, cell):
        """Test formation cycles in seaborn mode."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            show_formation=True,
            formation_cycles=3,
        )
        assert fig is not None

    def test_formation_cycles_disabled(self, cell):
        """Test with formation cycles disabled."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            show_formation=False,
        )
        assert fig is not None

    def test_custom_x_axis(self, cell):
        """Test custom x-axis parameter."""
        fig = summary_plot(
            cell,
            x="cycle_index",
            y="capacities_gravimetric",
            backend="matplotlib",
        )
        assert fig is not None

    def test_custom_ranges(self, cell):
        """Test custom axis ranges."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            x_range=[1, 10],
            y_range=[0, 200],
            backend="matplotlib",
        )
        assert fig is not None

    def test_markers(self, cell):
        """Test marker parameter."""
        fig = summary_plot(
            cell, y="capacities_gravimetric", markers=True, backend="matplotlib"
        )
        assert fig is not None

        fig_no_markers = summary_plot(
            cell, y="capacities_gravimetric", markers=False, backend="matplotlib"
        )
        assert fig_no_markers is not None

    def test_title(self, cell):
        """Test custom title."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            title="Test Plot",
            backend="matplotlib",
        )
        assert fig is not None

    def test_return_data(self, cell):
        """Test that return_data returns both figure and data."""
        result = summary_plot(
            cell,
            y="capacities_gravimetric",
            return_data=True,
            backend="matplotlib",
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        fig, data = result
        assert fig is not None
        assert isinstance(data, pd.DataFrame)
        # Data should have expected columns
        assert "cycle_index" in data.columns or "value" in data.columns

    def test_return_data_structure(self, cell):
        """Test structure of returned data."""
        _, data = summary_plot(
            cell,
            y="capacities_gravimetric",
            return_data=True,
            backend="matplotlib",
        )
        # Should have variable and value columns after melting
        assert "variable" in data.columns or "value" in data.columns

    def test_fullcell_standard_normalization(self, cell):
        """Test fullcell standard with normalization."""
        fig = summary_plot(
            cell,
            y="fullcell_standard_gravimetric",
            fullcell_standard_normalization_type="divide",
            fullcell_standard_normalization_factor=1500.0,
            backend="matplotlib",
        )
        assert fig is not None

    def test_fullcell_standard_reset_losses(self, cell):
        """Test fullcell standard with reset_losses."""
        fig = summary_plot(
            cell,
            y="fullcell_standard_gravimetric",
            reset_losses=True,
            backend="matplotlib",
        )
        assert fig is not None


@pytest.mark.skipif(
    not seaborn_available,
    reason="Seaborn not available",
)
class TestSummaryPlotEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_summary(self, cellpy_data_instance):
        """Test with cell that has no summary data."""
        # Create empty cell
        cell = cellpy_data_instance
        # Don't make summary - should handle gracefully
        with pytest.raises(NoDataFound):
            print(f"This should raise NoDataFound: {len(cell.data.summary)=}")
        with pytest.raises(NoDataFound):
            summary_plot(cell, y="capacities_gravimetric", backend="matplotlib")

    def test_single_cycle(self, cell):
        """Test with minimal data (if possible)."""
        # Filter to first cycle if possible
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            x_range=[1, 2],
            backend="matplotlib",
        )
        # Should still create a figure (might be empty)
        assert fig is not None

        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            x_range=[100000, 100001],
            backend="matplotlib",
            show_formation=False,
        )
        # Should still create a figure (might be empty)
        assert fig is not None

    def test_invalid_y_parameter(self, cell):
        """Test with invalid y parameter."""
        # Should raise ValueError since invalid_plot_type is not within the allowed columns
        # TODO: replace with NoDataFound
        # TODO: add test for other invalid parameters
        with pytest.raises(ValueError):
            summary_plot(cell, y="invalid_plot_type", backend="matplotlib")


@pytest.mark.skipif(
    not seaborn_available,
    reason="Seaborn not available",
)
class TestSummaryPlotGoldenReference:
    """Golden reference tests to compare outputs during refactoring."""

    def test_golden_reference_data_structure(self, cell):
        """Capture expected data structure for regression testing."""
        _, data = summary_plot(
            cell,
            y="capacities_gravimetric_coulombic_efficiency",
            return_data=True,
            backend="matplotlib",
            show_formation=False,
        )

        # Basic structure checks
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        # Should have cycle_index or equivalent
        assert "cycle_index" in data.columns or any(
            "cycle" in str(col).lower() for col in data.columns
        )

    def test_golden_reference_columns(self, cell):
        """Capture expected columns in returned data."""
        _, data = summary_plot(
            cell,
            y="capacities_gravimetric",
            return_data=True,
            backend="matplotlib",
        )

        # Check for expected columns after melting
        expected_cols = ["variable", "value"]
        for col in expected_cols:
            assert col in data.columns, f"Expected column {col} not found"

    def test_golden_reference_figure_properties_plotly(self, cell):
        """Capture expected Plotly figure properties."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="plotly",
            show_formation=False,
        )

        # Check basic plotly figure properties
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")
        assert len(fig.data) > 0  # Should have at least one trace

    def test_golden_reference_figure_properties_seaborn(self, cell):
        """Capture expected Seaborn figure properties."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            show_formation=False,
        )

        # Check basic matplotlib figure properties
        assert hasattr(fig, "get_axes")
        axes = fig.get_axes()
        assert len(axes) > 0  # Should have at least one axis


@pytest.mark.skipif(
    not seaborn_available,
    reason="Seaborn not available",
)
class TestSummaryPlotFiltersAndRate:
    """Coverage for the filters / nominal_capacity / with_rate additions
    introduced in issue #363."""

    def _rate_cols(self, cell):
        h = cell.headers_summary
        return h.charge_c_rate, h.discharge_c_rate

    def test_filters_rate_range_drops_rows(self, cell):
        """The rate filter must be wired into the data pipeline.

        Asserting "drops *some* but not all" rows is fragile when the
        test cell has a near-constant C-rate (which it does). Instead,
        verify the filter is reachable: an out-of-range filter empties
        the frame, which the plotter surfaces as the standard
        "No data found" ``ValueError``.
        """
        summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            show_formation=False,
        )
        with pytest.raises(ValueError, match="No data found"):
            summary_plot(
                cell,
                y="capacities_gravimetric",
                filters={"rate": (1e6, 1e7)},
                backend="matplotlib",
                show_formation=False,
            )

    def test_filters_passthrough_when_none(self, cell):
        """``filters=None`` is the default - result must match
        unfiltered baseline."""
        _, baseline = summary_plot(
            cell,
            y="capacities_gravimetric",
            return_data=True,
            backend="matplotlib",
            show_formation=False,
        )
        _, with_none = summary_plot(
            cell,
            y="capacities_gravimetric",
            filters=None,
            return_data=True,
            backend="matplotlib",
            show_formation=False,
        )
        assert len(with_none) == len(baseline)

    def test_nominal_capacity_rescales_rate_columns(self, cell):
        """Doubling the nominal capacity must halve the C-rate columns
        in the returned data."""
        charge_col, discharge_col = self._rate_cols(cell)
        old_nom = cell.data.nom_cap
        if not old_nom:
            pytest.skip("cell.data.nom_cap is unset; cannot exercise rescale")

        _, baseline = summary_plot(
            cell,
            y="capacities_gravimetric_with_rate",
            return_data=True,
            backend="matplotlib",
            show_formation=False,
        )
        _, scaled = summary_plot(
            cell,
            y="capacities_gravimetric_with_rate",
            nominal_capacity=old_nom * 2.0,
            return_data=True,
            backend="matplotlib",
            show_formation=False,
        )

        base_rate = baseline.loc[baseline["variable"].isin([charge_col, discharge_col]), "value"]
        scaled_rate = scaled.loc[scaled["variable"].isin([charge_col, discharge_col]), "value"]

        base_mean = float(base_rate.dropna().mean())
        scaled_mean = float(scaled_rate.dropna().mean())
        if not (base_mean and base_mean == base_mean):
            pytest.skip("baseline rate data is empty / NaN; cannot compare")
        assert scaled_mean == pytest.approx(base_mean * 0.5, rel=1e-6)

    def test_with_rate_yset_produces_rate_rows(self, cell):
        """``*_with_rate`` y-sets must include rate columns in the
        returned (melted) DataFrame."""
        charge_col, discharge_col = self._rate_cols(cell)
        _, data = summary_plot(
            cell,
            y="capacities_gravimetric_with_rate",
            return_data=True,
            backend="matplotlib",
            show_formation=False,
        )
        variables = set(data["variable"].unique())
        assert charge_col in variables
        assert discharge_col in variables

    def test_seaborn_with_formation_clears_facet_titles(self, cell):
        """Regression: seaborn ``relplot`` adds default facet titles like
        ``"row = 0 | cycle_type = standard"``. ``_clean_up_axis`` must
        match every axis and overwrite the title with ``""`` - otherwise
        the internal facet identifier leaks into the final plot.
        """
        fig = summary_plot(
            cell,
            y="capacities_gravimetric_with_rate",
            backend="matplotlib",
            show_formation=True,
            formation_cycles=3,
        )
        leaky = [
            ax.get_title()
            for ax in fig.get_axes()
            if "cycle_type" in ax.get_title() or "row =" in ax.get_title()
        ]
        assert not leaky, f"Seaborn facet titles leaked through: {leaky}"


@pytest.mark.skipif(
    not plotly_available,
    reason="Plotly not available",
)
class TestSummaryPlotHoverColumns:
    """Coverage for the optional ``hover_columns`` parameter."""

    def test_hover_columns_added(self, cell):
        """hover_columns survives the melt and reaches the plotly hover."""
        hdr = cell.headers_summary
        extras = [hdr.test_time, hdr.data_point]

        fig, data = summary_plot(
            cell,
            y="capacities_gravimetric",
            hover_columns=extras,
            return_data=True,
            backend="plotly",
            show_formation=False,
        )

        for col in extras:
            assert col in data.columns, (
                f"Expected hover column {col!r} to survive data preparation"
            )

        templates = [t.hovertemplate or "" for t in fig.data]
        assert any(col in tmpl for tmpl in templates for col in extras), (
            f"Expected at least one trace hovertemplate to reference "
            f"{extras}, got {templates}"
        )

    def test_hover_columns_unknown_warns(self, cell, caplog):
        """Unknown hover columns are dropped with a warning, not raised."""
        hdr = cell.headers_summary
        with caplog.at_level(logging.WARNING):
            fig, data = summary_plot(
                cell,
                y="capacities_gravimetric",
                hover_columns=[hdr.test_time, "definitely_not_a_real_column"],
                return_data=True,
                backend="plotly",
                show_formation=False,
            )

        assert fig is not None
        assert hdr.test_time in data.columns
        assert "definitely_not_a_real_column" not in data.columns
        assert any(
            "definitely_not_a_real_column" in rec.getMessage()
            for rec in caplog.records
        ), "Expected a warning naming the missing hover column"

    def test_hover_columns_ignored_for_fullcell(self, cell, caplog):
        """fullcell_standard_* is out of scope: warn and continue."""
        hdr = cell.headers_summary
        with caplog.at_level(logging.WARNING):
            fig = summary_plot(
                cell,
                y="fullcell_standard_gravimetric",
                hover_columns=[hdr.test_time],
                backend="plotly",
                show_formation=False,
            )

        assert fig is not None
        assert any(
            "hover_columns" in rec.getMessage()
            and "fullcell_standard_gravimetric" in rec.getMessage()
            for rec in caplog.records
        ), "Expected a warning that hover_columns is ignored for fullcell_standard_*"


class TestSummaryPlotFormationCyclesNormalisation:
    """Regression tests for issue #366.

    Passing ``formation_cycles=False`` (or ``0``) without explicitly also
    setting ``show_formation=False`` used to crash with
    ``TypeError: bad operand type for unary ~: 'slice'`` because the
    formation-axes branch ran with the ``slice(None, None)`` sentinel
    selector. ``SummaryPlotConfig.__post_init__`` now mirrors the legacy
    normalisation so both forms produce a valid no-formation plot.
    """

    def test_config_normalises_zero_formation_cycles(self):
        from cellpy.utils.plotutils import SummaryPlotConfig

        cfg = SummaryPlotConfig.from_kwargs(formation_cycles=0)
        assert cfg.formation_cycles == 0
        assert cfg.show_formation is False

    def test_config_normalises_false_formation_cycles(self):
        from cellpy.utils.plotutils import SummaryPlotConfig

        cfg = SummaryPlotConfig.from_kwargs(formation_cycles=False)
        assert cfg.formation_cycles == 0
        assert cfg.show_formation is False

    def test_config_keeps_show_formation_for_positive_count(self):
        from cellpy.utils.plotutils import SummaryPlotConfig

        cfg = SummaryPlotConfig.from_kwargs(formation_cycles=3)
        assert cfg.formation_cycles == 3
        assert cfg.show_formation is True

    @pytest.mark.skipif(
        not plotly_available,
        reason="Plotly not available",
    )
    @pytest.mark.parametrize("formation_cycles_arg", [False, 0])
    def test_plotly_with_zero_or_false_formation_cycles(
        self, cell, formation_cycles_arg
    ):
        """Reproduction from issue #366 for the plotly backend."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="plotly",
            formation_cycles=formation_cycles_arg,
        )
        assert fig is not None
        assert hasattr(fig, "data")

    @pytest.mark.skipif(
        not seaborn_available,
        reason="Seaborn not available",
    )
    @pytest.mark.parametrize("formation_cycles_arg", [False, 0])
    def test_seaborn_with_zero_or_false_formation_cycles(
        self, cell, formation_cycles_arg
    ):
        """Same regression on the seaborn backend."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            formation_cycles=formation_cycles_arg,
        )
        assert fig is not None
        assert hasattr(fig, "get_axes")
