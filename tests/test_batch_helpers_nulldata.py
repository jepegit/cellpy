"""Regression: join_summaries must raise NullData, not NameError (#688)."""

import pytest

from cellpy.exceptions import NullData
from cellpy.utils.batch_tools import batch_helpers


def test_join_summaries_empty_raises_nulldata():
    with pytest.raises(NullData, match="No summaries available"):
        batch_helpers.join_summaries({}, selected_summaries=["discharge_capacity"])
