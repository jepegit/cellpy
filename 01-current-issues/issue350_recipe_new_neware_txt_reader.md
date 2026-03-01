# Recipe: Add a new Neware txt reader (issue 350)

Use this checklist when you receive a new Neware text file and need a working reader quickly.

---

## Before you start (today / prep)

- **Read** `01-current-issues/issue350_neware_loading_overview.md`.
- **Confirm** you have a working env (e.g. `cellpy_dev_321` or `.venv`), and tests run:  
`pytest tests/test_neware.py -v`
- **Locate** where test data lives: `parameters.nw_file_path` (from `tests/fdv.py` / conftest) or your own raw data dir.
- **Decide** a short model name for the new format (e.g. `COLLEAGUE`, `LAB_X`, `V2`). It will be the key in `SUPPORTED_MODELS` and the value used in `get(..., model="...")`.

---

## When you have the new file (tomorrow)

### 1. Inspect the file

- Open the file in a text editor or Excel. Note:
  - **Encoding** (UTF-8, ISO-8859-1, etc.).
  - **Delimiter** (tab `\t`, comma `,`, semicolon `;`).
  - **Header row index** (0-based: which row has column names?).
  - **Skip rows** (any intro lines before the header?).
  - **Decimal** (`.` or `,`).
- **List exact column names** in the first data row (copy-paste from the file). You will map these to cellpy names.

### 2. Map columns to cellpy

- Identify which raw column corresponds to each required cellpy quantity:

  | Cellpy (internal)  | Config key (renaming dict) | Your file’s column name |
  | ------------------ | -------------------------- | ----------------------- |
  | test_time          | test_time_txt              | _______________________ |
  | step_time          | step_time_txt              | _______________________ |
  | current            | current_txt                | _______________________ |
  | voltage            | voltage_txt                | _______________________ |
  | step_index         | step_index_txt             | _______________________ |
  | cycle_index        | cycle_index_txt            | _______________________ |
  | charge_capacity    | charge_capacity_txt        | _______________________ |
  | discharge_capacity | discharge_capacity_txt     | _______________________ |

- Optional: data_point, date_time, internal_resistance, charge_energy, discharge_energy, power. Add rows as needed.
- Note **units** in headers or in the file (A vs mA, Ah vs mAh, etc.) for `raw_units` and `unit_labels`.

### 3. Add configuration module

- Copy an existing config as template:
  - `cellpy/readers/instruments/configurations/neware_txt_one.py` → `neware_txt_<your_name>.py`
  - Or `neware_txt_zero.py` if you prefer minimal options.
- In the new file:
  - Set **normal_headers_renaming_dict**: keys = cellpy keys (e.g. `test_time_txt`), values = **exact** raw column names from the new file.
  - Set **raw_units** (e.g. `"current": "mA"`, `"charge": "mAh"`).
  - Set **unit_labels** if you use `update_headers_with_units` (e.g. same as raw_units or display labels).
  - Set **formatters**: at least `decimal`, and `sep`/`encoding`/`skiprows`/`header` if you do **not** rely on auto formatter.
  - Keep or adjust **states** (column name and charge/discharge/rest keys) if the file has a step-type column.
  - Keep **post_processors** as in the template; disable only what does not apply (e.g. no datetime column → `convert_date_time_to_datetime: False`).

### 4. Register the model

- In `**cellpy/readers/instruments/neware_txt.py`**, add one entry to **SUPPORTED_MODELS**:
  - `"<MODEL_NAME>": "neware_txt_<your_config_file_name>"`  
  - Example: `"COLLEAGUE": "neware_txt_colleague"`.

### 5. Test

- Put a **small** sample of the new file in test data (e.g. under `tests/` or the path used by your `parameters` fixture).
- Load it:
  - `c = get(filename=path, instrument="neware_txt", model="<MODEL_NAME>", testing=True)`
- Assert:
  - `len(c.data.raw) > 0`
  - No missing required columns (validation should pass).
  - Optionally: `len(c.data.summary) >= 0` (summary may be built later).
- Add or update a test in `**tests/test_neware.py`** that uses the new file and `model="<MODEL_NAME>"` so it stays regression-tested.

### 6. Optional

- Set default model in `**prms.Instruments.Neware**` (e.g. in `.cellpy_prms_default.conf` or in code) so you don’t have to pass `model=` every time.
- If the file needs **pre-processing** (e.g. strip BOM or blank lines), add or enable a pre_processor in the config and ensure the processor exists in `**processors/pre_processors.py`**.

---

## Quick reference

- **Config dir:** `cellpy/readers/instruments/configurations/`
- **Model registry:** `cellpy/readers/instruments/neware_txt.py` → `SUPPORTED_MODELS`
- **Internal header keys:** `cellpy/parameters/internal_settings.py` → `headers_normal` (e.g. `test_time_txt`, `cycle_index_txt`)
- **Overview:** `01-current-issues/issue350_neware_loading_overview.md`

---

## If something fails

- **Missing columns:** Check that **normal_headers_renaming_dict** uses the **exact** raw column names (spaces, case, special chars).
- **Wrong delimiter/encoding:** Use **formatters** in config or pass `sep=`, `encoding=` to `get()`. Or rely on auto formatter (`sep: None` in formatters).
- **Bad last row:** `remove_last_if_bad` in post_processors should trim it; if not, add a pre_processor or fix the sample file.
- **Validation error:** Ensure all **MUST_HAVE_RAW_COLUMNS** (in `neware_txt.py`) are present after rename; add the mapping in the config for any missing one.

