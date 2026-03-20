"""Manual debug entry for neware_nda — use launch config 'cellpy.get (neware)'.

cellpy loads instrument loaders via importlib (see InstrumentFactory.create), not as
normal package imports. Debugging `neware_nda.py` directly as __main__ can leave
breakpoints unbound; starting from this script avoids that mismatch.
"""
from pathlib import Path

import cellpy

_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_NDAX = _ROOT / "testdata" / "data" / "20260302_IFE_BTS85_2_9_8_1.ndax"


if __name__ == "__main__":
    cellpy.get(
        str(_DEFAULT_NDAX),
        instrument="neware_nda",
        random_keyword="test-random-keyword",
    )
