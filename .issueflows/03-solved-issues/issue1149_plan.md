# Issue #1149 plan

## Goal

Make `neware_nda` report the units that the fastnda frame actually contains, so gravimetric capacity, C-rate, and raw current from an `.ndax` load match the file.

## Constraints

- Do not commit the raw file. It stays under gitignored `local/data/`.
- Journal mass and nominal capacity stay the Arbin-good `cellpy_db` values. Do not rescale them.
- Do not change NDC scale factors in `local_fastnda`. This file's decoder output is already in the units its column names claim.
- `data.raw` stays in `raw_units`. Downstream (`get_converter_to_specific`, C-rate, raw-plot labels) trusts that declaration. Fix the declaration, not the plotters.

### Prior art

- `DataLoader.get_raw_units` in `src/cellpy/readers/instruments/neware_nda.py` — declares `current="A"`, `charge="Ah"`. Both the legacy `loader()` path and `declarations()` copy this dict. The vendor names it renames are already `current_mA`, `voltage_V`, `*_mAh`, `*_mWh`, `internal_resistance_mOhm`.
- `cellpy.libs.local_fastnda.formats.BDF_MULTIPLIER_MAP` — same fact as a scale (`1e-3` from those milli columns to A/Ah/Wh). Do not call `to_bdf`; that would rescale the frame.
- `merge_raw_units` / `get_default_raw_units` — omitted keys stay at `charge="Ah"`, `current="A"`, `mass="mg"`, `energy="Wh"`, `resistance="ohm"`, `nominal_capacity="mAh/g"`.
- `cellpycore.units.spec.CellpyUnits` — raw frame is in `raw_units`. Arbin loaders declare `A`/`Ah` because their files are in those units. The `.ndax` XML has no unit string (`SignalUnit` is empty).
- Neware txt configs (`configurations/neware_txt_*.py`) use pint unit strings (`mohm`, not `mOhm`).
- `tests/test_neware_nda_two_stage.py` — declaration mapping only; no unit assertion.
- Toolbox: none for this. Graph report not consulted (unit bug is local to one loader).

## Evidence (local file, not in git)

`local/data/20261013_nor110_04_fcnmp_cyc_20261013151333.ndax` (home checkout; `local/` is gitignored). BTS Client 8.0.1.489 (2025.11.24). NDC version 17.

| piece | reader | result |
|---|---|---|
| `data.ndc` filetype 1 | `_read_ndc_17_filetype_1` (`current * 1000`) | voltage 3.50–4.85 V; current −65.70 to +65.70 |
| `data_runInfo.ndc` filetype 18 | `_read_ndc_17_filetype_18` (`capacity * 1000`, Ah→mAh) | charge cap max 950.2, discharge cap max 933.6 |
| `Step.xml` | — | `Curr` 65.7 on the CC steps; stop voltages 3.50 V / 4.85 V |
| wall time | — | ~29.8 h (matches the ~30 h cycle) |

65.7 mA is the programmed current. 56 mA in the issue is the C/20 estimate, so the raw-plot factor versus 56 mA is not a clean 1000. The loader then renames `current_mA` and `*_capacity_mAh` onto canonical columns and labels them `A` and `Ah`, which is the 1000× gravimetric capacity and C-rate error.

## Approach

Build `DataLoader.get_raw_units()` from the fastnda column names already in `normal_headers_renaming_dict`. Longest suffix wins:

| suffix | pint string |
|---|---|
| `_mAh` | `mAh` |
| `_mWh` | `mWh` |
| `_mOhm` | `mohm` |
| `_mA` | `mA` |
| `_V` | `V` |

Header key → `CellpyUnits` field: `current_txt`→`current`, `voltage_txt`→`voltage`, `charge_capacity_txt` and `discharge_capacity_txt`→`charge`, `charge_energy_txt` and `discharge_energy_txt`→`energy`, `internal_resistance_txt`→`resistance`. Charge and discharge must share a suffix; disagree → `ValueError`.

Not in the frame, so not parsed from a suffix:

- `mass` stays `"g"` (same journal unit as Arbin; the merge default is `mg`).
- Drop the `nominal_capacity="Ah/g"` override. The merge default `mAh/g` then matches the journal.

No divide-by-1000 in the frame. No NDC reader edits. The `.ndax` is not parsed for units.

## Files to touch

- `src/cellpy/readers/instruments/neware_nda.py` — suffix table plus `get_raw_units()` derived from `normal_headers_renaming_dict`
- `tests/test_neware_nda_two_stage.py` — `declarations().raw_units` is `current="mA"`, `charge="mAh"`, `energy="mWh"`, `resistance="mohm"`, `voltage="V"`, `mass="g"`, `nominal_capacity="mAh/g"`, read from the real renaming dict.
- `tests/test_neware_nda_two_stage.py` or a sibling test — if `local/data/20261013_nor110_04_fcnmp_cyc_20261013151333.ndax` exists, load with `instrument="neware_nda"` and assert `|current|` max ≈ 65.7, discharge-capacity max ≈ 934, and `raw_units.current == "mA"`, `raw_units.charge == "mAh"`. Skip when the file is absent so CI stays green.

## Test strategy

`uv run pytest tests/test_neware_nda_two_stage.py tests/test_neware.py -m essential`

The local-file assertion is not marked essential (file is not in the repo). Run it once locally against the gitignored ndax.

## Open questions

- None. 65.7 mA from `Step.xml` is the programmed current. 56 mA in the issue stays the C/20 estimate.
