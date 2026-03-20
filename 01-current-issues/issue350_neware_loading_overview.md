# Neware text loading – overview (issue 350)

How loading Neware text files works today, and how it ties to configurations and processors.

---

## 1. Entry point and loader class

- **Public API:** `cellpy.get(filename=..., instrument="neware_txt", model="...")` (see `cellpy/readers/cellreader.py`; instrument is passed through to the loader).
- **Loader:** `cellpy.readers.instruments.neware_txt.DataLoader` (subclasses `TxtLoader` in `base.py`).
- **File type:** `raw_ext = "csv"` (tab- or comma-separated text).

The loader is selected by `instrument="neware_txt"`. The **model** selects which *configuration module* is used (see below).

---

## 2. Class hierarchy and responsibilities

```
AtomicLoad (base.py)
  → BaseLoader
    → AutoLoader   ← loads config, holds pre/post processors
      → TxtLoader  ← CSV parsing, formatters, auto-delimiter
        → neware_txt.DataLoader  ← Neware-specific: SUPPORTED_MODELS, get_headers_aux, validate
```

- **AtomicLoad:** File path, copy-to-temp, `loader_executor` → `loader()`.
- **AutoLoader:** Reads **model** from kwargs (default from `prms.Instruments.Neware["default_model"]`), calls `register_configuration()` to load the config module, then sets `self.pre_processors` and `self.post_processors` from config. Also `get_raw_units` / `get_raw_limits` from config.
- **TxtLoader:** Uses config `formatters` (sep, skiprows, header, encoding, decimal, thousands). Can run **auto formatter** (`find_delimiter_and_start`) when `sep` is None. Reads CSV with `query_file()` → `pd.read_csv(...)`. Runs **pre_processors** on the temp file, then **post_processors** on `data.raw` (in fixed order then the rest).
- **DataLoader (neware_txt):** Defines `SUPPORTED_MODELS`, `MUST_HAVE_RAW_COLUMNS`, `get_headers_aux()` (Aux_ columns), and `validate()` (required columns and numeric types).

---

## 3. Model → configuration module

In **`neware_txt.py`**:

```python
SUPPORTED_MODELS = {
    "ONE": "neware_txt_zero",
    "UIO": "neware_txt_zero",
    "UIO_AGA": "neware_txt_one",
    "TIOTECH": "neware_txt_two",
}
```

- **Model** is the key (e.g. `"UIO_AGA"`); it is uppercased in `base.AutoLoader.register_configuration()`.
- **Value** is the configuration module name under `cellpy.readers.instruments.configurations` (e.g. `neware_txt_one` → `configurations/neware_txt_one.py`).
- Config is loaded via `register_configuration_from_module(self.model, model_module_name)` in `base.py`; that builds a **ModelParameters** dataclass from the module’s attributes.

So: **one new Neware variant = one new config module + one new entry in SUPPORTED_MODELS** (and optionally a new default in prms).

---

## 4. Configuration module (e.g. `neware_txt_one.py`)

Location: **`cellpy/readers/instruments/configurations/neware_txt_*.py`**.

Each module defines (all optional except where noted):

| Attribute | Purpose |
|-----------|--------|
| **file_info** | e.g. `{"raw_extension": "csv"}`. |
| **raw_units** | Units for current, charge, voltage, energy, power, resistance, mass. Used by post_processors and summaries. |
| **unit_labels** | Labels for display (e.g. "mA", "mAh"). Used by `update_headers_with_units` when headers contain `{{ current }}` etc. |
| **normal_headers_renaming_dict** | **Required.** Maps cellpy internal key → **raw file column name**. Keys are from `headers_normal` (e.g. `data_point_txt`, `test_time_txt`, `cycle_index_txt`, `step_index_txt`, `current_txt`, `voltage_txt`, `charge_capacity_txt`, `discharge_capacity_txt`, `datetime_txt`, `step_time_txt`, etc.). After `rename_headers` post-processor, raw columns are renamed to cellpy internal names (e.g. `test_time`, `cycle_index`). |
| **states** | Step-type column and keys for charge/discharge/rest (e.g. `"Step Type"`, `["CC Chg"]`, `["CC DChg"]`, `["Rest"]`). Used for step logic and optional column selection. |
| **raw_limits** | Epsilons for step detection (current/voltage/charge stability, etc.). |
| **formatters** | `skiprows`, `sep`, `header`, `encoding`, `decimal`, `thousands`. If `sep` is None, TxtLoader uses **auto formatter** (`find_delimiter_and_start`). |
| **pre_processors** | Dict of name → enabled (e.g. `{"remove_empty_lines": True}`). Run on the **file path** before CSV read; must return path (e.g. to a new temp file). |
| **post_processors** | Dict of name → enabled. Run in order: **ORDERED_POST_PROCESSING_STEPS** first, then the rest. See below. |

Existing configs:

- **neware_txt_zero**: Ah, no `update_headers_with_units`, no `unit_labels`; simple renaming.
- **neware_txt_one** / **neware_txt_two**: mAh, with `update_headers_with_units` and `unit_labels`; template-style headers with `{{ current }}` etc.

---

## 5. Processors

### 5.1 Pre-processors (`processors/pre_processors.py`)

- Run **before** `pd.read_csv`, on the **file path**.
- Signature: `(filename: Path) -> Path` (return path to the file to read; can be a new temp file).
- Example: **remove_empty_lines** – strips blank lines, writes to a new temp file, returns that path.

Neware configs today typically do **not** set pre_processors (empty or omitted). If the new format has garbage lines or BOM, add a pre_processor or use auto formatter.

### 5.2 Post-processors (`processors/post_processors.py`)

- Run **after** loading into `data.raw`, in order.
- Signature: `(data: Data, config_params: ModelParameters) -> Data`.
- **Ordered** (run first):
  1. **update_headers_with_units** – Replaces `{{ current }}` etc. in `normal_headers_renaming_dict` with `unit_labels` so rename_headers uses the right display names.
  2. **get_column_names** – (Not implemented; placeholder.)
  3. **rename_headers** – Renames raw columns to cellpy names using `config_params.normal_headers_renaming_dict` (raw column name → cellpy name).
  4. **select_columns_to_keep** – Keeps only required + state column + any in `config_params.columns_to_keep`.
  5. **remove_last_if_bad** – Drops last row if it has more NaNs than the previous row.

- **Then** (order from config): split_capacity, split_current, cumulate_capacity_within_cycle, set_index, set_cycle_number_not_zero, convert_date_time_to_datetime, convert_step_time_to_timedelta, convert_test_time_to_timedelta.

So the critical config for a new format is **normal_headers_renaming_dict**: it must map each required cellpy key to the **exact** column name as it appears in the raw CSV (after the first data row).

---

## 6. Load flow (summary)

1. **Copy file** to temp (unless refused).
2. **Pre-process** file (if any pre_processors enabled).
3. **Parse loader kwargs** (and optionally run **auto formatter** if `sep` is None).
4. **Read CSV:** `query_file()` → `pd.read_csv(sep=..., skiprows=..., header=..., encoding=..., decimal=..., thousands=...)`.
5. Build **Data**: metadata, `data.raw = data_df`, empty summary.
6. **Post-process** `data` (ordered steps then config-defined steps).
7. **identify_last_data_point**, set `start_datetime` if missing.
8. **Validate** (Neware: check MUST_HAVE_RAW_COLUMNS and numeric types).

---

## 7. Cellpy internal column names (required for rename)

After **rename_headers**, `data.raw` must have at least these columns (from `headers_normal`), which **DataLoader.validate** checks via **MUST_HAVE_RAW_COLUMNS**:

- `test_time_txt` → `test_time`
- `step_time_txt` → `step_time`
- `current_txt` → `current`
- `voltage_txt` → `voltage`
- `step_index_txt` → `step_index`
- `cycle_index_txt` → `cycle_index`
- `charge_capacity_txt` → `charge_capacity`
- `discharge_capacity_txt` → `discharge_capacity`

Optional but common: `data_point_txt`, `datetime_txt`, `internal_resistance_txt`, `charge_energy_txt`, `discharge_energy_txt`, `power_txt`. The config’s **normal_headers_renaming_dict** maps **cellpy key** → **raw column name**; only entries present in the raw file are renamed.

---

## 8. Making it easy to add a new Neware txt format tomorrow

- **Add one config module:** Copy an existing one (e.g. `neware_txt_one.py`) to `neware_txt_<name>.py`, then:
  - Set **normal_headers_renaming_dict** to the new file’s column names.
  - Set **raw_units** / **unit_labels** to match (A vs mA, Ah vs mAh, etc.).
  - Adjust **formatters** only if you do not want auto (e.g. fix encoding, decimal).
  - Enable/disable **post_processors** as needed (e.g. `convert_date_time_to_datetime` only if you have a datetime column).
- **Register the model:** In `neware_txt.py`, add one line to **SUPPORTED_MODELS**, e.g. `"COLLEAGUE": "neware_txt_<name>"`.
- **Optional:** Set `prms.Instruments.Neware["default_model"]` or pass `model="COLLEAGUE"` in `get()`.
- **Test:** Add a small raw file under `tests/` (or testdata path), then load with `get(..., instrument="neware_txt", model="COLLEAGUE")` and assert on `len(c.data.raw)` and required columns.

No change to **base.py** or **post_processors.py** is needed for a new variant unless the format needs a new processor (e.g. new pre_processor for cleaning the file). Keep the new format’s logic in the **config module** and in **SUPPORTED_MODELS** only.

---

## 9. Prep today (so tomorrow is fast)

- **Docs:** Keep this overview and the recipe (`issue350_recipe_new_neware_txt_reader.md`) in `01-current-issues` and use the recipe when the new file arrives.
- **Env:** Ensure the dev environment and tests pass (`pytest tests/test_neware.py -v`).
- **Template:** When the file arrives, copy an existing config (e.g. `neware_txt_one.py`) to `neware_txt_<name>.py`, fill **normal_headers_renaming_dict** from the new file’s header row, add one **SUPPORTED_MODELS** entry, then run a quick `get(..., model="...")` test. No base.py or processor changes needed for a standard CSV variant.

---

## 10. References

- **Loader:** `cellpy/readers/instruments/neware_txt.py`
- **Base loader / TxtLoader / AutoLoader:** `cellpy/readers/instruments/base.py`
- **Configs:** `cellpy/readers/instruments/configurations/neware_txt_*.py`
- **Config loading:** `cellpy/readers/instruments/configurations/__init__.py` (`ModelParameters`, `register_configuration_from_module`)
- **Post-processors:** `cellpy/readers/instruments/processors/post_processors.py` (`ORDERED_POST_PROCESSING_STEPS`, `rename_headers`, etc.)
- **Pre-processors:** `cellpy/readers/instruments/processors/pre_processors.py`
- **Internal headers:** `cellpy/parameters/internal_settings.py` (`headers_normal`, `HeadersNormal`)
- **Neware tests:** `tests/test_neware.py` (and `parameters.nw_file_path` from `tests/fdv.py` / conftest)
