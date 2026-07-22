# Configuration reference

Auto-generated from the configuration models. Do not edit by hand — regenerate with:

```shell
uv run python -m cellpy.config.reference
```

Settings are resolved in layers, later winning over earlier: **defaults → user
`cellpy.toml` → project `cellpy.toml` → environment / `.env` → runtime
overrides**. Ask where a value came from with `cellpy.config.sources()`.

Environment variables use the pattern `CELLPY_<SECTION>__<FIELD>` (two
underscores between section and field), e.g. `CELLPY_READER__AUTO_DIRS=0`.

## paths

Paths used in cellpy.

| Setting | Type | Default |
| --- | --- | --- |
| `outdatadir` | `Path` | `<current directory>` |
| `rawdatadir` | `OtherPath` | `<current directory>` |
| `cellpydatadir` | `OtherPath` | `<current directory>` |
| `db_path` | `Path` | `<current directory>` |
| `filelogdir` | `Path` | `<current directory>` |
| `examplesdir` | `Path` | `<current directory>` |
| `notebookdir` | `Path` | `<current directory>` |
| `templatedir` | `Path` | `<current directory>` |
| `batchfiledir` | `Path` | `<current directory>` |
| `instrumentdir` | `Path` | `<current directory>` |
| `db_filename` | `str` | `cellpy_db.xlsx` |
| `env_file` | `Path` | `<home>/.env_cellpy` |


## file_names

Settings for file names and file handling.

| Setting | Type | Default |
| --- | --- | --- |
| `file_name_format` | `str` | `YYYYMMDD_[NAME]EEE_CC_TT_RR` |
| `raw_extension` | `str` | `res` |
| `reg_exp` | `str | None` | — |
| `sub_folders` | `bool` | `True` |
| `file_list_location` | `str | None` | — |
| `file_list_type` | `str | None` | — |
| `file_list_name` | `str | None` | — |
| `cellpy_file_extension` | `str` | `h5` |


## reader

Settings for reading data.

| Setting | Type | Default |
| --- | --- | --- |
| `diagnostics` | `bool` | `False` |
| `filestatuschecker` | `str` | `size` |
| `force_step_table_creation` | `bool` | `True` |
| `force_all` | `bool` | `False` |
| `sep` | `str` | `;` |
| `cycle_mode` | `str` | `anode` |
| `sorted_data` | `bool` | `True` |
| `select_minimal` | `bool` | `False` |
| `limit_loaded_cycles` | `int | tuple[int, int] | list[int] | None` | — |
| `ensure_step_table` | `bool` | `False` |
| `ensure_summary_table` | `bool` | `False` |
| `voltage_interpolation_step` | `float` | `0.01` |
| `time_interpolation_step` | `float` | `10.0` |
| `capacity_interpolation_step` | `float` | `2.0` |
| `use_cellpy_stat_file` | `bool` | `False` |
| `auto_dirs` | `bool` | `True` |
| `max_raw_files_to_merge` | `int` | `20` |
| `jupyter_executable` | `str` | `jupyter` |
| `use_harmonized_raw` | `bool` | `True` |


## db

Settings for the simple database.

| Setting | Type | Default |
| --- | --- | --- |
| `db_type` | `str` | `simple_excel_reader` |
| `db_table_name` | `str` | `db_table` |
| `db_header_row` | `int` | `0` |
| `db_unit_row` | `int` | `1` |
| `db_data_start_row` | `int` | `2` |
| `db_search_start_row` | `int` | `2` |
| `db_search_end_row` | `int` | `-1` |
| `db_file_sqlite` | `str` | `excel.db` |
| `db_connection` | `str | None` | — |


## db_cols

Column names for the simple excel database reader.

| Setting | Type | Default |
| --- | --- | --- |
| `id` | `str` | `id` |
| `exists` | `str` | `exists` |
| `project` | `str` | `project` |
| `label` | `str` | `label` |
| `group` | `str` | `group` |
| `selected` | `str` | `selected` |
| `cell_name` | `str` | `cell` |
| `cell_type` | `str` | `cell_type` |
| `experiment_type` | `str` | `experiment_type` |
| `mass_active` | `str` | `mass_active_material` |
| `area` | `str` | `area` |
| `mass_total` | `str` | `mass_total` |
| `loading` | `str` | `loading_active_material` |
| `nom_cap` | `str` | `nominal_capacity` |
| `nom_cap_specifics` | `str` | `nominal_capacity_specifics` |
| `file_name_indicator` | `str` | `file_name_indicator` |
| `instrument` | `str` | `instrument` |
| `raw_file_names` | `str` | `raw_file_names` |
| `cellpy_file_name` | `str` | `cellpy_file_name` |
| `comment_slurry` | `str` | `comment_slurry` |
| `comment_cell` | `str` | `comment_cell` |
| `comment_general` | `str` | `comment_general` |
| `freeze` | `str` | `freeze` |
| `argument` | `str` | `argument` |
| `batch` | `str` | `batch` |
| `sub_batch_01` | `str` | `b01` |
| `sub_batch_02` | `str` | `b02` |
| `sub_batch_03` | `str` | `b03` |
| `sub_batch_04` | `str` | `b04` |
| `sub_batch_05` | `str` | `b05` |
| `sub_batch_06` | `str` | `b06` |
| `sub_batch_07` | `str` | `b07` |


## batch

Settings for batch processing.

| Setting | Type | Default |
| --- | --- | --- |
| `auto_use_file_list` | `bool` | `False` |
| `template` | `str` | `standard` |
| `fig_extension` | `str` | `png` |
| `backend` | `str` | `plotly` |
| `notebook` | `bool` | `True` |
| `dpi` | `int` | `300` |
| `markersize` | `int` | `4` |
| `symbol_label` | `str` | `simple` |
| `color_style_label` | `str` | `seaborn-deep` |
| `figure_type` | `str` | `unlimited` |
| `summary_plot_width` | `int` | `900` |
| `summary_plot_height` | `int` | `800` |
| `summary_plot_height_fractions` | `list` | `[0.2, 0.5, 0.3]` |


## instruments

Instrument settings (legacy capitalized instrument keys preserved).

| Setting | Type | Default |
| --- | --- | --- |
| `tester` | `str | None` | — |
| `custom_instrument_definitions_file` | `str | None` | — |
| `Arbin` | `ArbinConfig` | — |
| `Maccor` | `MaccorConfig` | — |
| `Neware` | `NewareConfig` | — |
| `Batmo` | `BatmoConfig` | — |


## defaults

Merged CellInfo + Materials defaults for metadata construction.

| Setting | Type | Default |
| --- | --- | --- |
| `cell_info` | `CellInfoDefaults` | — |
| `materials` | `MaterialsDefaults` | — |


## units

Session unit policy; keys validated against ``cellpycore.units.CellpyUnits``.

| Setting | Type | Default |
| --- | --- | --- |
| `current` | `str` | `A` |
| `charge` | `str` | `mAh` |
| `voltage` | `str` | `V` |
| `time` | `str` | `sec` |
| `resistance` | `str` | `ohm` |
| `power` | `str` | `W` |
| `energy` | `str` | `Wh` |
| `frequency` | `str` | `hz` |
| `mass` | `str` | `mg` |
| `nominal_capacity` | `str` | `mAh/g` |
| `specific_gravimetric` | `str` | `g` |
| `specific_areal` | `str` | `cm**2` |
| `specific_volumetric` | `str` | `cm**3` |
| `length` | `str` | `cm` |
| `area` | `str` | `cm**2` |
| `volume` | `str` | `cm**3` |
| `temperature` | `str` | `C` |
| `pressure` | `str` | `bar` |


## secrets

Credentials are read from the **environment only** — never from a config file.
A `[secrets]` section in a `cellpy.toml` is an error, not a silent override, so
that a credential you thought was configured cannot quietly fail to be.

| Setting | Environment variable | Notes |
| --- | --- | --- |
| `password` | `CELLPY_PASSWORD` | never echoed in reprs, dumps or logs |
| `key_filename` | `CELLPY_KEY_FILENAME` | not secret material; grouped here because it arrives with them |
| `host` | `CELLPY_HOST` | not secret material; grouped here because it arrives with them |
| `user` | `CELLPY_USER` | not secret material; grouped here because it arrives with them |
