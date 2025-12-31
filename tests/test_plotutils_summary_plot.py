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
        fig = summary_plot(cell, y=y_param, interactive=False, show_formation=False)
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
        fig = summary_plot(cell, y=y_param, interactive=False, show_formation=False)
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
        fig = summary_plot(cell, y=y_param, interactive=False, show_formation=False)
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
            interactive=True,
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
            interactive=True,
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
            interactive=False,
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
            interactive=False,
            show_formation=True,
            formation_cycles=3,
        )
        assert fig is not None

    def test_formation_cycles_disabled(self, cell):
        """Test with formation cycles disabled."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            interactive=False,
            show_formation=False,
        )
        assert fig is not None

    def test_custom_x_axis(self, cell):
        """Test custom x-axis parameter."""
        fig = summary_plot(
            cell,
            x="cycle_index",
            y="capacities_gravimetric",
            interactive=False,
        )
        assert fig is not None

    def test_custom_ranges(self, cell):
        """Test custom axis ranges."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            x_range=[1, 10],
            y_range=[0, 200],
            interactive=False,
        )
        assert fig is not None

    def test_markers(self, cell):
        """Test marker parameter."""
        fig = summary_plot(
            cell, y="capacities_gravimetric", markers=True, interactive=False
        )
        assert fig is not None

        fig_no_markers = summary_plot(
            cell, y="capacities_gravimetric", markers=False, interactive=False
        )
        assert fig_no_markers is not None

    def test_title(self, cell):
        """Test custom title."""
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            title="Test Plot",
            interactive=False,
        )
        assert fig is not None

    def test_return_data(self, cell):
        """Test that return_data returns both figure and data."""
        result = summary_plot(
            cell,
            y="capacities_gravimetric",
            return_data=True,
            interactive=False,
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
            interactive=False,
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
            interactive=False,
        )
        assert fig is not None

    def test_fullcell_standard_reset_losses(self, cell):
        """Test fullcell standard with reset_losses."""
        fig = summary_plot(
            cell,
            y="fullcell_standard_gravimetric",
            reset_losses=True,
            interactive=False,
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
            summary_plot(cell, y="capacities_gravimetric", interactive=False)

    def test_single_cycle(self, cell):
        """Test with minimal data (if possible)."""
        # Filter to first cycle if possible
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            x_range=[1, 2],
            interactive=False,
        )
        # Should still create a figure (might be empty)
        assert fig is not None

        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            x_range=[100000, 100001],
            interactive=False,
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
            summary_plot(cell, y="invalid_plot_type", interactive=False)


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
            interactive=False,
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
            interactive=False,
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
            interactive=True,
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
            interactive=False,
            show_formation=False,
        )

        # Check basic matplotlib figure properties
        assert hasattr(fig, "get_axes")
        axes = fig.get_axes()
        assert len(axes) > 0  # Should have at least one axis
