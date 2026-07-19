# Golden fixture suites

Committed regression oracles for cellpy 2 Stage 0 characterization work.

**Do not edit files here by hand.** Regenerate with:

```bash
uv run python dev/regenerate_goldens.py
```

Full convention, naming rules, and how to add suites: [`../../README.md`](../../README.md).

## Suites

| Suite | Source | Artifacts |
|-------|--------|-----------|
| `pipeline_smoke` | `testdata/data/20160805_test001_45_cc_01.res` | `summary.parquet`, `metrics.json` |
| `loader_arbin_res` | `testdata/data/20160805_test001_45_cc_01.res` | `raw.parquet`, `raw_units.json`, `meta.json`, `metrics.json` |
| `loader_maccor_txt` | `testdata/data/maccor_001.txt` | `raw.parquet`, `raw_units.json`, `meta.json`, `metrics.json` |
| `loader_neware_txt` | `testdata/data/neware_uio.csv` | `raw.parquet`, `raw_units.json`, `meta.json`, `metrics.json` |
| `loader_pec_csv` | `testdata/data/pec.csv` | `raw.parquet`, `raw_units.json`, `meta.json`, `metrics.json` |
| `loader_custom` | `testdata/data/custom_data_001.csv` + `custom_instrument_001.yml` | `raw.parquet`, `raw_units.json`, `meta.json`, `metrics.json` |
| `curve_get_cap_*`, `curve_get_ccap_*`, `curve_get_dcap_*`, `curve_get_ocv_*` | `testdata/data/20160805_test001_45_cc_01.res` (via cellpy pipeline) | `curve.parquet`, `metrics.json`; `null_data.json` for NullData cases |
| `ica_dqdv_*` | `testdata/data/20160805_test001_45_cc_01.res` (via cellpy pipeline) | `ica.parquet`, `metrics.json` |

The `ica_dqdv_*` suites snapshot the **pre-redesign** dQ/dV output (#566). They
go through the old entry points on purpose: after the redesign those are
deprecation shims over the new core, and `--verify` then shows the shims are
numerically unchanged.
