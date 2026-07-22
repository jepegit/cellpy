"""Helpers for prms characterization tests (issue #430)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cellpy.parameters import prmreader, prms

INVENTORY_ROOT = Path("/cellpy_inventory_root")

EXPECTED_PRMS_INVENTORY: list[tuple[str, str, object]] = [
    ("Paths", "batchfiledir", "/cellpy_inventory_root"),
    ("Paths", "cellpydatadir", "/cellpy_inventory_root"),
    ("Paths", "db_filename", "cellpy_db.xlsx"),
    ("Paths", "db_path", "/cellpy_inventory_root"),
    ("Paths", "env_file", "/cellpy_inventory_root/.env_cellpy"),
    ("Paths", "examplesdir", "/cellpy_inventory_root"),
    ("Paths", "filelogdir", "/cellpy_inventory_root"),
    ("Paths", "instrumentdir", "/cellpy_inventory_root"),
    ("Paths", "notebookdir", "/cellpy_inventory_root"),
    ("Paths", "outdatadir", "/cellpy_inventory_root"),
    ("Paths", "rawdatadir", "/cellpy_inventory_root"),
    ("Paths", "templatedir", "/cellpy_inventory_root"),
    ("FileNames", "cellpy_file_extension", "h5"),
    ("FileNames", "file_list_location", None),
    ("FileNames", "file_list_name", None),
    ("FileNames", "file_list_type", None),
    ("FileNames", "file_name_format", "YYYYMMDD_[NAME]EEE_CC_TT_RR"),
    ("FileNames", "raw_extension", "res"),
    ("FileNames", "reg_exp", None),
    ("FileNames", "sub_folders", True),
    ("Db", "db_connection", None),
    ("Db", "db_data_start_row", 2),
    ("Db", "db_file_sqlite", "excel.db"),
    ("Db", "db_header_row", 0),
    ("Db", "db_search_end_row", -1),
    ("Db", "db_search_start_row", 2),
    ("Db", "db_table_name", "db_table"),
    ("Db", "db_type", "simple_excel_reader"),
    ("Db", "db_unit_row", 1),
    ("DbCols", "area", "area"),
    ("DbCols", "argument", "argument"),
    ("DbCols", "batch", "batch"),
    ("DbCols", "cell_name", "cell"),
    ("DbCols", "cell_type", "cell_type"),
    ("DbCols", "cellpy_file_name", "cellpy_file_name"),
    ("DbCols", "comment_cell", "comment_cell"),
    ("DbCols", "comment_general", "comment_general"),
    ("DbCols", "comment_slurry", "comment_slurry"),
    ("DbCols", "exists", "exists"),
    ("DbCols", "experiment_type", "experiment_type"),
    ("DbCols", "file_name_indicator", "file_name_indicator"),
    ("DbCols", "freeze", "freeze"),
    ("DbCols", "group", "group"),
    ("DbCols", "id", "id"),
    ("DbCols", "instrument", "instrument"),
    ("DbCols", "label", "label"),
    ("DbCols", "loading", "loading_active_material"),
    ("DbCols", "mass_active", "mass_active_material"),
    ("DbCols", "mass_total", "mass_total"),
    ("DbCols", "nom_cap", "nominal_capacity"),
    ("DbCols", "nom_cap_specifics", "nominal_capacity_specifics"),
    ("DbCols", "project", "project"),
    ("DbCols", "raw_file_names", "raw_file_names"),
    ("DbCols", "selected", "selected"),
    ("DbCols", "sub_batch_01", "b01"),
    ("DbCols", "sub_batch_02", "b02"),
    ("DbCols", "sub_batch_03", "b03"),
    ("DbCols", "sub_batch_04", "b04"),
    ("DbCols", "sub_batch_05", "b05"),
    ("DbCols", "sub_batch_06", "b06"),
    ("DbCols", "sub_batch_07", "b07"),
    ("CellInfo", "active_electrode_area", 1.0),
    ("CellInfo", "active_electrode_current_collector", "standard"),
    ("CellInfo", "active_electrode_loading", 1.0),
    ("CellInfo", "active_electrode_thickness", 1.0),
    ("CellInfo", "active_electrode_type", "standard"),
    ("CellInfo", "cell_type", "standard"),
    ("CellInfo", "comment", ""),
    ("CellInfo", "counter_electrode_type", "standard"),
    ("CellInfo", "electrolyte_type", "standard"),
    ("CellInfo", "electrolyte_volume", 1.0),
    ("CellInfo", "experiment_type", "cycling"),
    ("CellInfo", "reference_electrode_current_collector", "standard"),
    ("CellInfo", "reference_electrode_type", "standard"),
    ("CellInfo", "separator_type", "standard"),
    ("CellInfo", "voltage_lim_high", 1.0),
    ("CellInfo", "voltage_lim_low", 0.0),
    ("Reader", "auto_dirs", True),
    ("Reader", "capacity_interpolation_step", 2.0),
    ("Reader", "cycle_mode", "anode"),
    ("Reader", "diagnostics", False),
    ("Reader", "ensure_step_table", False),
    ("Reader", "ensure_summary_table", False),
    ("Reader", "filestatuschecker", "size"),
    ("Reader", "force_all", False),
    ("Reader", "force_step_table_creation", True),
    ("Reader", "jupyter_executable", "jupyter"),
    ("Reader", "limit_loaded_cycles", None),
    ("Reader", "max_raw_files_to_merge", 20),
    ("Reader", "select_minimal", False),
    ("Reader", "sep", ";"),
    ("Reader", "sorted_data", True),
    ("Reader", "time_interpolation_step", 10.0),
    ("Reader", "use_cellpy_stat_file", False),
    ("Reader", "use_harmonized_raw", False),
    ("Reader", "voltage_interpolation_step", 0.01),
    ("Materials", "cell_class", "Li-Ion"),
    ("Materials", "default_mass", 1.0),
    ("Materials", "default_material", "silicon"),
    ("Materials", "default_nom_cap", 1.0),
    ("Materials", "default_nom_cap_specifics", "gravimetric"),
    ("Instruments", "Arbin.SQL_Driver", "SQL Server"),
    ("Instruments", "Arbin.SQL_PWD", "ChangeMe123"),
    ("Instruments", "Arbin.SQL_UID", "sa"),
    ("Instruments", "Arbin.SQL_server", "localhost/SQLEXPRESS"),
    ("Instruments", "Arbin.chunk_size", None),
    ("Instruments", "Arbin.detect_subprocess_need", False),
    ("Instruments", "Arbin.max_chunks", None),
    ("Instruments", "Arbin.max_res_filesize", 150000000),
    ("Instruments", "Arbin.office_version", "64bit"),
    ("Instruments", "Arbin.sub_process_path", None),
    ("Instruments", "Arbin.use_subprocess", False),
    ("Instruments", "Batmo.default_model", "bdf"),
    ("Instruments", "Maccor.default_model", "one"),
    ("Instruments", "Neware.default_model", "one"),
    ("Instruments", "custom_instrument_definitions_file", None),
    ("Instruments", "tester", None),
    ("Batch", "auto_use_file_list", False),
    ("Batch", "backend", "plotly"),
    ("Batch", "color_style_label", "seaborn-deep"),
    ("Batch", "dpi", 300),
    ("Batch", "fig_extension", "png"),
    ("Batch", "figure_type", "unlimited"),
    ("Batch", "markersize", 4),
    ("Batch", "notebook", True),
    ("Batch", "summary_plot_height", 800),
    ("Batch", "summary_plot_height_fractions", [0.2, 0.5, 0.3]),
    ("Batch", "summary_plot_width", 900),
    ("Batch", "symbol_label", "simple"),
    ("Batch", "template", "standard"),
]


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize_value(v) for v in value]
    if hasattr(value, "to_dict"):
        return _normalize_value(value.to_dict())
    if isinstance(value, Path):
        return str(value).replace("\\", "/")
    if isinstance(value, str):
        return value.replace("\\", "/")
    return value


def _flatten_section(
    section: str, data: Any, prefix: str = ""
) -> list[tuple[str, str, Any]]:
    out: list[tuple[str, str, Any]] = []
    if isinstance(data, dict):
        for key, val in sorted(data.items()):
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(val, dict):
                out.extend(_flatten_section(section, val, full_key))
            else:
                out.append((section, full_key, _normalize_value(val)))
    else:
        out.append((section, prefix, _normalize_value(data)))
    return out


def _fresh_paths_section() -> prms.PathsClass:
    root = INVENTORY_ROOT
    paths = prms.PathsClass()
    paths.outdatadir = root
    paths.rawdatadir = str(root)
    paths.cellpydatadir = str(root)
    paths.db_path = root
    paths.filelogdir = root
    paths.examplesdir = root
    paths.notebookdir = root
    paths.templatedir = root
    paths.batchfiledir = root
    paths.instrumentdir = root
    paths.db_filename = "cellpy_db.xlsx"
    paths.env_file = root / ".env_cellpy"
    return paths


def fresh_section_defaults() -> dict[str, dict]:
    return {
        "Paths": prmreader._convert_paths_to_dict(_fresh_paths_section()),
        "FileNames": prmreader._convert_to_dict(prms.FileNamesClass()),
        "Db": prmreader._convert_to_dict(prms.DbClass()),
        "DbCols": prmreader._convert_to_dict(prms.DbColsClass()),
        "CellInfo": prmreader._convert_to_dict(prms.CellInfoClass()),
        "Reader": prmreader._convert_to_dict(prms.ReaderClass()),
        "Materials": prmreader._convert_to_dict(prms.MaterialsClass()),
        "Instruments": prmreader._convert_instruments_to_dict(
            prms.InstrumentsClass(
                tester=None,
                custom_instrument_definitions_file=None,
                Arbin=prms.Arbin,
                Maccor=prms.Maccor,
                Neware=prms.Neware,
                Batmo=prms.Batmo,
            )
        ),
        "Batch": prmreader._convert_to_dict(prms.BatchClass(backend="plotly")),
    }


def collect_prms_inventory() -> list[tuple[str, str, Any]]:
    inventory: list[tuple[str, str, Any]] = []
    for section, data in fresh_section_defaults().items():
        inventory.extend(_flatten_section(section, data))
    return sorted(inventory, key=lambda t: (t[0], t[1]))


def assert_inventory_equal(
    actual: list[tuple[str, str, Any]],
    expected: list[tuple[str, str, Any]],
) -> None:
    actual_map = {(s, f): v for s, f, v in actual}
    expected_map = {(s, f): v for s, f, v in expected}
    added = sorted(set(actual_map) - set(expected_map))
    removed = sorted(set(expected_map) - set(actual_map))
    changed = sorted(
        key
        for key in set(actual_map) & set(expected_map)
        if actual_map[key] != expected_map[key]
    )
    lines: list[str] = []
    if added:
        lines.append("Added fields: " + ", ".join(f"{s}.{f}" for s, f in added))
    if removed:
        lines.append("Removed fields: " + ", ".join(f"{s}.{f}" for s, f in removed))
    for section, field in changed:
        lines.append(
            f"Changed {section}.{field}: expected {expected_map[(section, field)]!r}, "
            f"got {actual_map[(section, field)]!r}"
        )
    if lines:
        raise AssertionError("prms inventory mismatch:\n" + "\n".join(lines))


def write_minimal_prm_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
