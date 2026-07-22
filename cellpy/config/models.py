"""Pydantic models mirroring legacy prms sections (issue #452)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cellpycore.units import CellpyUnits
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from cellpy.config.types import LimitLoadedCycles, OtherPathField, PathField

class PathsConfig(BaseModel):
    """Paths used in cellpy."""

    # validate_assignment keeps the mutable-session ergonomics *validated*
    # (config plan §3.1): assigning a plain string re-runs the PathField /
    # OtherPathField coercion instead of storing a raw str that breaks
    # serialization later (seen via `cellpy info --params` after batch runs).
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    outdatadir: PathField = Path.cwd()
    rawdatadir: OtherPathField = Path.cwd()
    cellpydatadir: OtherPathField = Path.cwd()
    db_path: PathField = Path.cwd()
    filelogdir: PathField = Path.cwd()
    examplesdir: PathField = Path.cwd()
    notebookdir: PathField = Path.cwd()
    templatedir: PathField = Path.cwd()
    batchfiledir: PathField = Path.cwd()
    instrumentdir: PathField = Path.cwd()
    db_filename: str = "cellpy_db.xlsx"
    env_file: PathField = Path.home() / ".env_cellpy"


class FileNamesConfig(BaseModel):
    """Settings for file names and file handling."""

    file_name_format: str = "YYYYMMDD_[NAME]EEE_CC_TT_RR"
    raw_extension: str = "res"
    reg_exp: str | None = None
    sub_folders: bool = True
    file_list_location: str | None = None
    file_list_type: str | None = None
    file_list_name: str | None = None
    cellpy_file_extension: str = "h5"


class ReaderConfig(BaseModel):
    """Settings for reading data."""

    diagnostics: bool = False
    filestatuschecker: str = "size"
    force_step_table_creation: bool = True
    force_all: bool = False
    sep: str = ";"
    cycle_mode: str = "anode"
    sorted_data: bool = True
    select_minimal: bool = False
    limit_loaded_cycles: LimitLoadedCycles = None
    ensure_step_table: bool = False
    ensure_summary_table: bool = False
    voltage_interpolation_step: float = 0.01
    time_interpolation_step: float = 10.0
    capacity_interpolation_step: float = 2.0
    use_cellpy_stat_file: bool = False
    auto_dirs: bool = True
    max_raw_files_to_merge: int = 20
    jupyter_executable: str = "jupyter"
    # Phase B / #560 flag day: opt-in to producing the native raw from the
    # two-stage harmonize(parse()) pipeline rather than the legacy
    # loader()+to_native rename. Default OFF: the flip currently drops aux
    # columns not in aux_map and renumbers data_point, and applies to loaders
    # whose two-stage path is unverified, so it is not yet safe as the default.
    # Turn on per session once a loader is hardened. Single-file loads only;
    # multi-file merges and parse failures keep the legacy path regardless.
    use_harmonized_raw: bool = True


class DbConfig(BaseModel):
    """Settings for the simple database."""

    db_type: str = "simple_excel_reader"
    db_table_name: str = "db_table"
    db_header_row: int = 0
    db_unit_row: int = 1
    db_data_start_row: int = 2
    db_search_start_row: int = 2
    db_search_end_row: int = -1
    db_file_sqlite: str = "excel.db"
    db_connection: str | None = None


class DbColsConfig(BaseModel):
    """Column names for the simple excel database reader."""

    id: str = "id"
    exists: str = "exists"
    project: str = "project"
    label: str = "label"
    group: str = "group"
    selected: str = "selected"
    cell_name: str = "cell"
    cell_type: str = "cell_type"
    experiment_type: str = "experiment_type"
    mass_active: str = "mass_active_material"
    area: str = "area"
    mass_total: str = "mass_total"
    loading: str = "loading_active_material"
    nom_cap: str = "nominal_capacity"
    nom_cap_specifics: str = "nominal_capacity_specifics"
    file_name_indicator: str = "file_name_indicator"
    instrument: str = "instrument"
    raw_file_names: str = "raw_file_names"
    cellpy_file_name: str = "cellpy_file_name"
    comment_slurry: str = "comment_slurry"
    comment_cell: str = "comment_cell"
    comment_general: str = "comment_general"
    freeze: str = "freeze"
    argument: str = "argument"
    batch: str = "batch"
    sub_batch_01: str = "b01"
    sub_batch_02: str = "b02"
    sub_batch_03: str = "b03"
    sub_batch_04: str = "b04"
    sub_batch_05: str = "b05"
    sub_batch_06: str = "b06"
    sub_batch_07: str = "b07"


class BatchConfig(BaseModel):
    """Settings for batch processing."""

    auto_use_file_list: bool = False
    template: str = "standard"
    fig_extension: str = "png"
    backend: str = "plotly"
    notebook: bool = True
    dpi: int = 300
    markersize: int = 4
    symbol_label: str = "simple"
    color_style_label: str = "seaborn-deep"
    figure_type: str = "unlimited"
    summary_plot_width: int = 900
    summary_plot_height: int = 800
    summary_plot_height_fractions: list[float] = Field(default_factory=lambda: [0.2, 0.5, 0.3])


class ArbinConfig(BaseModel):
    """Arbin instrument knobs (SQL credentials live in ``secrets``)."""

    model_config = ConfigDict(extra="allow")

    max_res_filesize: int = 150_000_000
    chunk_size: int | None = None
    max_chunks: int | None = None
    use_subprocess: bool = False
    detect_subprocess_need: bool = False
    sub_process_path: str | None = None
    office_version: str = "64bit"


class MaccorConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    default_model: str = "one"


class NewareConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    default_model: str = "one"


class BatmoConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    default_model: str = "bdf"


class InstrumentsConfig(BaseModel):
    """Instrument settings (legacy capitalized instrument keys preserved)."""

    tester: str | None = None
    custom_instrument_definitions_file: str | None = None
    Arbin: ArbinConfig = Field(default_factory=ArbinConfig)
    Maccor: MaccorConfig = Field(default_factory=MaccorConfig)
    Neware: NewareConfig = Field(default_factory=NewareConfig)
    Batmo: BatmoConfig = Field(default_factory=BatmoConfig)


class CellInfoDefaults(BaseModel):
    """Default cell parameters (values in cellpy units by convention)."""

    voltage_lim_low: float = 0.0
    voltage_lim_high: float = 1.0
    active_electrode_area: float = 1.0
    active_electrode_thickness: float = 1.0
    active_electrode_loading: float = 1.0
    electrolyte_volume: float = 1.0
    electrolyte_type: str = "standard"
    active_electrode_type: str = "standard"
    counter_electrode_type: str = "standard"
    reference_electrode_type: str = "standard"
    experiment_type: str = "cycling"
    cell_type: str = "standard"
    separator_type: str = "standard"
    active_electrode_current_collector: str = "standard"
    reference_electrode_current_collector: str = "standard"
    comment: str = ""


class MaterialsDefaults(BaseModel):
    """Default material-specific values (cellpy units by convention)."""

    cell_class: str = "Li-Ion"
    default_material: str = "silicon"
    default_mass: float = 1.0
    default_nom_cap: float = 1.0
    default_nom_cap_specifics: str = "gravimetric"


class ScienceDefaults(BaseModel):
    """Merged CellInfo + Materials defaults for metadata construction."""

    cell_info: CellInfoDefaults = Field(default_factory=CellInfoDefaults)
    materials: MaterialsDefaults = Field(default_factory=MaterialsDefaults)


class UnitsConfig(BaseModel):
    """Session unit policy; keys validated against ``cellpycore.units.CellpyUnits``."""

    current: str = "A"
    charge: str = "mAh"
    voltage: str = "V"
    time: str = "sec"
    resistance: str = "ohm"
    power: str = "W"
    energy: str = "Wh"
    frequency: str = "hz"
    mass: str = "mg"
    nominal_capacity: str = "mAh/g"
    specific_gravimetric: str = "g"
    specific_areal: str = "cm**2"
    specific_volumetric: str = "cm**3"
    length: str = "cm"
    area: str = "cm**2"
    volume: str = "cm**3"
    temperature: str = "C"
    pressure: str = "bar"

    def as_cellpy_units(self) -> CellpyUnits:
        return CellpyUnits(**self.model_dump())


class SecretsConfig(BaseModel):
    """Credentials — env / ``.env`` only; never read from or written to TOML.

    ``password`` is a :class:`~pydantic.SecretStr`, so it does not leak through
    ``repr()``, logs, tracebacks or ``model_dump()``. Read the actual value with
    :meth:`get_password` at the point of use, never earlier.

    The other three are *not* secret material — a host, a user name and a path
    to a key file — so they stay plain strings. They live here because they
    arrive from the same env layer and the same consumers need them together
    (config plan decision 5).
    """

    model_config = ConfigDict(validate_assignment=True)

    password: SecretStr | None = None
    key_filename: str | None = None
    host: str | None = None
    user: str | None = None

    def get_password(self) -> str | None:
        """The plain password, or None. Call at the point of use."""
        return None if self.password is None else self.password.get_secret_value()


class CellpyConfig(BaseModel):
    """Root configuration object (parallel to legacy prms)."""

    model_config = ConfigDict(validate_assignment=True)

    paths: PathsConfig = Field(default_factory=PathsConfig)
    file_names: FileNamesConfig = Field(default_factory=FileNamesConfig)
    reader: ReaderConfig = Field(default_factory=ReaderConfig)
    db: DbConfig = Field(default_factory=DbConfig)
    db_cols: DbColsConfig = Field(default_factory=DbColsConfig)
    batch: BatchConfig = Field(default_factory=BatchConfig)
    instruments: InstrumentsConfig = Field(default_factory=InstrumentsConfig)
    defaults: ScienceDefaults = Field(default_factory=ScienceDefaults)
    units: UnitsConfig = Field(default_factory=UnitsConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)

    def model_dump_for_file(self) -> dict[str, Any]:
        """Dump config suitable for TOML persistence (secrets excluded)."""

        data = self.model_dump(mode="json")
        data.pop("secrets", None)
        return data


def inventory_paths_config(root: Path) -> PathsConfig:
    """Build ``PathsConfig`` with every directory rooted at ``root`` (parity tests)."""

    return PathsConfig(
        outdatadir=root,
        rawdatadir=root,
        cellpydatadir=root,
        db_path=root,
        filelogdir=root,
        examplesdir=root,
        notebookdir=root,
        templatedir=root,
        batchfiledir=root,
        instrumentdir=root,
        db_filename="cellpy_db.xlsx",
        env_file=root / ".env_cellpy",
    )


def default_inventory_config(root: Path) -> CellpyConfig:
    """Fresh config for inventory parity (fixed path root, otherwise model defaults)."""

    return CellpyConfig(paths=inventory_paths_config(root))
