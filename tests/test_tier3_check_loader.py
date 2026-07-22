"""Tier-3 ports pass ``check_loader`` (#561).

Acceptance for the tier-3 decisions issue: ported loaders
(``biologics_mpr``, ``batmo_bdf``) must pass the InstrumentLoader conformance
kit. Parked ``ext_nda_reader`` is covered in ``test_parked_loaders.py``.

Two adapters are needed:

1. **``AtomicLoad.name`` collision.** Legacy ``DataLoader`` classes use
   ``name`` as the file-path property, so they cannot declare the contract's
   class-level ``name`` / ``instrument`` / ``supported_suffixes``. The adapters
   expose that surface and drive the real ``parse()`` → ``declarations()`` →
   ``harmonize()`` path (same as Phase C).

2. **Native projection.** ``harmonize()`` currently keeps declared
   ``passthrough`` columns (the one-release ``date_time`` shim, plus legacy
   headers with no native counterpart yet — see
   ``config_declarations``). ``check_raw_frame`` requires a pure native frame.
   The adapters select the native-schema columns after harmonize so the kit
   validates the on-spec subset; clearing passthrough is a later cut when
   cellpy-core maps those headers (energy / aux) or the ``date_time`` window
   ends.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from cellpycore.config import default_schema
from cellpycore.metadata.models import TestMeta

from cellpy.readers.instruments import batmo_bdf, biologics_mpr
from cellpy.readers.instruments.contract import LoaderResult
from cellpy.readers.instruments.harmonize import harmonize
from cellpy.readers.instruments.testing import check_loader

BIOL_FIXTURE = Path("testdata/data/biol.mpr")
BATMO_FIXTURE = Path("testdata/data/batmo_bdf.csv")


def _two_stage_load(loader, source, **kwargs) -> tuple[LoaderResult, ...]:
    vendor = loader.parse(source, **kwargs)
    declarations = loader.declarations()
    raw = harmonize(vendor, declarations, strict=False)
    known = set(default_schema().raw.ordered_names())
    raw = raw.select([column for column in raw.columns if column in known])
    return (
        LoaderResult(
            raw=raw,
            raw_units=declarations.raw_units,
            test_meta=TestMeta(),
        ),
    )


class BiologicsMprContract:
    """InstrumentLoader face for ``biologics_mpr.DataLoader``."""

    name = "biologics_mpr"
    instrument = "biologics"
    supported_suffixes = (".mpr",)

    def can_load(self, source: Path) -> bool:
        return Path(source).suffix.lower() in self.supported_suffixes

    def load(self, source, *, instrument_config=None, **kwargs):
        return _two_stage_load(biologics_mpr.DataLoader(), source, **kwargs)


class BatmoBdfContract:
    """InstrumentLoader face for ``batmo_bdf.DataLoader``."""

    name = "batmo_bdf"
    instrument = "batmo"
    supported_suffixes = (".csv",)

    def can_load(self, source: Path) -> bool:
        return Path(source).suffix.lower() in self.supported_suffixes

    def load(self, source, *, instrument_config=None, **kwargs):
        return _two_stage_load(batmo_bdf.DataLoader(), source, **kwargs)


@pytest.mark.essential
def test_biologics_mpr_passes_check_loader():
    check_loader(BiologicsMprContract, BIOL_FIXTURE)


@pytest.mark.essential
def test_batmo_bdf_passes_check_loader():
    check_loader(BatmoBdfContract, BATMO_FIXTURE)
