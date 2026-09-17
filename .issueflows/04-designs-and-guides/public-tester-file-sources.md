# Public tester-file sources (catalog only)

Scanned 2026-09-16. **Links and descriptions only — files were not downloaded.**
Treat this as a shopping list. Review licence + whether the file is native
tester output vs a converted CSV/MAT before adding anything to `testdata/`.

**Already in this repo (do not re-fetch):** `testdata/data/` has Maccor
`.txt` (`maccor_001`, `maccor_002`), Neware CSV (`neware_uio.csv`,
`nw_regular_export_ife_example.csv`), PEC CSV (`pec.csv` +
`pec_multiple_tests/`), BatMo BDF CSV, and `fdv.py` points at `biol.mpr` and
`20260302_IFE_BTS85_2_9_8_1.ndax` (may be local-only / not always in git).
Arbin `.res` under `testdata/batch_project/data/raw/` is gitignored.

**Useful first picks for breadth** (small, native, CC-BY or already used by
parser projects):

1. SINTEF pipeline-test set — many cyclers, some intentional bugs.
2. NewareNDA issue fixtures — tiny `.nda` / `.ndax` for `neware_nda`.
3. yadg `tests/test_x_eclab/` — many small BioLogic `.mpr` / `.mpt` techniques
   (licence review before committing; yadg is GPL-family).
4. TDK Ceracharge Zenodo — BioLogic BCS-810 `.mpr` + `.mps` (CC BY 4.0);
   prefer the ~4–7 MB formation GCPL files, not the 70–110 MB cycle files.

---

## 1. SINTEF — pipeline / workflow test set (best multi-tester pack)

Landing: https://zenodo.org/records/18986774
DOI: https://doi.org/10.5281/zenodo.18986774
Older versions: https://doi.org/10.5281/zenodo.18214281 ·
https://doi.org/10.5281/zenodo.17289383 ·
https://doi.org/10.5281/zenodo.17035637
Licence: CC BY 4.0 (Clark / Tolchard, SINTEF; plus third-party files as noted)
Catalog JSON: https://zenodo.org/api/records/18986774/files/metadata.json/content

Description: exported files from several cyclers, meant for pipeline tests.
Some files include known export/test bugs on purpose.

| File | Tester | Size | Description | Link |
| --- | --- | --- | --- | --- |
| `SINTEF__G20M7-202512-Gru6mV__20251228__C30__25degC__Neware.nda` | Neware | 929 kB | Li-ion full cell, CCCV C/30, native `.nda` | https://zenodo.org/records/18986774/files/SINTEF__G20M7-202512-Gru6mV__20251228__C30__25degC__Neware.nda |
| `SINTEF__SLPBA842124HV__2024-10-23__Rate_25degC__Neware__Time_Bug.csv` | Neware | 3.2 MB | Li-ion rate capability; **non-monotonic total time** | https://zenodo.org/records/18986774/files/SINTEF__SLPBA842124HV__2024-10-23__Rate_25degC__Neware__Time_Bug.csv |
| `SINTEF__NaCR32140-MP10-04__2025-08-25__CCCV_0p02C_25degC__BioLogic__Outlier_Bug.mpt` | BioLogic | 53.6 MB | Na-ion CCCV C/50 `.mpt`; **voltage/current outliers** | https://zenodo.org/records/18986774/files/SINTEF__NaCR32140-MP10-04__2025-08-25__CCCV_0p02C_25degC__BioLogic__Outlier_Bug.mpt |
| `SINTEF__NaCR32140-MP10-04__2025-08-25__GITT_0p05C_25degC__BioLogic.mpt` | BioLogic | 74.7 MB | Na-ion GITT `.mpt` | https://zenodo.org/records/18986774/files/SINTEF__NaCR32140-MP10-04__2025-08-25__GITT_0p05C_25degC__BioLogic.mpt |
| `tum__bak-n18650ck-202204-001__characterization__25degC__biologic.txt` | BioLogic | 2.1 MB | Li-ion 18650 rate/characterization (text export) | https://zenodo.org/records/18986774/files/tum__bak-n18650ck-202204-001__characterization__25degC__biologic.txt |
| `faraday__lg-INR21700M50-2019-002__2019-06-02__rate__25degC__maccor.csv` | Maccor | 598 kB | Faraday / LG M50 21700 rate, CSV export (not Maccor `.txt`) | https://zenodo.org/records/18986774/files/faraday__lg-INR21700M50-2019-002__2019-06-02__rate__25degC__maccor.csv |
| `stanford__a123-%20ANR26650m1B-2020-k1__1C__25degC__arbin.xlsx` | Arbin | 1.1 MB | A123 26650, 1C / 25 °C, Excel export | https://zenodo.org/records/18986774/files/stanford__a123-%20ANR26650m1B-2020-k1__1C__25degC__arbin.xlsx |
| `shandong__nacr32140-mp10__2023-10-10__pulse__25degC__arbin.CSV` | Arbin | 21.6 MB | Na-ion pulse, CSV export | https://zenodo.org/records/18986774/files/shandong__nacr32140-mp10__2023-10-10__pulse__25degC__arbin.CSV |
| `SINTEF__LiGrR2032__2024-04-30__25degC__Landt.csv` | Landt | 2.6 MB | Li-graphite half-cell cycling | https://zenodo.org/records/18986774/files/SINTEF__LiGrR2032__2024-04-30__25degC__Landt.csv |
| `SINTEF__LiGrR2032__2024-04-30__25degC__Landt.txt` | Landt | 2.8 MB | same test, `.txt` | https://zenodo.org/records/18986774/files/SINTEF__LiGrR2032__2024-04-30__25degC__Landt.txt |
| `sintef__energizer-cr2032-202602-dtjrga__2026-02-25__c100__RT__landt.ccs` | Landt | 10.2 MB | Energizer CR2032, Landt `.ccs` | https://zenodo.org/records/18986774/files/sintef__energizer-cr2032-202602-dtjrga__2026-02-25__c100__RT__landt.ccs |
| `DLR__LiGrHydra0b__20221114__GITT__25degC__Basytec.txt` | BaSyTec | 62.4 MB | Li-graphite half-cell GITT | https://zenodo.org/records/18986774/files/DLR__LiGrHydra0b__20221114__GITT__25degC__Basytec.txt |
| `DLR__LiGrHydra0b__20230131__POCV__25degC__Basytec.txt` | BaSyTec | 9.3 MB | Li-graphite POCV | https://zenodo.org/records/18986774/files/DLR__LiGrHydra0b__20230131__POCV__25degC__Basytec.txt |
| `DLR__LiLNMOHydra0b__20221130__GITT__25degC__Basytec.txt` | BaSyTec | 63.0 MB | Li-LNMO half-cell GITT | https://zenodo.org/records/18986774/files/DLR__LiLNMOHydra0b__20221130__GITT__25degC__Basytec.txt |
| `DLR__LiLNMOHydra0b__20221125__POCV__25degC__Basytec.txt` | BaSyTec | 4.1 MB | Li-LNMO POCV | https://zenodo.org/records/18986774/files/DLR__LiLNMOHydra0b__20221125__POCV__25degC__Basytec.txt |
| `tum__bak-n18650ck-202204-044__cycle__45degC__basytec.txt` | BaSyTec | 258 MB | TUM 18650 cycling @ 45 °C — too big for unit tests | https://zenodo.org/records/18986774/files/tum__bak-n18650ck-202204-044__cycle__45degC__basytec.txt |
| `FZJ__INR21700__20250606__HPPC__25degC__Digatron.csv` | Digatron | 13.3 MB | INR21700 HPPC | https://zenodo.org/records/18986774/files/FZJ__INR21700__20250606__HPPC__25degC__Digatron.csv |
| `SINTEF__SLPBA842124HV-06__20241011__DCIR__0p1C__25degC__Novonix.csv` | Novonix | 119 MB | DCIR @ 0.1C — large | https://zenodo.org/records/18986774/files/SINTEF__SLPBA842124HV-06__20241011__DCIR__0p1C__25degC__Novonix.csv |

cellpy today has loaders for BioLogic `.mpr`, Neware CSV/NDA/XLSX, Maccor
`.txt`, Arbin `.res`/SQL/CSV/XLSX, PEC CSV. Landt / BaSyTec / Digatron /
Novonix would be **new** instruments (or custom-loader fixtures).

---

## 2. BioLogic — native `.mpr` / `.mpt`

### 2a. TDK Ceracharge (BCS-810, CC BY 4.0)

Landing: https://zenodo.org/records/18925051
DOI: https://doi.org/10.5281/zenodo.18925051
Authors: Zhu / Schröder (TU Braunschweig)
Description: commercial TDK Ceracharge solid-state cells, 25 °C / 30 % RH,
CC-CV to 2.4 V, CC-CV discharge to 0 V, EIS 10 kHz–10 mHz. Files are
`.mpr` (raw) and `.mps` (EC-Lab settings). Name pattern:
`CellNNN_{Form|Cyc}_{current}_{temp}_{RH}_{cycles}_{step}_{technique}_{channel}`.

64 files on the record. Smaller / more test-sized examples:

| File | Size | Description | Link |
| --- | --- | --- | --- |
| `Cell007_Form_200uA_25T_30RH_Cycle1to10_02_GCPL_CA7.mpr` | 4.1 MB | formation GCPL | https://zenodo.org/records/18925051/files/Cell007_Form_200uA_25T_30RH_Cycle1to10_02_GCPL_CA7.mpr |
| `Cell008_Form_200uA_25T_30RH_Cycle1to10_02_GCPL_CA8.mpr` | 6.9 MB | formation GCPL | https://zenodo.org/records/18925051/files/Cell008_Form_200uA_25T_30RH_Cycle1to10_02_GCPL_CA8.mpr |
| `Cell001_Cyc_20uA_25T_30RH_Cycle11to100_01_GEIS_CA1.mpr` | 36 kB | GEIS | https://zenodo.org/records/18925051/files/Cell001_Cyc_20uA_25T_30RH_Cycle11to100_01_GEIS_CA1.mpr |
| `Cell003_Form_50uA_25T_30RH_Cycle1to10_03_GEIS_CA3.mpr` | 38 kB | GEIS | https://zenodo.org/records/18925051/files/Cell003_Form_50uA_25T_30RH_Cycle1to10_03_GEIS_CA3.mpr |
| `Cell007_Form_200uA_25T_30RH_Cycle1to10.mps` | 8 kB | settings | https://zenodo.org/records/18925051/files/Cell007_Form_200uA_25T_30RH_Cycle1to10.mps |
| `Cell001_Cyc_20uA_25T_30RH_Cycle11to100_02_GCPL_CA1.mpr` | 110 MB | long cycling — skip for unit tests | https://zenodo.org/records/18925051/files/Cell001_Cyc_20uA_25T_30RH_Cycle11to100_02_GCPL_CA1.mpr |

Full file list: `GET https://zenodo.org/api/records/18925051` (JSON).

Relevant to open #270 (mpr data version 3) if any of these are v3 — check
header after a *controlled* fetch, not assumed here.

### 2b. yadg BioLogic fixtures (many techniques, small)

Repo: https://github.com/dgbowl/yadg
Folder: https://github.com/dgbowl/yadg/tree/main/tests/test_x_eclab
Licence: review before reuse (yadg is GPL-family). Data provenance discussed
in https://github.com/dgbowl/yadg/issues/256

~100 `.mpr` / `.mpt` pairs: GCPL, CA, CP, CV, MB, OCV, PEIS, GEIS, LSV, WAIT,
ZIR, plus issue-specific files. Small examples (raw GitHub URLs):

- https://raw.githubusercontent.com/dgbowl/yadg/main/tests/test_x_eclab/ocv.mpr (29 kB)
- https://raw.githubusercontent.com/dgbowl/yadg/main/tests/test_x_eclab/peis.mpr (19 kB)
- https://raw.githubusercontent.com/dgbowl/yadg/main/tests/test_x_eclab/gcpl.issue_149.mpr (24 kB)
- https://raw.githubusercontent.com/dgbowl/yadg/main/tests/test_x_eclab/mb.mpr (190 kB)
- https://raw.githubusercontent.com/dgbowl/yadg/main/tests/test_x_eclab/gcpl.mpr (962 kB)

Issue attachments (same project):

- https://github.com/dgbowl/yadg/files/8168390/test.zip — MPR with VMP ExtDev module
- https://github.com/dgbowl/yadg/files/8170557/OpeningFiles.zip — same file before/after EC-Lab “export as text” (mpr mutated)

### 2c. galvani test data (LFS / release zip)

Repo: https://github.com/echemdata/galvani (now also https://codeberg.org/echemdata/galvani)
Release archives (actual binaries; git LFS quota is often exhausted):
https://github.com/echemdata/galvani/releases/latest
Licence: GPL-3.0+ — do not copy binaries into cellpy without a licence pass.

Pointer paths (130-byte LFS stubs in git; real files only in the release zip):
`tests/testdata/bio_logic1.mpr` … `bio_logic6.mpr`, `v1150/{CA,CP,GCPL,GEIS,MB,OCV,PEIS}.mpr`,
`arbin1.res`, `UM34_Test005E.res`.

### 2d. UCL / LG M50 21700 ageing (huge)

DOI: https://doi.org/10.5281/zenodo.10637534
Description: BioLogic `.mpr` cycling + `.mpt` RPTs for commercial 21700 cells.
Zips are **6–12 GB each**. Fine as a soak/manual corpus, not CI fixtures.
Paper: “Lithium-ion battery degradation: comprehensive cycle ageing data…”

---

## 3. Neware — `.nda` / `.ndax` / CSV

### 3a. NewareNDA regression fixtures (small native binaries)

Repo: https://github.com/d-cogswell/NewareNDA (branch `development`)
Tree: https://github.com/d-cogswell/NewareNDA/tree/development/tests/nda
Licence: check repo + whether issue-attached files were contributed for
redistribution.

| File | Size | Description | Link |
| --- | --- | --- | --- |
| `123456789012_Unit27_Example_Data_File.ndax` | 6 kB | tiny example | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/Issue94/123456789012_Unit27_Example_Data_File.ndax |
| `ZZZZZZZZTEST.ndax` | 12 kB | issue 27 | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/Issue27_2/ZZZZZZZZTEST.ndax |
| `46_1_5_60_ZZZZZZZZTEST_20250924092922.ndax` | 7 kB | issue 27 | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/Issue27_2/46_1_5_60_ZZZZZZZZTEST_20250924092922.ndax |
| `TestFile.nda` | 394 kB | issue 72, `.nda` | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/Issue72/TestFile.nda |
| `new_nda_file.nda` | 124 kB | neware_reader sample | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/neware_reader/new_nda_file.nda |
| `TESTCELL0001-Test_Data_Collection_Ndc17.ndax` | 6 kB | NDC v17 | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/PR28/TESTCELL0001-Test_Data_Collection_Ndc17.ndax |
| `TESTCELL0001-B2-2025-M50T_NewareNDA_Investigation.ndax` | 559 kB | M50T investigation | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/PR28/TESTCELL0001-B2-2025-M50T_NewareNDA_Investigation.ndax |
| `test_2.ndax` | 1.3 MB | issue 5 | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/Issue5/test_2.ndax |
| `BTS85-36-6-5-110-20240424.ndax` | 3.7 MB | BTS85 | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/github/Issue60/BTS85-36-6-5-110-20240424.ndax |
| `2-1-6_61[07005012].nda` | 1.4 MB | mediafire set | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/mediafire/2-1-6_61%5B07005012%5D.nda |
| `SIM.nda` | 9.4 MB | mediafire SIM | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/mediafire/SIM.nda |
| `2-1-6_62[12500007].nda` | 26 MB | large | https://github.com/d-cogswell/NewareNDA/blob/development/tests/nda/mediafire/2-1-6_62%5B12500007%5D.nda |

SINTEF `.nda` above is the only clearly CC-BY native Neware binary found.

### 3b. Figshare Neware CSV (exported, not `.nda`)

Landing: https://doi.org/10.6084/m9.figshare.26927890.v1
API: https://api.figshare.com/v2/articles/26927890
Author: Hannah Morin
Description: Neware → Excel sheet 3 → CSV. NMC / NCA / LFP cells, 2C fast-charge
fractions 0 / 10 / 20 / 50 / 100 %. Dozens of ~50–500 kB CSVs.

Examples:

- https://ndownloader.figshare.com/files/48983944 — `LFP_S0100_0p_bat49_c0.csv` (372 kB)
- https://ndownloader.figshare.com/files/48983986 — `NCA_S0100_0p_bat62_c0.csv` (302 kB)
- https://ndownloader.figshare.com/files/48984106 — `NMC_S0100_0p_bat112_c0.csv` (423 kB)

Full name list is on the figshare API (`files[].name` / `download_url`).

### 3c. IEEE DataPort Neware BTS4000 (login wall)

https://ieee-dataport.org/documents/2500-cycle-single-cell-battery-aging-dataset
Description: 2500 cycles, Neware BTS4000, Excel + 42.6 MB CSV. Account required.

---

## 4. Maccor

### 4a. Hawaii / Dubarry relaxation (native Maccor `.txt`)

Landing: https://data.mendeley.com/datasets/y8nstxmdrg/1
DOI: https://doi.org/10.17632/y8nstxmdrg.1
Licence: CC BY 4.0
Paper: Fernando et al., *Cell Reports Physical Science* — NMC811 and LFP
relaxation.
Description: **one Maccor `.txt` per cell folder** (full history) + MATLAB
`.mat` relaxation extracts. Protocol 1 / 2; P2 temperature UP (25→55 °C) and
DOWN (30→−15 °C). Per-folder readme.

Related (also Maccor, format of public files not confirmed as `.txt`):
https://doi.org/10.17632/9w745cjx6v — formation + RPTs at many C-rates and
temperatures (Fernando / Dubarry, 2025).

### 4b. Faraday / Oxford (mostly converted)

- SINTEF re-export of Faraday LG M50 rate as CSV — see table in §1.
- Oxford Battery Intelligence data index:
  https://battery-intelligence-lab.github.io/data-and-code/
- Oxford Degradation Dataset 1 (Kokam pouch, **MATLAB `.mat` only**):
  https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac
  DOI 10.5287/bodleian:KO2kdmYGg
- Path-dependent set 3 notes Maccor 4000 + BioLogic MPG205 EIS, but the public
  drop is `.mat`; raw Excel/MIMS on request to david.howey@eng.ox.ac.uk
  https://ora.ox.ac.uk/objects/uuid:78f66fa8-deb9-468a-86f3-63983a7391a9

cellpy already has two Maccor `.txt` dialects. A Dubarry-folder `.txt` is the
clearest *new* native Maccor source found.

---

## 5. Arbin

Native public `.res` is rare. Known sources:

- galvani `arbin1.res` / `UM34_Test005E.res` — only in the **release zip**,
  GPL (see §2c).
- SINTEF Arbin **exports**: Stanford A123 `.xlsx` (1.1 MB) and Shandong pulse
  `.CSV` (21.6 MB) — good for `arbin_sql_xlsx` / `arbin_sql_csv`, not `.res`.

No open CC-BY `.res` found in this scan.

---

## 6. PEC

No extra public PEC CSV/TXT found beyond cellpy’s own
`testdata/data/pec.csv` and `testdata/data/pec_multiple_tests/`.
Open #827 is “multiple cell PEC CSV” — that folder may already cover it.
Battery Archive mentions PEC Oracle as an *ingest* path, not a file drop.

---

## 7. Converted / not native tester files (lower value for loader tests)

| Source | What you actually get | Link |
| --- | --- | --- |
| Battery Archive | per-cell `_timeseries.csv` / `_cycle_data.csv` (normalized, not vendor) | https://batteryarchive.org/ · complete CSV: email info@batteryarchive.org |
| CALCE | usually Excel/MAT ageing tables | linked from https://battery-intelligence-lab.github.io/data-and-code/ |
| NASA PCoE battery | `.mat` | same index |
| Oxford Howey sets | `.mat` | §4b |
| BaSyTec ageing zips (48 cells, CTS-Lab) | zipped checkup/aging; format inside not listed as native `.txt` | https://zenodo.org/records/15755725 |

---

## 8. Licence / hygiene notes

- Prefer **CC BY 4.0** Zenodo / Mendeley for anything that might be committed.
- **Do not** copy galvani or yadg binaries into cellpy until a licence review
  (both GPL-family). Linking to them from this catalog is fine.
- NewareNDA fixtures came from GitHub issues; redistribution terms are unclear.
- Several “public” sets are converted CSV/XLSX/MAT. Useful for custom/generic
  loaders, weak as vendor-loader goldens.
- Prefer files **< ~5 MB** for CI. The BioLogic GITT `.mpt` (75 MB) and TUM
  BaSyTec (258 MB) are soak-only.
- After any future download: scan for unexpected content, strip PII from
  filenames/headers, record licence + DOI next to the fixture.
