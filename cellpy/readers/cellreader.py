    # -*- coding: utf-8 -*-
"""Datareader for cell testers and potentiostats.

This module is used for loading data and databases created by different cell
testers and exporting them in a common hdf5-format.

Examples:
    >>> c = cellpy.get(["super_battery_run_01.res", "super_battery_run_02.res"]) # loads and merges the runs
    >>> voltage_curves = c.get_cap()
    >>> c.save("super_battery_run.h5")
"""

import cellpy.config as config

import collections
import copy
import logging
import numbers
import os
import sys
import time
import datetime
import uuid
import warnings
from pathlib import Path
from typing import Union, List, Optional, Iterable, Any

import numpy as np

from . import externals as externals
from cellpy.readers import data_structures as ds
from cellpy.exporters import tabular as exporters_tabular
from cellpy.readers import capacity_curves
from cellpy.readers import slicing
from cellpy.readers import test_meta
import cellpy.internals.connections as internals

from cellpy.exceptions import (
    DeprecatedFeature,
    MixedCycleModesError,
    NoDataFound,
)
from cellpy.parameters import prms
from cellpy.parameters.internal_settings import (
    get_cellpy_units,
    headers_normal,
    headers_step_table,
    headers_summary,
    merge_raw_units,
    get_default_output_units,
    PICKLE_PROTOCOL,
    CellpyUnits,
)

# cellpy-core seam: CellpyCell delegates Data ownership and the per-cycle summary
# pipeline to cellpy-core. OldCellpyCellCore is the legacy bridge that restores the
# old headers/units (identical to cellpy.parameters.internal_settings) that cellpy
# still expects. cellpy-core's __init__ is intentionally empty, so import submodules.
from cellpycore import units as core_units
from cellpycore.cell_core import OldCellpyCellCore

from cellpy.readers.cellpy_file import dtype as cellpy_file_dtype
from cellpy.readers.cellpy_file import fids as cellpy_file_fids
from cellpy.readers.cellpy_file import read as cellpy_file_read
from cellpy.readers.cellpy_file import write as cellpy_file_write

DIGITS_C_RATE = 5


# TODO: @jepe - new feature - method for assigning new cycle numbers and step numbers
#   - Sometimes the user forgets to increment the cycle number and it would be good
#   to have a method so that its possible to set new cycle numbers manually
#   - Some testers merges different steps into one (e.g CC-CV), it would be nice to have
#   a method for "splitting that up"

# TODO: @jepe - performance warnings - mixed types within cols (pytables)

# warnings.filterwarnings("ignore", category=wq.pandas.io.pytables.PerformanceWarning)
# externals.pandas.set_option("mode.chained_assignment", None)  # "raise", "warn", None

_module_logger = logging.getLogger(__name__)


# def ds.Q(value, *args, **kwargs):
#     """Convert value to pint quantity."""
#     ureg, Q = ds.get_pint_unit_registry()
#     return Q(value, *args, **kwargs)


# Instruments that read from a database rather than a file (used for the
# provenance ``source_kind`` and for cellpy.get's db-path detection).
DB_READER_INSTRUMENTS = ("arbin_sql", "arbin_sql_7")


class CellpyCell:
    """Main class for working and storing data.

    This class is the main work-horse for cellpy where methods for
    reading, selecting, and tweaking your data is located. It also contains the
    header definitions, both for the cellpy hdf5 format, and for the various
    cell-tester file-formats that can be read.

    Attributes:
        data: ``cellpy.Data`` object containing the data
        cellpy_units: cellpy.units object
        cellpy_datadir: path to cellpy data directory
        raw_datadir: path to raw data directory
        filestatuschecker: filestatuschecker object
        force_step_table_creation: force step table creation
        ensure_step_table: ensure step table
        limit_loaded_cycles: limit loaded cycles
        profile: profile
        select_minimal: select minimal
        empty: empty
        forced_errors: forced errors
        capacity_modifiers: capacity modifiers
        sep: delimiter to use when reading (when applicable) and exporting files
        cycle_mode: cycle mode
        tester: tester
        cell_name: cell name (session name, defaults to concatenated names of the subtests)
    """

    # TODO: CellpyCell contains many thousand lines of code. It needs to be simplified. Use dependency injection to
    #   separate concerns better!
    def __repr__(self):
        txt = f"<CellpyCell> (id={hex(id(self))})"
        if self.cell_name:
            txt += f" [name={self.cell_name}]"
        return txt

    def _repr_html_(self):
        header = f"""
            <h2>CellpyCell-object</h2>
            <b>id</b>: {hex(id(self))} <br>
            <b>name</b>: {self.cell_name} <br>
            <b>tester</b>: {self.tester} <br>
            <b>cycle_mode</b>: {self.cycle_mode} <br>
            <b>sep</b>: {self.sep} <br>
            <b>cellpy_datadir</b>: {self.cellpy_datadir} <br>
            <b>raw_datadir</b>: {self.raw_datadir} <br>
        """
        all_vars = "<p>"
        all_vars += f"""
            <b>capacity_modifiers</b>: {self.capacity_modifiers} <br>
            <b>empty</b>: {self.empty} <br>
            <b>ensure_step_table</b>: {self.ensure_step_table} <br>
            <b>filestatuschecker</b>: {self.filestatuschecker} <br>
            <b>force_step_table_creation</b>: {self.force_step_table_creation} <br>
            <b>forced_errors</b>: {self.forced_errors} <br>
            <b>limit_loaded_cycles</b>: {self.limit_loaded_cycles} <br>
            <b>profile</b>: {self.profile} <br>
            <b>cellpy_units</b>: {self.cellpy_units} <br>
            <b>select_minimal</b>: {self.select_minimal} <br>
            <b>selected_scans</b>: {self.selected_scans} <br>
        """
        all_vars += "</p>"

        cell_txt = ""

        try:
            data_txt = self.data._repr_html_()
        except NoDataFound:
            cell_txt += "<h3>No data</h3>"
        else:
            cell_txt += "<h3>data</h3>"
            cell_txt += f"<blockquote>{data_txt}</blockquote>"
        return header + all_vars + cell_txt

    def __str__(self):
        txt = "CellpyCell\n"
        txt += "----------\n"
        if self.cell_name:
            txt += f"session name: {self.cell_name}\n"
        if self.tester:
            txt += f"tester: {self.tester}\n"
            try:
                if self.data:
                    txt += "data:\n"
                    for t in str(self.data).split("\n"):
                        txt += "     "
                        txt += t
                        txt += "\n"
                    txt += "\n"
            except NoDataFound:
                txt += "datasets: EMPTY\n"
        else:
            txt += "datasets: EMPTY"
        txt += "\n"
        return txt

    def __bool__(self):
        if self.data:
            return True
        else:
            return False

    def __len__(self):
        if self.data:
            return 1
        else:
            return 0

    def __init__(
        self,
        filenames=None,
        selected_scans=None,
        profile=False,
        filestatuschecker=None,  # "modified"
        tester=None,
        initialize=False,
        cellpy_units=None,
        output_units=None,
        debug=False,
        native_schema=False,
        core=None,
        instrument_factory=None,
    ):
        """
        Args:
            filenames: list of files to load.
            selected_scans:
            profile: experimental feature.
            filestatuschecker: property to compare cellpy and raw-files;
               default read from prms-file.
            tester: instrument used (e.g. "arbin_res") (checks prms-file as
               default).
            initialize: create a dummy (empty) dataset; defaults to False.
            cellpy_units (dict): sent to cellpy.parameters.internal_settings.get_cellpy_units
            output_units (dict): sent to cellpy.parameters.internal_settings.get_default_output_units
            debug (bool): set to True if you want to see debug messages.
            core (CellpyCellCore): injected core seam (issue #520, DI). When
                given it is used as-is (it owns the ``Data`` object and runs
                the step/summary engine); when None the default is built from
                the ``native_schema`` flag.
            instrument_factory (InstrumentFactory): injected loader registry
                (issue #520, DI). When None,
                ``register_instrument_readers()`` builds the default factory.
            native_schema (bool): opt-in feature flag (issue #511, V2-11).
                When True, frames are kept in native cellpy-core column names
                and the polars engine runs directly (no legacy rename
                sandwich). Supported pipeline: ``from_raw`` / ``load`` →
                ``make_step_table`` → ``make_summary`` → ``save`` (v9).
                Legacy-named consumers (``get_cap``, exporters, plotting,
                campaign merge) are not supported on a native-schema cell.
        """
        # TODO v 1.1: move to data (allow for multiple testers for same cell)
        if tester is None:
            self.tester = config.instruments.tester
            logging.debug(f"reading instrument from prms: {config.instruments}")
        else:
            self.tester = tester

        self.loader = None  # this will be set in the function set_instrument
        self.debug = debug
        logging.debug("created CellpyCell instance")

        # cellpy-core seam: the core owns the Data object and runs the per-cycle
        # summary pipeline. Construct it without initializing so that cellpy's own
        # initialize() creates the cellpy ``ds.Data`` it expects (the data
        # property reads/writes ``self.core._data``). Under the ``native_schema``
        # opt-in (#511) the legacy bridge is replaced by the rename-free
        # pandas<->polars adapter. An injected ``core`` (#520, DI) wins over
        # both defaults.
        self.native_schema = bool(native_schema)
        if core is not None:
            self.core = core
        elif self.native_schema:
            from cellpy.readers.native_core import NativeCellpyCellCore

            self.core = NativeCellpyCellCore(initialize=False, debug=debug)
        else:
            self.core = OldCellpyCellCore(initialize=False, debug=debug)

        self._cell_name = None
        self._initial_cells = None
        self.group = None
        self.last_uploaded_from = None
        self.last_uploaded_at = None
        self.cellpy_file_name = None
        self.cellpy_object_created_at = datetime.datetime.now()

        self.profile = profile

        self.minimum_selection = {}
        self.filestatuschecker = filestatuschecker or config.reader.filestatuschecker
        self.forced_errors = 0

        self.file_names = filenames or []
        if not self._is_listtype(self.file_names):
            self.file_names = [self.file_names]

        self.selected_scans = selected_scans or []
        if not self._is_listtype(self.selected_scans):
            self.selected_scans = [self.selected_scans]

        self.overwrite_able = True  # attribute that prevents saving to the same filename as loaded from if False

        self.capacity_modifiers = ["reset"]

        self.list_of_step_types = [
            "charge",
            "discharge",
            "cv_charge",
            "cv_discharge",
            "taper_charge",
            "taper_discharge",
            "charge_cv",
            "discharge_cv",
            "ocvrlx_up",
            "ocvrlx_down",
            "ir",
            "rest",
            "not_known",
        ]
        # - options
        self.force_step_table_creation = config.reader.force_step_table_creation
        self.force_all = config.reader.force_all
        self.sep = config.reader.sep
        self._cycle_mode = None
        self.select_minimal = config.reader.select_minimal
        self.limit_loaded_cycles = config.reader.limit_loaded_cycles
        self.limit_data_points = None
        self.ensure_step_table = config.reader.ensure_step_table
        self.ensure_summary_table = config.reader.ensure_summary_table
        self.raw_datadir = internals.OtherPath(config.paths.rawdatadir)
        self.cellpy_datadir = internals.OtherPath(config.paths.cellpydatadir)
        self.auto_dirs = config.reader.auto_dirs  # v2.0

        # - headers and instruments
        self.headers_normal = headers_normal
        self.headers_summary = headers_summary
        self.headers_step_table = headers_step_table
        self.instrument_factory = instrument_factory  # injected (#520) or None
        self.register_instrument_readers()
        self.set_instrument()
        # - units used by cellpy
        self.cellpy_units = get_cellpy_units(cellpy_units)
        self.output_units = get_default_output_units(output_units)  # v2.0

        if initialize:
            self.initialize()

    def initialize(self):
        """Initialize the CellpyCell object with empty Data instance."""

        logging.debug("Initializing...")
        self.core._data = ds.Data()

    # the batch utility might be using session name
    # the cycle and ica collector are using session name
    # improvement suggestion: use data.cell_name instead
    @property
    def cell_name(self):
        """Returns the session name"""

        if not self._cell_name:
            try:
                return self.data.cell_name
            except NoDataFound:
                return None
        else:
            return self._cell_name

    @cell_name.setter
    def cell_name(self, n):
        """sets the session name"""

        self._cell_name = n
        if not self.data.cell_name:
            self.data.cell_name = n

    def _invent_a_cell_name(self, filename=None, override=False):
        if filename is None:
            self.cell_name = "nameless"
            return
        if self.cell_name and not override:
            return
        if isinstance(filename, (list, tuple)):
            names = [Path(n).with_suffix("").name for n in filename]
            names = [
                n.replace(" ", "_").replace("-", "_").replace(".", "_") for n in names
            ]
            names = list(set(names))
            if len(names) == 1:
                self.cell_name = names[0]
            else:
                self.cell_name = "-".join(names)
        else:
            self.cell_name = Path(filename).with_suffix("").name

    @property
    def mass(self):
        """Returns the mass"""
        return self.data.mass

    @mass.setter
    def mass(self, m):
        self.data.mass = self._dump_cellpy_unit(m, "mass")

    @property
    def active_mass(self):
        """Returns the active mass (same as mass)"""
        return self.data.mass

    @active_mass.setter
    def active_mass(self, m):
        self.data.mass = self._dump_cellpy_unit(m, "mass")

    @property
    def tot_mass(self):
        """Returns the total mass"""
        return self.data.tot_mass

    @tot_mass.setter
    def tot_mass(self, m):
        self.data.tot_mass = self._dump_cellpy_unit(m, "mass")

    @property
    def active_electrode_area(self):
        """Returns the area"""
        return self.data.active_electrode_area

    @active_electrode_area.setter
    def active_electrode_area(self, a):
        self.data.active_electrode_area = self._dump_cellpy_unit(a, "area")

    @property
    def nom_cap(self):
        """Returns the nominal capacity"""
        return self.data.nom_cap

    @nom_cap.setter
    def nom_cap(self, c):
        self.data.nom_cap = self._dump_cellpy_unit(c, "nominal_capacity")

    @property
    def nominal_capacity(self):
        """Returns the nominal capacity"""
        return self.data.nom_cap

    @nominal_capacity.setter
    def nominal_capacity(self, c):
        self.data.nom_cap = self._dump_cellpy_unit(c, "nominal_capacity")

    # TODO: move this outside of the class
    def _dump_cellpy_unit(self, value, parameter):
        """Parse for unit, update cellpy_units class, and return magnitude."""
        if isinstance(value, numbers.Number):
            return value
        logging.critical(f"Parsing {parameter} ({value})")

        try:
            c = ds.Q(value)
            c_unit = c.units
            self.cellpy_units[parameter] = f"{c_unit}"
            logging.critical(f"Updated your cellpy_units['{parameter}'] to '{c_unit}'")
            c = c.magnitude
        except ValueError:
            logging.debug(f"Could not parse {value}")
            return
        return c

    @property
    def nom_cap_specifics(self):
        """Returns the nominal capacity specific"""
        return self.data.meta_common.nom_cap_specifics

    @nom_cap_specifics.setter
    def nom_cap_specifics(self, c):
        if c.lower() == "areal":
            self.cellpy_units.nominal_capacity = (
                f"{self.cellpy_units.charge}/{self.cellpy_units.specific_areal}"
            )
        elif c.lower() == "gravimetric":
            self.cellpy_units.nominal_capacity = (
                f"{self.cellpy_units.charge}/{self.cellpy_units.specific_gravimetric}"
            )
        elif c.lower() == "volumetric":
            self.cellpy_units.nominal_capacity = (
                f"{self.cellpy_units.charge}/{self.cellpy_units.specific_volumetric}"
            )
        elif c.lower() == "absolute":
            self.cellpy_units.nominal_capacity = f"{self.cellpy_units.charge}"
        else:
            logging.warning(f"Unknown nominal capacity specific: {c}")
            return
        self.data.meta_common.nom_cap_specifics = c.lower()

    @property
    def raw_units(self):
        """Returns the raw_units dictionary"""

        return self.data.raw_units

    @property
    def data(self):
        """Returns the DataSet instance"""

        # Data ownership lives in the cellpy-core seam (self.core._data).
        if not self.core._data:
            logging.debug(
                "NoDataFound - might consider defaulting to create one in the future"
            )
            raise NoDataFound
        else:
            return self.core._data

    @data.setter
    def data(self, new_cell):
        """sets the DataSet instance"""

        self.core._data = new_cell

    @property
    def empty(self):
        """Gives True if the CellpyCell object is empty (or non-functional)"""

        return not self._validate_cell()

    # TODO: consider moving splitting etc outside of CellpyCell
    # ------------------- SPLITTING AND DROPPING -------------------
    @classmethod
    def vacant(cls, cell=None):
        """Create a CellpyCell instance.

        Args:
            cell (CellpyCell instance): the attributes from the data will be
                copied to the new CellpyCell instance.

        Returns:
            CellpyCell instance.

        """

        new_cell = cls(initialize=True)
        if cell is not None:
            new_cell.data.meta_common = cell.data.meta_common
            new_cell.data.meta_test_dependent = cell.data.meta_test_dependent
            new_cell.data._extra_tests = dict(cell.data._extra_tests)
            new_cell.data._active_test_id = cell.data._active_test_id
            new_cell.data._provenance = dict(cell.data._provenance)

            new_cell.data.raw_data_files = cell.data.raw_data_files
            new_cell.data.raw_data_files_length = cell.data.raw_data_files_length
            new_cell.data.raw_units = cell.data.raw_units
            new_cell.data.raw_limits = cell.data.raw_limits

            new_cell.data.loaded_from = cell.data.loaded_from
            new_cell.data._raw_id = cell.data.raw_id
        return new_cell

    # The split/drop-cycle helpers live in cellpy.readers.slicing (issue
    # #519); thin delegates below keep the public API and subclass dispatch.
    def mod_raw_split_cycle(self, data_points: List) -> None:
        """Split cycle(s) into several cycles. See :func:`cellpy.readers.slicing.mod_raw_split_cycle`."""
        return slicing.mod_raw_split_cycle(self, data_points)

    def _mod_raw_split_cycle(self, data_point: int) -> None:
        """See :func:`cellpy.readers.slicing._mod_raw_split_cycle`."""
        return slicing._mod_raw_split_cycle(self, data_point)

    def split(self, cycle=None):
        """Split experiment into two sub-experiments. See :func:`cellpy.readers.slicing.split`."""
        return slicing.split(self, cycle=cycle)

    def drop_from(self, cycle=None):
        """Select first part of experiment up to cycle. See :func:`cellpy.readers.slicing.drop_from`."""
        return slicing.drop_from(self, cycle=cycle)

    def drop_to(self, cycle=None):
        """Select last part of experiment from cycle. See :func:`cellpy.readers.slicing.drop_to`."""
        return slicing.drop_to(self, cycle=cycle)

    def from_cycle(self, cycle: int) -> "CellpyCell":
        """Select experiment from cycle number. See :func:`cellpy.readers.slicing.from_cycle`."""
        return slicing.from_cycle(self, cycle)

    def to_cycle(self, cycle: int) -> "CellpyCell":
        """Select experiment to cycle number. See :func:`cellpy.readers.slicing.to_cycle`."""
        return slicing.to_cycle(self, cycle)

    def drop_edges(self, start: int, end: int) -> "CellpyCell":
        """Select middle part of experiment. See :func:`cellpy.readers.slicing.drop_edges`."""
        return slicing.drop_edges(self, start, end)

    def split_many(self, base_cycles: Optional[Union[int, List[int]]] = None) -> List["CellpyCell"]:
        """Split experiment into several sub-experiments. See :func:`cellpy.readers.slicing.split_many`."""
        return slicing.split_many(self, base_cycles=base_cycles)

    def with_cycles(self, cycles: Union[int, List[int]]) -> "CellpyCell":
        """Select a subset of cycles. See :func:`cellpy.readers.slicing.with_cycles`."""
        return slicing.with_cycles(self, cycles)

    # ------------------- SPLITTING AND DROPPING FINISHED -----------

    # TODO: consider moving splitting etc outside of CellpyCell
    # ----------------- Instrument handling -------------------------
    def __register_external_readers(self):
        logging.debug(
            "Not implemented yet. Should allow registering readers "
            "for example installed as plug-ins."
        )
        self.__external_readers = dict()
        return

    def register_instrument_readers(self):
        """Register instrument readers.

        Builds the default factory only when none is set — an injected
        ``instrument_factory`` (#520, DI) is kept as-is. Set
        ``self.instrument_factory = None`` first to force a rebuild.
        """
        if self.instrument_factory is None:
            self.instrument_factory = ds.generate_default_factory()
        # instruments = find_all_instruments()
        # for instrument_id, instrument in instruments.items():
        #     self.instrument_factory.register_builder(instrument_id, instrument)

    def _set_raw_units(self):
        return merge_raw_units(self.loader_class.get_raw_units())

    @staticmethod
    def _route_loader_meta_to_boxes(data):
        """Route loader-set orphan attributes into the meta boxes (issue #508).

        Loaders historically parked parsed metadata as plain attributes on
        ``Data`` (never serialized, invisible to ``Data.tests``). Copy them
        into ``meta_test_dependent`` so they persist and surface in the
        derived ``TestMeta`` record. The orphan attributes stay set for
        backward compatibility. ``test_name`` has no home in the metadata
        model and remains orphan-only.
        """
        box = data.meta_test_dependent
        for attr in ("test_ID", "channel_index", "creator", "schedule_file_name"):
            # normalize absent-ish values: raw-file backends differ by
            # platform (Windows ODBC yields '' where Linux mdbtools yields
            # NaN) - both mean "not provided"
            value = test_meta._unwrap(getattr(data, attr, None))
            if isinstance(value, str) and not value.strip():
                value = None
            if value is not None:
                setattr(box, attr, value)

    def _set_instrument(self, instrument, **kwargs):
        self.loader_class = self.instrument_factory.create(instrument, **kwargs)
        self.raw_limits = self.loader_class.get_raw_limits()
        # ----- create the loader ------------------------
        self.loader = self.loader_class.loader_executor

    def set_instrument(
        self,
        instrument=None,
        model=None,
        instrument_file=None,
        unit_test=False,
        **kwargs,
    ):
        """Set the instrument (i.e. tell cellpy the file-type you use).

        Three different modes of setting instruments are currently supported. You can
        provide the already supported instrument names (see the documentation, e.g. "arbin_res").
        You can use the "custom" loader by providing the path to a yaml-file
        describing the file format. This can be done either by setting instrument to
        "instrument_name::instrument_definition_file_name", or by setting instrument to "custom" and
        provide the definition file name through the instrument_file keyword argument. A last option
        exists where you provide the yaml-file name directly to the instrument parameter. Cellpy
        will then look into your local instrument folder and search for the yaml-file. Some
        instrument types also supports a model key-word.

        Args:
            instrument: (str) in ["arbin_res", "maccor_txt",...]. If
                instrument ends with ".yml" a local instrument file will be used. For example,
                if instrument is "my_instrument.yml", cellpy will look into the local
                instruments folders for a file called "my_instrument.yml" and then
                use LocalTxtLoader to load after registering the instrument. If the instrument
                name contains a '::' separator, the part after the separator will be interpreted
                as 'instrument_file'.
            model: (str) optionally specify if the instrument loader supports handling several models
                (some instruments allow for exporting data in slightly different formats depending on
                the choices made during the export or the model of the instrument, e.g. different number of
                header lines, different encoding).
            instrument_file: (path) instrument definition file,
            unit_test: (bool) set to True if you want to print the settings instead of setting them.
            kwargs (dict): key-word arguments sent to the initializer of the
                loader class

        Note:
            If you are using a local instrument loader, you will have to register it first to the loader factory.

            >>> c = CellpyCell()  # this will automatically register the already implemented loaders
            >>> c.instrument_factory.register_builder(instrument_id, (module_name, path_to_instrument_loader_file))

            It is highly recommended using the module_name as the instrument_id.

        """

        # constants:
        custom_instrument_splitter = "::"
        model_id = "model="
        # consume keyword arguments:
        _override_local_instrument_path = kwargs.pop(
            "_override_local_instrument_path", False
        )

        # parse input (need instrument, instrument_file and model)

        # None, None, [-]
        if instrument is None and instrument_file is None:
            instrument = self.tester

        # "xxx::yyy", None, [-] -> "xxx", "yyy", [-] or "xxx", None, "yyy"
        if not instrument_file:
            instrument, instrument_file_or_model = self._parse_instrument_str(
                instrument, custom_instrument_splitter
            )
            if instrument_file_or_model:
                if instrument_file_or_model.startswith(model_id):
                    model = instrument_file_or_model[len(model_id) :]
                else:
                    instrument_file = instrument_file_or_model

        # "xxx::yyy", "zzz", None -> "xxx", "zzz", "yyy"
        if instrument_file and not model:
            instrument, model = self._parse_instrument_str(
                instrument, custom_instrument_splitter
            )

        if instrument and instrument.endswith(".yml"):
            instrument_file = instrument
            instrument = "local_instrument"
            config.instruments.custom_instrument_definitions_file = instrument_file
            if _override_local_instrument_path:
                instrument_file = Path(instrument_file)
            else:
                instrument_file = Path(config.paths.instrumentdir) / instrument_file

            if not instrument_file.is_file():
                raise FileNotFoundError(f"Could not locate {instrument_file}")

        if model is not None and model.startswith(model_id):
            model = model[len(model_id) :]

        if unit_test:
            print(f"{instrument=}")
            print(f"{instrument_file=}")
            print(f"{model=}")
            print(f"{kwargs=}")
            return instrument, instrument_file, model, kwargs

        self._set_instrument(
            instrument, instrument_file=instrument_file, model=model, **kwargs
        )

    @staticmethod
    def _parse_instrument_str(instrument, custom_instrument_splitter="::"):
        if not instrument:
            return None, None
        try:
            _instrument = instrument.split(custom_instrument_splitter)
            if len(_instrument) < 2:
                return instrument, None
            else:
                return _instrument
        except AttributeError:
            return str(instrument), None

    # ----------------- Instrument handling finished -----------------

    @property
    def cycle_mode(self):
        """The active test's ``cycle_mode`` (scalar).

        For per-test access on multi-test objects, use
        ``self.data.get_cycle_mode(test_id)`` / ``set_cycle_mode`` and the
        ``self.data.tests`` collection (issue #506).
        """
        try:
            data = self.data
            m = data.meta_test_dependent.cycle_mode
            # cellpy saves this as a list (ready for v2.0),
            # but we want to return a scalar for the moment
            # Temporary fix to make sure that cycle_mode is a scalar:
            if isinstance(m, (tuple, list)):
                return m[0]
            return m
        except NoDataFound:
            return self._cycle_mode

    @cycle_mode.setter
    def cycle_mode(self, cycle_mode):
        # TODO: v2.0 edit this from scalar to list
        logging.debug(f"-> cycle_mode: {cycle_mode}")
        try:
            data = self.data
            data.meta_test_dependent.cycle_mode = cycle_mode
            self._cycle_mode = cycle_mode
        except NoDataFound:
            self._cycle_mode = cycle_mode

    def _guard_mixed_cycle_modes(self):
        """Refuse engine compute when tests present carry different cycle_modes.

        The engine applies one global charge/discharge convention; running it
        on a merged object mixing e.g. anode and cathode tests would silently
        apply the wrong convention to some tests (issue #506; per-test engine
        polarity is future work, #507).
        """
        try:
            modes = test_meta.cycle_modes_in_data(self.data)
        except NoDataFound:
            return
        if len(modes) > 1:
            raise MixedCycleModesError(
                f"tests in this object carry different cycle_modes {sorted(modes)} "
                f"(test_ids: {self.data.tests.test_ids}); the engine applies one "
                "global convention, so computing steps/summary would be wrong for "
                "some tests. Per-test engine polarity is tracked in #507/#510."
            )

    # TODO: this probably does not need to be here
    def set_raw_datadir(self, directory=None):
        """Set the directory containing .res-files.

        Used for setting directory for looking for res-files.
        A valid directory name is required.

        Args:
            directory (str): path to res-directory

        Examples:
            >>> d = CellpyCell()
            >>> directory = "MyData/cycler-data"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            logging.info("No directory name given")
            return
        if not os.path.isdir(directory):
            logging.info(directory)
            logging.info("Directory does not exist")
            return
        self.raw_datadir = directory

    # TODO: this probably does not need to be here
    def set_cellpy_datadir(self, directory=None):
        """Set the directory containing .hdf5-files.

        Used for setting directory for looking for hdf5-files.
        A valid directory name is required.

        Args:
            directory (str): path to hdf5-directory

        Examples:
            >>> d = CellpyCell()
            >>> directory = "MyData/HDF5"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            logging.info("No directory name given")
            return
        if not os.path.isdir(directory):
            logging.info("Directory does not exist")
            return
        self.cellpy_datadir = directory

    # TODO: this could be moved outside to either utility functions or to a new class:
    # ----------------- File checking -------------------------
    def check_file_ids(self, rawfiles, cellpyfile, detailed=False):
        """Check the stats for the files (raw-data and cellpy hdf5).

        This method checks if the hdf5 file and the res-files have the same
        timestamps etc. to find out if we need to bother to load .res -files.

        if detailed is set to True, the method returns dict
        containing True or False for each individual raw-file. If not, it returns
        False if the raw files are newer than the cellpy hdf5-file (i.e. update is needed), else True.

        Args:
            cellpyfile (str): filename of the cellpy hdf5-file.
            rawfiles (list of str): name(s) of raw-data file(s).
            detailed (bool): return a dict containing True or False for each individual raw-file.

        Returns:
            Bool or dict

        """

        txt = f"Checking file ids - using '{self.filestatuschecker}'"
        logging.info(txt)

        ids_cellpy_file = self._check_cellpy_file(cellpyfile)

        logging.debug(f"cellpyfile ids: {ids_cellpy_file}")

        if not ids_cellpy_file:
            # logging.debug("hdf5 file does not exist - needs updating")
            return False

        ids_raw = self._check_raw(rawfiles)

        if detailed:
            similar = self._parse_ids(ids_raw, ids_cellpy_file)
            return similar

        else:
            similar = self._compare_ids(ids_raw, ids_cellpy_file)
            if not similar:
                # logging.debug("hdf5 file needs updating")
                return False
            else:
                # logging.debug("hdf5 file is updated")
                return True

    def _check_raw(self, file_names, abort_on_missing=False):
        """Get the file-ids for the res_files."""

        strip_file_names = True
        check_on = self.filestatuschecker
        if not self._is_listtype(file_names):
            file_names = [file_names]

        ids = dict()
        for f in file_names:
            logging.debug(f"checking raw file {f}")
            fid = ds.FileID(f)
            # logging.debug(fid)
            if fid.name is None:
                warnings.warn(f"file does not exist: {f}")
                if abort_on_missing:
                    sys.exit(-1)
            else:
                if strip_file_names:
                    name = f.name
                else:
                    name = f
                if check_on == "size":
                    ids[name] = int(fid.size)
                elif check_on == "modified":
                    ids[name] = int(fid.last_modified)
                else:
                    ids[name] = int(fid.last_modified)
        return ids

    def _check_HDFStore_available(self):
        try:
            _ = externals.pandas.HDFStore
        except Exception as e:
            print(f"Could not use HDFStore ({e})")
            return False
        return True

    def _check_cellpy_file(self, filename: "OtherPath"):  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        """Get the file-ids for the cellpy_file."""

        if not isinstance(filename, internals.OtherPath):
            logging.debug("filename must be an OtherPath object")
            filename = internals.OtherPath(filename)

        use_full_filename_path = False
        check_on = self.filestatuschecker
        logging.debug("checking cellpy-file")
        logging.debug(filename)
        if not filename.is_file():
            logging.debug("cellpy-file does not exist")
            return None

        fid_result = cellpy_file_fids.read_fid_table(filename)
        if fid_result is None:
            return None

        raw_data_files, _raw_data_files_length = fid_result
        txt = "contains %i res-files" % (len(raw_data_files))
        logging.debug(txt)
        ids = dict()
        for fid in raw_data_files:
            full_name = fid.full_name
            name = fid.name
            size = fid.size
            mod = fid.last_modified
            logging.debug(f"fileID information for: {full_name}")
            logging.debug(f"   modified: {mod}")
            logging.debug(f"   size: {size}")

            if use_full_filename_path:
                name = full_name

            if check_on == "size":
                ids[name] = int(fid.size)
            elif check_on == "modified":
                ids[name] = int(fid.last_modified)
            else:
                ids[name] = int(fid.last_modified)
        return ids

    @staticmethod
    def _compare_ids(ids_raw, ids_cellpy_file):
        similar = True
        l_res = len(ids_raw)
        l_cellpy = len(ids_cellpy_file)
        if l_res == l_cellpy and l_cellpy > 0:
            for name, value in list(ids_raw.items()):
                try:
                    c_value = ids_cellpy_file[name]
                except KeyError:
                    logging.debug("KeyError when comparing raw and cellpy file.")
                    logging.debug(
                        "Could be due to upper case vs. lower case confusion."
                    )
                    similar = False
                else:
                    if c_value != value:
                        similar = False
        else:
            similar = False

        return similar

    @staticmethod
    def _parse_ids(ids_raw, ids_cellpy_file):
        similar = dict()
        for name in ids_raw:
            v_cellpy = ids_cellpy_file.get(name, None)
            v_raw = ids_raw[name]
            similar[name] = False
            if v_raw is not None:
                if v_raw == v_cellpy:
                    similar[name] = True
        return similar

    # ----------------- File checking end --------------------

    # TODO: v2.0 - remove this
    def loadcell(
        self,
        raw_files,
        cellpy_file=None,
        mass=None,
        summary_on_raw=True,
        summary_on_cellpy_file=True,
        find_ir=True,
        find_end_voltage=True,
        force_raw=False,
        use_cellpy_stat_file=None,
        cell_type=None,
        loading=None,
        area=None,
        estimate_area=True,
        selector=None,
        **kwargs,
    ):
        """Loads data for given cells (soon to be deprecated).

        Args:
            raw_files (list): name of res-files
            cellpy_file (path): name of cellpy-file
            mass (float or str): mass of electrode or active material in cellpy_units
                (default mg). Pass a string with unit (e.g. "1.14 mg") to override
                cellpy_units.
            summary_on_raw (bool): calculate summary if loading from raw
            summary_on_cellpy_file (bool): calculate summary if loading from cellpy-file.
            find_ir (bool): summarize ir
            find_end_voltage (bool): summarize end voltage
            force_raw (bool): only use raw-files
            use_cellpy_stat_file (bool): use stat file if creating summary
                from raw
            cell_type (str): set the data type (e.g. "anode"). If not, the default from
               the config file is used.
            loading (float or str): loading in units [mass] / [area] (cellpy_units),
                used to calculate area if area not given.
            area (float or str): area of active electrode in cellpy_units (default cm**2).
                Pass a string with unit (e.g. "2.12 cm**2") to override cellpy_units.
            estimate_area (bool): calculate area from loading if given (defaults to True).
            selector (dict): passed to load.
            **kwargs: passed to from_raw

        Examples:

            >>> srnos = my_dbreader.select_batch("testing_new_solvent")
            >>> cell_datas = []
            >>> for srno in srnos:
            >>> ... my_run_name = my_dbreader.get_cell_name(srno)
            >>> ... mass = my_dbreader.get_mass(srno)
            >>> ... rawfiles, cellpyfiles = \
            >>> ...     filefinder.search_for_files(my_run_name)
            >>> ... cell_data = cellreader.CellpyCell()
            >>> ... cell_data.loadcell(raw_files=rawfiles,
            >>> ...                    cellpy_file=cellpyfiles)
            >>> ... cell_data.set_mass(mass)
            >>> ... cell_data.make_summary() # etc. etc.
            >>> ... cell_datas.append(cell_data)
            >>>

        Warning:
            This method will soon be deprecated. Use ``cellpy.get`` instead.

        """
        # This is a part of a dramatic API change. It will not be possible to
        # load more than one set of datasets (i.e. one single cellpy-file or
        # several raw-files that will be automatically merged)

        # TODO @jepe Make setting or prm so that it is possible to update only new data
        # TODO @jepe Allow passing handle to progress-bar or update a global progressbar

        warnings.warn(
            DeprecationWarning("loadcell is deprecated. Use cellpy.get instead.")
        )
        logging.debug("Started cellpy.cellreader.loadcell ")

        if cellpy_file is None:
            similar = False
        elif force_raw:
            similar = False
        else:
            similar = self.check_file_ids(raw_files, cellpy_file)
            logging.debug("checked if the files were similar")
        logging.debug(f"similar: {similar}")

        if similar:
            logging.debug(f"loading cellpy-file: {cellpy_file}")
            self.load(cellpy_file, selector=selector)

        else:
            logging.debug("cellpy file(s) needs updating - loading raw")
            logging.info("Loading raw-file")
            logging.debug(raw_files)

            self.from_raw(raw_files, **kwargs)

        logging.debug("loaded files")

        if not self._validate_cell():
            logging.warning("Empty run!")
            return self

        logging.debug("setting cell_type")
        if cell_type is not None:
            self.cycle_mode = cell_type.lower()
            logging.debug(f"setting cycle mode: {cell_type}")

        logging.debug("setting mass")
        if mass is not None:
            self.set_mass(mass)

        logging.debug("setting nom_cap")
        nom_cap = kwargs.pop("nom_cap", None)
        if nom_cap is not None:
            self.set_nom_cap(nom_cap)

        logging.debug("calculating area")
        if area is not None:
            logging.debug(f"got area: {area}")
            self.data.meta_common.active_electrode_area = area
        elif loading and estimate_area:
            logging.debug(f"got loading: {logging}")
            area = self.data.mass / loading
            logging.debug(
                f"calculating area from loading ({loading}) and mass ({self.data.mass}): {area}"
            )
            self.data.meta_common.active_electrode_area = area
        else:
            logging.debug("using default area")

        if similar:
            if summary_on_cellpy_file:
                self.make_summary(
                    find_ir=find_ir,
                    find_end_voltage=find_end_voltage,
                    use_cellpy_stat_file=use_cellpy_stat_file,
                )

        else:
            if summary_on_raw:
                self.make_summary(
                    find_ir=find_ir,
                    find_end_voltage=find_end_voltage,
                    use_cellpy_stat_file=use_cellpy_stat_file,
                )

        return self

    # TODO: this could be moved outside to either utility functions or to a new class:
    def from_raw(
        self,
        file_names=None,
        pre_processor_hook=None,
        post_processor_hook=None,
        is_a_file=True,
        refuse_copying=False,
        **kwargs,
    ):
        """Load a raw data-file.

        Args:
            file_names (list of raw-file names): uses CellpyCell.file_names if
                None. If the list contains more than one file name, then the
                runs will be merged together. Remark! the order of the files in
                the list is important.
            pre_processor_hook (callable): function that will be applied to the data within the loader.
            post_processor_hook (callable): function that will be applied to the
                cellpy.Dataset object after initial loading.
            is_a_file (bool): set this to False if it is a not a file-like object.
            refuse_copying (bool): if set to True, the raw-file will not be copied before loading.

        Transferred Parameters:
            recalc (bool): used by merging. Set to false if you don't want cellpy to automatically shift cycle number
                and time (e.g. add last cycle number from previous file to the cycle numbers
                in the next file).
            bad_steps (list of tuples): used by ``ArbinLoader``. (c, s) tuples of steps s (in cycle c)
                to skip loading.
            data_points (tuple of ints): used by ``ArbinLoader``. Load only data from data_point[0] to
                data_point[1] (use None for infinite). NOT IMPLEMENTED YET.

        """
        if file_names:
            self.file_names = file_names

        if not isinstance(self.file_names, (list, tuple)):
            self.file_names = [file_names]

        # file_type = self.tester
        instrument = kwargs.pop("instrument", None)
        instrument_file = kwargs.pop("instrument_file", None)
        if instrument_file:
            logging.info("Setting custom instrument")
            logging.info(f"-> {instrument}")
            logging.info(f"-> instrument file: {instrument_file}")
            self.set_instrument(instrument="custom", instrument_file=instrument_file)
        elif instrument:
            logging.info("Setting custom instrument")
            logging.info(f"-> {instrument}")
            self.set_instrument(instrument)

        raw_file_loader = self.loader
        try:
            self.tester = self.loader_class.instrument_name
        except AttributeError:
            logging.debug("could not set instrument name")

        max_raw_files_to_merge = config.reader.max_raw_files_to_merge
        if len(self.file_names) > max_raw_files_to_merge:
            logging.debug("ERROR? Too many files to merge")
            raise ValueError(
                f"Too many files to merge (max allowed is {max_raw_files_to_merge})"
                f" - could be a bug in the code (please report if you know you have"
                f" less than {max_raw_files_to_merge} files)"
            )

        logging.debug("start iterating through file(s)")
        recalc = kwargs.pop("recalc", True)
        data = None
        for file_name in self.file_names:
            logging.debug("loading raw file:")
            logging.debug(f"{file_name}")
            if is_a_file:
                file_name = internals.OtherPath(file_name)
                if not file_name.is_file():
                    raise NoDataFound(f"Could not find the file {file_name}")

            new_data = raw_file_loader(
                file_name,
                pre_processor_hook=pre_processor_hook,
                refuse_copying=refuse_copying,
                **kwargs,
            )  # list of tests

            if new_data is None:
                raise IOError(
                    f"Could not read {file_name}. Loader returned None. Aborting."
                )
            if not new_data.has_data:
                raise IOError(f"Could not read any data from {file_name}. Aborting.")

            if post_processor_hook is not None:
                # REMARK! this needs to be changed if we stop returning the datasets in a list
                # (i.e. if we chose to remove option for having more than one test pr instance)
                new_data = post_processor_hook(new_data)

            if data is None:
                # retrieving the first cell data (e.g. first file)
                logging.debug("getting data from first file")
                data = new_data
            else:
                # appending cell data file to existing
                logging.debug("continuing reading files...")
                data = self._append(data, new_data, recalc=recalc)

                # retrieving file info in a for-loop in case of multiple files
                # Remark!
                #    - the raw_data_files attribute is a list
                #    - the raw_data_files_length attribute is a list

                logging.debug("added the data set - merging file info")

                data.raw_data_files.extend(new_data.raw_data_files)
                data.raw_data_files_length.extend(new_data.raw_data_files_length)

        logging.debug("finished loading the raw-files")

        if not config.reader.sorted_data:
            logging.debug("sorting data")
            data = self._sort_data(data)

        data.raw_units = self._set_raw_units()

        # issue #508 (V2-05/06): finalize per-test metadata on the loaded object.
        # - route loader-parsed orphan attributes into the meta boxes
        # - stamp the compact test_id grouping key onto raw (0 for a single,
        #   unmerged test; tester-assigned ids remain as provenance in
        #   meta_test_dependent.test_ID) - must run after the loader's own
        #   intra-file merging (e.g. arbin_res) and the continuation folds
        # - record load provenance for the derived TestMeta record
        self._route_loader_meta_to_boxes(data)
        data.raw[self.headers_normal.test_id_txt] = data.active_test_id
        data._provenance = {
            "uuid": str(uuid.uuid4()),
            "source_kind": "db" if self.tester in DB_READER_INSTRUMENTS else "file",
            "source_type": self.tester,
            "source_uri": str(data.loaded_from),
            "raw_file_names": [f.name for f in data.raw_data_files],
            "loaded_datetime": datetime.datetime.now().isoformat(),
        }

        self.data = data
        if self.native_schema:
            # #511 opt-in: translate once at the I/O boundary; everything
            # downstream stays in native column names.
            from cellpy.readers.cellpy_file import translate as cellpy_file_translate

            cellpy_file_translate.to_native(self.data)
        self._invent_a_cell_name(self.file_names)  # TODO (v1.0.0): fix me
        self.last_uploaded_from = "raw"
        self.last_uploaded_at = datetime.datetime.now()
        return self

    def _validate_cell(self, level=0):
        logging.debug("validating test")
        # simple validation for finding empty datasets - should be expanded to
        # find not-complete datasets, datasets with missing parameters etc
        v = True
        if level == 0:
            try:
                _ = self.data
                return True
            except NoDataFound:
                return False
        return v

    def _partial_load(self, **kwargs):
        """Load only a selected part of the cellpy file."""
        raise NotImplementedError

    def _link(self, **kwargs):
        """Create a link to a cellpy file.

        If the file is very big, it is sometimes better to work with the data
        out of memory (i.e. on disk). A CellpyCell object with a linked file
        will in most cases work as a normal object. However, some methods
        might be disabled. And it will be slower.

        Note:
            2020.02.08 - maybe this functionality is not needed and can be replaced
                by using dask or similar?
        """
        raise NotImplementedError

    # TODO: this could be moved outside to either utility functions or to a new class:
    # -------------------- cellpy file handling -------------------------
    def load(
        self,
        cellpy_file,
        parent_level=None,
        return_cls=True,
        accept_old=True,
        selector=None,
        **kwargs,
    ):
        """Loads a cellpy file.

        Args:
            cellpy_file (OtherPath, str): Full path to the cellpy file.
            parent_level (str, optional): Parent level. Warning! Deprecating this soon!
            return_cls (bool): Return the class.
            accept_old (bool): Accept loading old cellpy-file versions.
                Instead of raising WrongFileVersion it only issues a warning.
            selector (dict): Experimental feature - select specific ranges of data.

        Returns:
            cellpy.CellpyCell class if return_cls is True
        """

        # This is what happens:
        # 1) (this is not implemented yet, using only hdf5) chose what file format to load from
        # 2) in reader (currently only _load_hdf5): check version and select sub-reader.
        # 3) in sub-reader: read data
        # 4) in this method: add data to CellpyCell object (i.e. self)
        for kwarg in kwargs:
            logging.debug(f"received (still) un-supported keyword argument {kwarg=}")

        logging.debug("loading cellpy-file:")
        logging.debug(cellpy_file)
        logging.debug(f"{type(cellpy_file)=}")
        cellpy_file = internals.OtherPath(cellpy_file)
        logging.debug(f"using pickle protocol {PICKLE_PROTOCOL}")
        result = cellpy_file_read.load(
            cellpy_file,
            accept_old=accept_old,
            selector=selector,
            parent_level=parent_level,
        )
        data = result.data
        limits = result
        logging.debug("cellpy-file loaded")

        if data:
            self.data = data
            if self.native_schema:
                # #511 opt-in: cellpy-file readers emit legacy names; translate
                # once at the I/O boundary.
                from cellpy.readers.cellpy_file import (
                    translate as cellpy_file_translate,
                )

                cellpy_file_translate.to_native(self.data)
            self.limit_loaded_cycles = limits.limit_loaded_cycles
            self.limit_data_points = limits.limit_data_points

        else:
            # raise LoadError
            logging.warning("Could not load")
            logging.warning(str(cellpy_file))

        self._invent_a_cell_name(cellpy_file)
        self.last_uploaded_from = cellpy_file
        self.cellpy_file_name = cellpy_file
        self.last_uploaded_at = datetime.datetime.now()

        if return_cls:
            return self

    def save(
        self,
        filename,
        force=False,
        overwrite=None,
        extension="cellpy",
        ensure_step_table=None,
        ensure_summary_table=None,
        cellpy_file_format=None,
    ):
        """Save the data structure to cellpy-format.

        Default on-disk format is **v9** (zip-of-parquet + ``meta.json``,
        ``.cellpy``). Pass ``cellpy_file_format="hdf5"`` / ``"v8"`` or a
        ``.h5`` / ``.hdf5`` path to write the legacy HDF5 layout.

        Args:
            filename: (str or pathlib.Path) the name you want to give the file
            force: (bool) save a file even if the summary is not made yet
                (not recommended)
            overwrite: (bool) save the new version of the file even if old one
                exists.
            extension: (str) filename extension when ``filename`` has no suffix
                (default ``cellpy``).
            ensure_step_table: (bool) make step-table if missing.
            ensure_summary_table: (bool) make summary-table if missing.
            cellpy_file_format: (str | None) ``"v9"`` / ``"cellpy"`` (default),
                or ``"hdf5"`` / ``"v8"`` for the legacy HDF5 writer. When
                omitted, inferred from the path suffix (``.h5``/``.hdf5`` →
                hdf5, otherwise v9).

        Returns:
            None

        """
        from cellpy.readers.cellpy_file import v9 as cellpy_file_v9

        logging.debug(f"Trying to save cellpy-file to {filename}")
        logging.info(f" -> {filename}")

        # some checks to find out what you want
        if overwrite is None:
            overwrite = self.overwrite_able

        if ensure_step_table is None:
            ensure_step_table = self.ensure_step_table

        if ensure_summary_table is None:
            ensure_summary_table = self.ensure_summary_table

        my_data = self.data
        summary_made = my_data.has_summary
        if not summary_made and not force and not ensure_summary_table:
            logging.info("File not saved!")
            logging.info("You should not save datasets without making a summary first!")
            logging.info("If you really want to do it, use save with force=True")
            return

        step_table_made = my_data.has_steps
        if not step_table_made and not force and not ensure_step_table:
            logging.info(
                "File not saved!"
                "You should not save datasets without making a step-table first!"
            )
            logging.info("If you really want to do it, use save with force=True")
            return

        outfile_all = internals.OtherPath(filename)
        if not outfile_all.suffix:
            logging.debug("No suffix given - adding one")
            outfile_all = outfile_all.with_suffix(f".{extension}")

        fmt = (cellpy_file_format or "").lower().strip()
        suffix = outfile_all.suffix.lower()
        if not fmt:
            if suffix in {".h5", ".hdf5"}:
                fmt = "hdf5"
            else:
                fmt = "v9"
        if fmt in {"h5", "hdf", "hdf5", "v8"}:
            fmt = "hdf5"
        elif fmt in {"v9", "cellpy", "zip"}:
            fmt = "v9"
        else:
            logging.warning(
                f"Unknown cellpy_file_format={cellpy_file_format!r}; using v9"
            )
            fmt = "v9"
        if fmt == "hdf5" and self.native_schema:
            raise ValueError(
                "the legacy HDF5 (v8) writer expects legacy column names; "
                "a native-schema cell (#511 opt-in) must save v9 (.cellpy)"
            )

        if outfile_all.is_file():
            logging.debug("Outfile exists")
            if overwrite:
                logging.debug("overwrite = True")
                try:
                    os.remove(outfile_all)
                except PermissionError as e:
                    logging.critical("Could not over write old file")
                    logging.info(e)
                    return
            else:
                logging.critical("File exists - did not save")
                logging.info(outfile_all)
                return

        if ensure_step_table:
            logging.debug("ensure_step_table is on")
            if not my_data.has_steps:
                logging.debug("save: creating step table")
                self.make_step_table()

        if ensure_summary_table:
            logging.debug("ensure_summary_table is on")
            if not my_data.has_summary:
                logging.debug("save: creating summary table")
                self.make_summary()

        logging.debug(f"trying to save to file: {outfile_all} (format={fmt})")
        if fmt == "hdf5":
            cellpy_file_write.save(my_data, outfile_all)
            logging.debug(" all -> hdf5 OK")
        else:
            units = None
            try:
                units = self.cellpy_units.to_frame()["value"].to_dict()
            except Exception:
                logging.debug(
                    "could not serialize cellpy_units for v9 meta", exc_info=True
                )
            cellpy_file_v9.save(my_data, outfile_all, cellpy_units=units)
            logging.debug(" all -> v9 .cellpy OK")

    # TODO @jepe: move this to its own module (e.g. as a cellpy-exporters?):
    @staticmethod
    def _convert2fid_table(cell):
        return cellpy_file_fids.convert2fid_table(cell)

    # TODO @jepe: move this to its own module (e.g. as a cellpy-loader in instruments?):
    @staticmethod
    def _convert2fid_list(tbl):
        return cellpy_file_fids.convert2fid_list(tbl)

    # -------------------- cellpy file handling end ----------------------

    def merge(self, cells, mode="campaign", renumber_cycles=True, **kwargs):
        """Merge other cells/datasets into this one.

        Two distinct semantics (issue #507, epic #402 V2-03/V2-07):

        - ``mode="campaign"`` (default): the sources are *different tests*
          (possibly different cells or programs). Each source keeps its
          identity via a distinct compact ``test_id`` stamped on the raw
          frame (this **overwrites** tester-assigned ids such as Arbin's
          ``Test_ID`` — those remain as provenance in
          ``meta_test_dependent.test_ID``), and its metadata becomes a
          record in ``self.data.tests``. Cycle numbers are renumbered to be
          globally unique by default (see ``renumber_cycles``); data points
          are offset; ``test_time`` /
          ``date_time`` are *not* shifted (independent timelines). Sources
          are never mutated. Mixing different ``cycle_mode`` values is
          allowed here, but computing steps/summary on the merged object
          then raises ``MixedCycleModesError``.
        - ``mode="continuation"``: the sources are the *same physical test*
          resumed across files — the classic fold, numerically identical to
          ``from_raw([file1, file2])`` (cycles, data points and test time
          are renumbered into one continuous run; source metadata is
          dropped). Extra ``**kwargs`` (e.g. ``recalc``) are forwarded.

        Args:
            cells: a CellpyCell or Data instance, or a sequence of them.
            mode (str): "campaign" (default) or "continuation".
            renumber_cycles (bool): campaign mode only. If True (default),
                cycle numbers are renumbered to be globally unique. If False
                (#529, needs cellpycore >= 0.2.2), sources keep their original
                cycle numbers: the identifying key becomes
                ``(test_id, cycle)`` and cycle numbers repeat across tests —
                cycle-keyed consumers (``get_cap(cycle=...)``, ``split`` /
                ``with_cycles``, exporters) then operate on the union of the
                matching cycles. Data points are always offset to stay
                globally unique.
            **kwargs: forwarded to the continuation fold.

        Returns:
            self (chainable), with ``self.data`` holding the merged object.
        """
        from cellpy.readers import merger

        if self.native_schema:
            raise NotImplementedError(
                "merge() is not supported on a native-schema cell yet "
                "(#511 opt-in scope); merge on the legacy path and load the "
                "result into a native-schema cell instead"
            )
        if cells is None:
            raise TypeError(
                "merge() requires the cells/datasets to merge into this one "
                "(a CellpyCell/Data or a sequence of them)"
            )
        if isinstance(cells, (CellpyCell, ds.Data)):
            cells = [cells]
        datas = [c.data if isinstance(c, CellpyCell) else c for c in cells]

        if mode == "continuation":
            logging.info("Merging (continuation)")
            for other in datas:
                self.data = self._append(self.data, other, **kwargs)
                for raw_data_file, file_size in zip(
                    other.raw_data_files,
                    other.raw_data_files_length,
                ):
                    self.data.raw_data_files.append(raw_data_file)
                    self.data.raw_data_files_length.append(file_size)
            return self

        if mode != "campaign":
            raise ValueError(f"unknown merge mode: {mode!r}")

        logging.info("Merging (campaign)")
        for other in datas:
            merger.campaign_fold(
                self.data, other, renumber_cycles=renumber_cycles, **kwargs
            )
        modes = test_meta.cycle_modes_in_data(self.data)
        if len(modes) > 1:
            logging.warning(
                f"merged object stores tests with different cycle_modes "
                f"{sorted(modes)}; computing steps/summary will raise "
                f"MixedCycleModesError until per-test engine polarity lands"
            )
        return self

    def _append(self, t1, t2, merge_summary=False, merge_step_table=False, recalc=True):
        logging.debug(
            f"merging two datasets\n(merge summary = {merge_summary})\n"
            f"(merge step table = {merge_step_table})"
        )
        if t1.raw.empty:
            logging.debug("OBS! the first dataset is empty")
            logging.debug(" -> merged contains only second")
            return t2

        if t2.raw.empty:
            logging.debug("OBS! the second dataset was empty")
            logging.debug(" -> merged contains only first")
            return t1

        if not isinstance(t1.loaded_from, (list, tuple)):
            t1.loaded_from = [t1.loaded_from]

        cycle_index_header = self.headers_summary.cycle_index
        data = t1
        if recalc:
            # finding diff of time
            start_time_1 = t1.meta_common.start_datetime
            start_time_2 = t2.meta_common.start_datetime

            if self.tester in ["arbin_res"]:
                diff_time = ds.xldate_as_datetime(
                    start_time_2
                ) - ds.xldate_as_datetime(start_time_1)
            else:
                diff_time = start_time_2 - start_time_1
            diff_time = diff_time.total_seconds()

            if diff_time < 0:
                logging.warning("Wow! your new dataset is older than the old!")
            logging.debug(f"diff time: {diff_time}")

            sort_key = self.headers_normal.datetime_txt  # DateTime
            logging.debug(f"sort key: {sort_key}")
            # mod data points for set 2
            data_point_header = self.headers_normal.data_point_txt
            try:
                last_data_point = max(t1.raw[data_point_header])
            except ValueError:
                logging.debug("ValueError when getting last data point for r1")
                last_data_point = 0

            t2.raw[data_point_header] = t2.raw[data_point_header] + last_data_point
            logging.debug("No error getting last data point for r2")
            # mod cycle index for set 2

            try:
                last_cycle = max(t1.raw[cycle_index_header])
            except ValueError:
                logging.debug("ValueError when getting last cycle index for r1")
                last_cycle = 0
            t2.raw[cycle_index_header] = t2.raw[cycle_index_header] + last_cycle
            # mod test time for set 2
            test_time_header = self.headers_normal.test_time_txt
            t2.raw[test_time_header] = t2.raw[test_time_header] + diff_time
        else:
            logging.debug("not doing recalc")
        # merging
        logging.debug("performing concat")
        raw = externals.pandas.concat([t1.raw, t2.raw], ignore_index=True)
        data.raw = raw
        data.loaded_from.append(t2.loaded_from)

        if merge_summary:
            # checking if we already have made a summary file of these datasets
            # (to be used if merging summaries (but not properly implemented yet))
            if t1.summary.empty or t2.summary.empty:
                summary_made = False
            else:
                summary_made = True

            try:
                _ = t1.summary[
                    cycle_index_header
                ]  # during loading arbin res files, a stats-frame is loaded into
                _ = t2.summary[
                    cycle_index_header
                ]  # the summary. This prevents merging those.
            except KeyError:
                summary_made = False
                logging.info("The summary is not complete - run make_summary()")

            if summary_made:
                # check if (self-made) summary exists.
                logging.debug("merge summaries")
                if recalc:
                    # This part of the code is seldom ran. Careful!
                    # mod cycle index for set 2
                    last_cycle = max(t1.summary[cycle_index_header])
                    t2.summary[cycle_index_header] = (
                        t2.summary[cycle_index_header] + last_cycle
                    )
                    # mod test time for set 2
                    t2.summary[test_time_header] = (
                        t2.summary[test_time_header] + diff_time
                    )
                    # to-do: mod all the cumsum stuff in the summary (best to make
                    # summary after merging) merging

                    t2.summary[data_point_header] = (
                        t2.summary[data_point_header] + last_data_point
                    )

                summary2 = externals.pandas.concat(
                    [t1.summary, t2.summary], ignore_index=True
                )

                data.summary = summary2
            else:
                logging.debug(
                    "could not merge summary tables (non-existing) -create them first!"
                )

        if merge_step_table:
            # (fixed in #507: was gated on a flag only set inside the
            # merge_summary branch, offset the wrong frame, and NameError'd
            # on last_cycle when recalc=False)
            if t1.has_steps and t2.has_steps:
                if recalc:
                    t2.steps[self.headers_step_table.cycle] = (
                        t2.steps[self.headers_step_table.cycle] + last_cycle
                    )
                steps2 = externals.pandas.concat(
                    [t1.steps, t2.steps], ignore_index=True
                )
                data.steps = steps2
            else:
                logging.debug(
                    "could not merge step tables (non-existing) -create them first!"
                )

        logging.debug(" -> merged with new dataset")
        # TODO: @jepe -  update merging for more variables
        return data

    # TODO: check if this can be moved to helpers
    def _validate_step_table(self, simple=False):
        step_index_header = self.headers_normal.step_index_txt
        logging.debug(f"-validating step table ({step_index_header=!r})")
        d = self.data.raw
        s = self.data.steps

        if not self.data.has_steps:
            return False

        no_cycles_raw = externals.numpy.amax(d[self.headers_normal.cycle_index_txt])
        headers_step_table = self.headers_step_table
        no_cycles_step_table = externals.numpy.amax(s[headers_step_table.cycle])

        if simple:
            logging.debug("  (simple)")
            if no_cycles_raw == no_cycles_step_table:
                return True
            else:
                return False

        else:
            validated = True
            if no_cycles_raw != no_cycles_step_table:
                logging.debug("  differ in no. of cycles")
                validated = False
            else:
                for j in range(1, no_cycles_raw + 1):
                    cycle_number = j
                    no_steps_raw = len(
                        externals.numpy.unique(
                            d.loc[
                                d[self.headers_normal.cycle_index_txt] == cycle_number,
                                self.headers_normal.step_index_txt,
                            ]
                        )
                    )
                    no_steps_step_table = len(
                        s.loc[
                            s[headers_step_table.cycle] == cycle_number,
                            headers_step_table.step,
                        ]
                    )
                    if no_steps_raw != no_steps_step_table:
                        validated = False
            return validated

    def print_steps(self):
        """Print the step table."""
        st = self.data.steps
        print(st)

    def get_step_numbers(
        self,
        steptype: str = "charge",
        allctypes: bool = True,
        pdtype: bool = False,
        cycle_number: int = None,
        trim_taper_steps: int = None,
        steps_to_skip: Optional[list] = None,
        steptable: Any = None,
        usteps: bool = False,
    ) -> Union[dict, Any]:
        # TODO: @jepe - include sub_steps here
        # TODO: @jepe - include option for not selecting taper steps here
        # TODO: @jepe - refactor this method!
        """Get the step numbers of selected type.

        Returns the selected step_numbers for the selected type of step(s).
        Either in a dictionary containing a list of step numbers corresponding
        to the selected steptype for the cycle(s), or a ``pandas.DataFrame`` instead of
        a dict of lists if pdtype is set to True. The frame is a sub-set of the
        step-table frame (i.e. all the same columns, only filtered by rows).

        Args:
            steptype (str): string identifying type of step.
            allctypes (bool): get all types of charge (or discharge).
            pdtype (bool): return results as pandas.DataFrame
            cycle_number (int): selected cycle, selects all if not set.
            trim_taper_steps (int): number of taper steps to skip (counted
                from the end, i.e. 1 means skip last step in each cycle).
            steps_to_skip (list): step numbers that should not be included.
            steptable (pandas.DataFrame): optional steptable

        Returns:
            dict or ``pandas.DataFrame``

        Examples:
            >>> my_charge_steps = CellpyCell.get_step_numbers(
            >>>    "charge",
            >>>    cycle_number = 3
            >>> )
            >>> print my_charge_steps
            {3: [5,8]}

        """
        if trim_taper_steps is not None and usteps:
            logging.warning(
                "Trimming taper steps is not possible when using usteps. Not doing any trimming."
            )
            trim_taper_steps = None

        if steps_to_skip is None:
            steps_to_skip = []

        if steptable is None:
            if not self.data.has_steps:
                logging.debug("step-table is not made")

                if self.force_step_table_creation or self.force_all:
                    logging.debug("creating step-table for")
                    logging.debug(self.data.loaded_from)
                    self.make_step_table()

                else:
                    logging.info(
                        "ERROR! Cannot use get_step_numbers: you must create your step-table first"
                    )
                    return None

        # check if steptype is valid
        steptype = steptype.lower()
        steptypes = []
        helper_step_types = ["ocv", "charge_discharge"]
        valid_step_type = True
        if steptype in self.list_of_step_types:
            steptypes.append(steptype)
        else:
            if steptype in helper_step_types:
                if steptype == "ocv":
                    steptypes.append("ocvrlx_up")
                    steptypes.append("ocvrlx_down")
                elif steptype == "charge_discharge":
                    steptypes.append("charge")
                    steptypes.append("discharge")
            else:
                valid_step_type = False
        if not valid_step_type:
            return None

        # in case of selection `allctypes`, then modify charge, discharge
        if allctypes:
            add_these = []
            for st in steptypes:
                if st in ["charge", "discharge"]:
                    st1 = st + "_cv"
                    add_these.append(st1)
                    st1 = "cv_" + st
                    add_these.append(st1)
            for st in add_these:
                steptypes.append(st)

        if steptable is None:
            st = self.data.steps
        else:
            st = steptable
        shdr = self.headers_step_table

        # Retrieving cycle numbers (if cycle_number is None, it selects all cycles)
        if cycle_number is None:
            cycle_numbers = self.get_cycle_numbers(steptable=steptable)
        else:
            if isinstance(cycle_number, collections.abc.Iterable):
                cycle_numbers = cycle_number
            else:
                cycle_numbers = [cycle_number]

        if trim_taper_steps is not None:
            trim_taper_steps = -trim_taper_steps
            logging.debug("taper steps to trim given")

        if pdtype:
            if trim_taper_steps:
                logging.info(
                    "Trimming taper steps is currently not"
                    "possible when returning externals.pandas.DataFrame. "
                    "Do it manually instead."
                )
            out = st[st[shdr.type].isin(steptypes) & st[shdr.cycle].isin(cycle_numbers)]
            return out

        out = dict()
        step_hdr = shdr.ustep if usteps else shdr.step
        for cycle in cycle_numbers:
            steplist = []
            for s in steptypes:
                mask_type_and_cycle = (st[shdr.type] == s) & (st[shdr.cycle] == cycle)
                if not any(mask_type_and_cycle):
                    logging.debug(f"Cycle {cycle} | StepType {s}: Not present!")
                else:
                    # Get the step numbers
                    step = st[mask_type_and_cycle][step_hdr].tolist()
                    for newstep in step[:trim_taper_steps]:
                        if newstep in steps_to_skip:
                            logging.debug(f"skipping step {newstep}")
                        else:
                            steplist.append(int(newstep))

            if not steplist:
                steplist = [0]
            out[cycle] = steplist
        return out

    def load_step_specifications(self, file_name, short=False):
        """Load a table that contains step-type definitions.

        This method loads a file containing a specification for each step or
        for each (cycle_number, step_number) combinations if `short==False`, and
        runs the `make_step_table` method. The step_cycle specifications that
        are allowed are stored in the variable `cellreader.list_of_step_types`.

        Args:
            file_name (str): name of the file to load
            short (bool): if True, the file only contains step numbers and
                step types. If False, the file contains cycle numbers as well.

        Returns:
            None
        """

        # if short:
        #     # the table only consists of steps (not cycle,step pairs) assuming
        #     # that the step numbers uniquely defines step type (this is true
        #     # for arbin at least).
        #     raise NotImplementedError

        step_specs = externals.pandas.read_csv(file_name, sep=config.reader.sep)
        if "step" not in step_specs.columns:
            logging.info("Missing column: step")
            raise IOError

        if "type" not in step_specs.columns:
            logging.info("Missing column: type")
            raise IOError

        if not short and "cycle" not in step_specs.columns:
            logging.info("Missing column: cycle")
            raise IOError

        self.make_step_table(step_specifications=step_specs, short=short)

    def _sort_data(self, dataset):
        # TODO: [# index]
        if self.headers_normal.data_point_txt in dataset.raw.columns:
            dataset.raw = dataset.raw.sort_values(
                self.headers_normal.data_point_txt
            ).reset_index()
            return dataset

        logging.debug("_sort_data: no datapoint header to sort by")

    def _ustep(self, n):
        un = []
        c = 0
        dn = n.diff()
        for i in dn:
            if i != 0:
                c += 1
            un.append(c)
        logging.debug("created u-steps")
        return un

    def make_step_table(
        self,
        step_specifications=None,
        short=False,
        override_step_types=None,
        override_raw_limits=None,
        profiling=False,
        all_steps=False,  # should be deprecated
        usteps=False,
        add_c_rate=True,
        skip_steps=None,
        sort_rows=True,
        from_data_point=None,
        nom_cap_specifics=None,
    ):
        """Create a table (v.4) that contains summary information for each step.

        This function creates a table containing information about the
        different steps for each cycle and, based on that, decides what type of
        step it is (e.g. charge) for each cycle.

        The format of the steps is:

        - index: cycleno - stepno - sub-step-no - ustep
        - Time info: average, stdev, max, min, start, end, delta
        - Logging info: average, stdev, max, min, start, end, delta
        - Current info: average, stdev, max, min, start, end, delta
        - Voltage info: average,  stdev, max, min, start, end, delta
        - Type: (from pre-defined list) - SubType
        - Info: not used.

        Args:
            step_specifications (pandas.DataFrame): step specifications
            short (bool): step specifications in short format
            override_step_types (dict): override the provided step types, for example set all
                steps with step number 5 to "charge" by providing {5: "charge"}.
            override_raw_limits (dict): override the instrument limits (resolution), for example set
                'current_hard' to 0.1 by providing {'current_hard': 0.1}.
            profiling (bool): turn on profiling
            usteps (bool): investigate all steps including same steps within
                one cycle (this is useful for e.g. GITT).
            add_c_rate (bool): include a C-rate estimate in the steps
            skip_steps (list of integers): list of step numbers that should not
                be processed (future feature - not used yet).
            sort_rows (bool): sort the rows after processing.
            from_data_point (int): first data point to use.
            nom_cap_specifics (str): "gravimetric", "areal", or "absolute".

        Returns:
            None

        """
        # TODO: @jepe - include option for omitting steps
        # TODO: @jepe  - make it is possible to update only new data

        if all_steps:
            warnings.warn(
                "all_steps will be deprecated, use usteps instead", FutureWarning
            )
            usteps = True

        self._guard_mixed_cycle_modes()

        time_00 = time.time()

        if nom_cap_specifics is None:
            nom_cap_specifics = self.nom_cap_specifics

        if profiling:
            print("PROFILING MAKE_STEP_TABLE".center(80, "="))

        # cellpy-core seam: delegate the per-step table computation to the core
        # (``make_core_step_table`` -> ``summarizers.make_step_table``). cellpy keeps
        # orchestration here: deprecation handling above, resolving the absolute
        # nominal capacity for the C-rate, and supplying the instrument resolution
        # limits (``self.raw_limits``). Both ``nom_cap`` (absolute) and
        # ``raw_limits`` are passed across the seam by value.
        nom_cap_abs = None
        if add_c_rate:
            # remark that no unit conversion is done with the current values!
            logging.debug("resolving nominal capacity for c-rate")
            nom_cap_abs = self.data.nom_cap
            if nom_cap_specifics == "gravimetric":
                nom_cap_abs = self.nominal_capacity_as_absolute(
                    nom_cap_abs, self.data.mass, nom_cap_specifics
                )
            elif nom_cap_specifics == "areal":
                nom_cap_abs = self.nominal_capacity_as_absolute(
                    nom_cap_abs, self.data.active_electrode_area, nom_cap_specifics
                )
            elif nom_cap_specifics == "absolute":
                nom_cap_abs = self.nominal_capacity_as_absolute(
                    nom_cap_abs, 1.0, nom_cap_specifics
                )

        result = self.core.make_core_step_table(
            self.data,
            raw_limits=self.raw_limits,
            step_specifications=step_specifications,
            short=short,
            override_step_types=override_step_types,
            override_raw_limits=override_raw_limits,
            usteps=usteps,
            add_c_rate=add_c_rate,
            nom_cap=nom_cap_abs,
            skip_steps=skip_steps,
            sort_rows=sort_rows,
            from_data_point=from_data_point,
        )

        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

        if from_data_point is not None:
            return result

        return self

    def _select_usteps(self, cycle: int, steps: Union[list, np.ndarray]):
        # TODO: @jepe - insert sub_step here
        s_hdr = self.headers_step_table.step
        us_hdr = self.headers_step_table.ustep
        c_txt = self.headers_normal.cycle_index_txt
        s_txt = self.headers_normal.step_index_txt
        steps = self.data.steps.loc[self.data.steps[us_hdr].isin(steps), s_hdr].unique()
        v = self.data.raw[
            (self.data.raw[c_txt] == cycle) & (self.data.raw[s_txt].isin(steps))
        ]

        if self._is_empty_array(v):
            logging.debug("empty dataframe")
            return None
        else:
            return v

    def _select_step(self, cycle, step):
        # TODO: @jepe - insert sub_step here
        c_txt = self.headers_normal.cycle_index_txt
        s_txt = self.headers_normal.step_index_txt
        v = self.data.raw[
            (self.data.raw[c_txt] == cycle) & (self.data.raw[s_txt] == step)
        ]

        if self._is_empty_array(v):
            logging.debug("empty dataframe")
            return None
        else:
            return v

    # TODO: move this out of CellpyCell
    # The tabular exporters live in cellpy.exporters.tabular (issue #518);
    # thin delegates below keep the public API and subclass dispatch.
    def _export_cycles(
        self,
        setname=None,
        sep=None,
        outname=None,
        shifted=False,
        method=None,
        shift=0.0,
        last_cycle=None,
    ):
        """Export voltage-capacity curves to a .csv file. See :func:`cellpy.exporters.tabular.export_cycles`."""
        return exporters_tabular.export_cycles(
            self,
            setname=setname,
            sep=sep,
            outname=outname,
            shifted=shifted,
            method=method,
            shift=shift,
            last_cycle=last_cycle,
        )

    def _export_normal(self, data, setname=None, sep=None, outname=None):
        """Export the raw frame to a .csv file. See :func:`cellpy.exporters.tabular.export_normal`."""
        return exporters_tabular.export_normal(
            self, data, setname=setname, sep=sep, outname=outname
        )

    def _export_stats(self, data, setname=None, sep=None, outname=None):
        """Export the summary frame to a .csv file. See :func:`cellpy.exporters.tabular.export_stats`."""
        return exporters_tabular.export_stats(
            self, data, setname=setname, sep=sep, outname=outname
        )

    def _export_steptable(self, data, setname=None, sep=None, outname=None):
        """Export the steps frame to a .csv file. See :func:`cellpy.exporters.tabular.export_steptable`."""
        return exporters_tabular.export_steptable(
            self, data, setname=setname, sep=sep, outname=outname
        )

    def to_excel(
        self,
        filename=None,
        cycles=None,
        raw=False,
        steps=True,
        nice=True,
        get_cap_kwargs=None,
        to_excel_kwargs=None,
    ):
        """Saves the data as .xlsx file(s). See :func:`cellpy.exporters.tabular.to_excel`."""
        return exporters_tabular.to_excel(
            self,
            filename=filename,
            cycles=cycles,
            raw=raw,
            steps=steps,
            nice=nice,
            get_cap_kwargs=get_cap_kwargs,
            to_excel_kwargs=to_excel_kwargs,
        )

    def to_csv(
        self,
        datadir=None,
        sep=None,
        cycles=False,
        raw=True,
        summary=True,
        shifted=False,
        method=None,
        shift=0.0,
        last_cycle=None,
    ):
        """Saves the data as .csv file(s). See :func:`cellpy.exporters.tabular.to_csv`."""
        return exporters_tabular.to_csv(
            self,
            datadir=datadir,
            sep=sep,
            cycles=cycles,
            raw=raw,
            summary=summary,
            shifted=shifted,
            method=method,
            shift=shift,
            last_cycle=last_cycle,
        )

    def to_bdf(
        self,
        filename=None,
        *,
        cycles=None,
        last_cycle=None,
        header_style="preferred",
        format="csv",
        extras=False,
        preprocess_fn=None,
        bdf_units=None,
    ):
        """Export the raw time-series in Battery Data Format (BDF).

        See `Battery Data Format <https://github.com/battery-data-alliance/battery-data-format>`_
        for the full specification.

        Args:
            filename: Output path. If ``None`` or extensionless, a default
                ``<cell_name>.bdf.<format>`` (or ``<filename>.bdf.<format>``)
                is used. An explicit suffix is honoured as-is.
            cycles: Optional cycle filter. ``None`` exports all cycles; an
                ``int`` exports that single cycle; an iterable of ints
                exports the listed cycles. Combines with ``last_cycle``.
            last_cycle: If given, drop rows whose cycle index exceeds
                ``last_cycle``.
            header_style: ``"preferred"`` (default, BDF spec) writes
                headers like ``"Test Time / s"``. ``"machine"`` writes
                machine-readable names like ``"test_time_second"``.
            format: ``"csv"`` (default) or ``"parquet"``.
            extras: Append columns from ``data.raw`` that are not in the
                BDF column map. ``False`` (default) exports only the BDF
                columns. ``True`` appends every unmapped raw column
                verbatim (no unit conversion, original name preserved).
                A string or iterable of strings restricts the appended
                columns to the listed names. The resulting file is no
                longer strictly BDF-compliant.
            preprocess_fn: A function that takes the raw DataFrame and returns
                a new DataFrame. This function is applied to the raw DataFrame
                after the cycle filter and before the BDF export.
            bdf_units: Optional
                :class:`~cellpy.parameters.internal_settings.CellpyUnits`
                controlling the **units written into the BDF file**.
                ``None`` (default) emits a strictly BDF-compliant file
                (``A``, ``V``, ``Ah``, ``Wh``, ``s``, ``W``, ``ohm``).
                When set, each attribute on the ``CellpyUnits`` overrides
                the spec target for the corresponding column kind
                (``charge`` → charge / discharge capacity, ``energy`` →
                charge / discharge energy, etc.); column labels and
                machine names are rebuilt from the override
                (e.g. ``"Charging Capacity / mAh"`` /
                ``"charging_capacity_mah"``) and values are scaled
                accordingly via pint. An incompatible unit (e.g.
                ``charge="kg"``) raises :class:`ValueError`. A file
                written with overrides is no longer strictly BDF-
                compliant; this is logged once at INFO level.

                Example::

                    from cellpy.parameters.internal_settings import CellpyUnits

                    # write charge in mAh and current in mA
                    bdf_units = CellpyUnits(charge="mAh", current="mA")
                    cell.to_bdf("out.bdf.csv", bdf_units=bdf_units)

        Returns:
            pathlib.Path: The path that the file was written to.

        Raises:
            ValueError: If the cell has no raw data, any BDF-required
                column is missing from ``data.raw``, or ``bdf_units``
                specifies a unit that cannot be converted from the
                cell's source unit.
        """
        from cellpy.exporters import to_bdf as _to_bdf

        return _to_bdf(
            self,
            filename,
            cycles=cycles,
            last_cycle=last_cycle,
            header_style=header_style,
            format=format,
            extras=extras,
            preprocess_fn=preprocess_fn,
            bdf_units=bdf_units,
        )

    # --------------helper-functions--------------------------------------------
    def _fix_dtype_step_table(self, dataset):
        return cellpy_file_dtype.fix_dtype_step_table(dataset)

    # near-dead, test-pinned only; moved to cellpy.exporters.tabular (#518),
    # removal decision deferred to the DI pass (#520)
    def _cap_mod_summary(self, summary, capacity_modifier="reset"):
        """See :func:`cellpy.exporters.tabular.cap_mod_summary`."""
        return exporters_tabular.cap_mod_summary(
            self, summary, capacity_modifier=capacity_modifier
        )

    def _cap_mod_normal(self, capacity_modifier="reset", allctypes=True):
        """See :func:`cellpy.exporters.tabular.cap_mod_normal`."""
        return exporters_tabular.cap_mod_normal(
            self, capacity_modifier=capacity_modifier, allctypes=allctypes
        )

    def get_mass(self):
        """Returns the mass of the active material (in mg).

        This method will be deprecated in the future.
        """
        return self.data.meta_common.mass

    def sget_voltage(self, cycle, step):
        """Returns voltage for cycle, step.

        Convenience function; same as issuing::

            raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][voltage_header]

        Args:
            cycle: cycle number
            step: step number

        Returns:
            pandas.Series or None if empty
        """
        header = self.headers_normal.voltage_txt
        return self._sget(cycle, step, header)

    def sget_current(self, cycle, step):
        """Returns current for cycle, step.

        Convenience function; same as issuing::

            raw[(raw[cycle_index_header] == cycle) & (raw[step_index_header] == step)][current_header]

        Args:
            cycle: cycle number
            step: step number

        Returns:
            pandas.Series or None if empty
        """
        header = self.headers_normal.current_txt
        return self._sget(cycle, step, header)

    def get_raw(
        self,
        header,
        cycle: Optional[Union[Iterable, int]] = None,
        with_index: bool = True,
        with_step: bool = False,
        with_time: bool = False,
        additional_headers: Optional[list] = None,
        as_frame: bool = True,
        scaler: Optional[float] = None,
    ) -> Union["externals.pandas.DataFrame", List["externals.numpy.array"]]:
        """Returns the values for column with given header (in raw units).

        Args:
            header: header name.
            cycle: cycle number (all cycles if None).
            with_index: if True, includes the cycle index as a column in the returned pandas.DataFrame.
            with_step: if True, includes the step index as a column in the returned pandas.DataFrame.
            with_time: if True, includes the time as a column in the returned pandas.DataFrame.
            additional_headers (list): additional headers to include in the returned pandas.DataFrame.
            as_frame: if not True, returns a list of current values as numpy arrays (one for each cycle).
                Remark that with_time and with_index will be False if as_frame is set to False.
            scaler: if not None, the returned values are scaled by this value.

        Returns:
            pandas.DataFrame (or list of numpy arrays if as_frame=False)
        """
        y_header = header  # Consider including some lookup handling here
        cycle_index_header = self.headers_normal.cycle_index_txt
        time_header = self.headers_normal.test_time_txt
        step_index_header = self.headers_normal.step_index_txt

        if not as_frame:
            with_time = False
            with_index = True
            with_step = False
            additional_headers = None

        y_headers = [y_header]
        if with_time:
            y_headers.append(time_header)
        if with_step:
            y_headers.append(step_index_header)
        if with_index:
            y_headers.append(cycle_index_header)

        y_headers = reversed(y_headers)
        if additional_headers is not None:
            y_headers.extend(additional_headers)

        data = self.data.raw

        if cycle is None:
            cycle = self.get_cycle_numbers()
        else:
            if not isinstance(cycle, collections.abc.Iterable):
                cycle = [cycle]

        logging.debug(f"getting current for cycles {cycle}")
        c = data.loc[(data[cycle_index_header].isin(cycle)), y_headers]

        if scaler is not None:
            c[y_header] = c[y_header] * scaler

        if not as_frame:
            gb = c.groupby(cycle_index_header)
            c = [gb.get_group(x) for x in gb.groups]
            c = [x[y_header].values for x in c]
        return c

    def get_voltage(self, cycle=None, with_index=True, with_time=False, as_frame=True):
        """Returns voltage (in raw units).

        Args:
            cycle: cycle number (all cycles if None).
            with_index: if True, includes the cycle index as a column in the returned pandas.DataFrame.
            with_time: if True, includes the time as a column in the returned pandas.DataFrame.
            as_frame: if not True, returns a list of current values as numpy arrays (one for each cycle).
                Remark that with_time and with_index will be False if as_frame is set to False.

        Returns:
            pandas.DataFrame (or list of pandas.Series if cycle=None and as_frame=False)
        """

        y_header = self.headers_normal.voltage_txt
        return self.get_raw(
            y_header,
            cycle=cycle,
            with_index=with_index,
            with_time=with_time,
            as_frame=as_frame,
            with_step=False,
            additional_headers=None,
            scaler=None,
        )

    def get_current(self, cycle=None, with_index=True, with_time=False, as_frame=True):
        """Returns current (in raw units).

        Args:
            cycle: cycle number (all cycles if None).
            with_index: if True, includes the cycle index as a column in the returned pandas.DataFrame.
            with_time: if True, includes the time as a column in the returned pandas.DataFrame.
            as_frame: if not True, returns a list of current values as numpy arrays (one for each cycle).
                Remark that with_time and with_index will be False if as_frame is set to False.

        Returns:
            ``pandas.DataFrame`` (or list of ``pandas.Series`` if cycle=None and as_frame=False)
        """

        y_header = self.headers_normal.current_txt
        return self.get_raw(
            y_header,
            cycle=cycle,
            with_index=with_index,
            with_time=with_time,
            as_frame=as_frame,
            with_step=False,
            additional_headers=None,
            scaler=None,
        )

    def get_datetime(self, cycle=None, with_index=True, with_time=False, as_frame=True):
        """Returns datetime (in raw units).

        Args:
            cycle: cycle number (all cycles if None).
            with_index: if True, includes the cycle index as a column in the returned pandas.DataFrame.
            with_time: if True, includes the time as a column in the returned pandas.DataFrame.
            as_frame: if not True, returns a list of current values as numpy arrays (one for each cycle).
                Remark that with_time and with_index will be False if as_frame is set to False.

        Returns:
            ``pandas.DataFrame`` (or list of ``pandas.Series`` if cycle=None and as_frame=False)
        """

        y_header = self.headers_normal.datetime_txt
        return self.get_raw(
            y_header,
            cycle=cycle,
            with_index=with_index,
            with_time=with_time,
            as_frame=as_frame,
            with_step=False,
            additional_headers=None,
            scaler=None,
        )

    def get_timestamp(
        self, cycle=None, with_index=True, as_frame=True, in_minutes=False, units="raw"
    ):
        """Returns timestamp.

        Args:
            cycle: cycle number (all cycles if None).
            with_index: if True, includes the cycle index as a column in the returned pandas.DataFrame.
            as_frame: if not True, returns a list of current values as numpy arrays (one for each cycle).
                Remark that with_time and with_index will be False if as_frame is set to False.
            in_minutes: (deprecated, use units="minutes" instead) return values in minutes
                instead of seconds if True.
            units: return values in given time unit ("raw", "seconds", "minutes", "hours").

        Returns:
            ``pandas.DataFrame`` (or list of ``pandas.Series`` if cycle=None and as_frame=False)
        """

        y_header = self.headers_normal.test_time_txt

        if in_minutes:
            units = "minutes"

        if units == "raw":
            scaler = None
        else:
            scaler = self.unit_scaler_from_raw(units, "time")

        return self.get_raw(
            y_header,
            cycle=cycle,
            with_index=with_index,
            with_time=False,
            as_frame=as_frame,
            with_step=False,
            additional_headers=None,
            scaler=scaler,
        )

    def sget_steptime(self, cycle, step):
        """Returns step time for cycle, step.

        Convenience function; Convenience function; same as issuing::

            raw[(raw[cycle_index_header] == cycle) & (raw[step_index_header] == step)][step_time_header]

        Args:
            cycle: cycle number
            step: step number

        Returns:
            ``pandas.Series`` or None if empty
        """

        header = self.headers_normal.step_time_txt
        return self._sget(cycle, step, header)

    def _sget(self, cycle, step, header):
        logging.debug(f"searching for {header}")

        cycle_index_header = self.headers_normal.cycle_index_txt
        step_index_header = self.headers_normal.step_index_txt

        test = self.data.raw

        if not isinstance(step, (list, tuple)):
            step = [step]

        return test.loc[
            (test[cycle_index_header] == cycle) & (test[step_index_header].isin(step)),
            header,
        ].reset_index(drop=True)

    def sget_timestamp(self, cycle, step):
        """Returns timestamp for cycle, step.

        Convenience function; same as issuing::

            raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][timestamp_header]

        Args:
            cycle: cycle number
            step: step number (can be a list of several step numbers)

        Returns:
            ``pandas.Series``
        """

        header = self.headers_normal.test_time_txt
        return self._sget(cycle, step, header)

    def sget_step_numbers(self, cycle, step):
        """Returns step number for cycle, step.

        Convenience function; same as issuing::

            raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][step_index_header]

        Args:
            cycle: cycle number
            step: step number (can be a list of several step numbers)

        Returns:
            ``pandas.Series``
        """

        header = self.headers_normal.step_index_txt
        return self._sget(cycle, step, header)

    def _using_usteps(self):
        if self.headers_step_table.ustep in self.data.steps.columns:
            return True
        return False

    # The capacity/curve getters live in cellpy.readers.capacity_curves
    # (issue #509); these delegates keep the public API and subclass
    # dispatch unchanged.

    def get_dcap(
        self,
        cycle=None,
        converter=None,
        mode='gravimetric',
        as_frame=True,
        usteps=False,
        **kwargs,
    ):
        """Returns discharge capacity and voltage for the selected cycle. See :func:`cellpy.readers.capacity_curves.get_dcap`."""
        return capacity_curves.get_dcap(
            self,
            cycle=cycle,
            converter=converter,
            mode=mode,
            as_frame=as_frame,
            usteps=usteps,
            **kwargs,
        )

    def get_ccap(
        self,
        cycle=None,
        converter=None,
        mode='gravimetric',
        as_frame=True,
        usteps=False,
        **kwargs,
    ):
        """Returns charge capacity and voltage for the selected cycle. See :func:`cellpy.readers.capacity_curves.get_ccap`."""
        return capacity_curves.get_ccap(
            self,
            cycle=cycle,
            converter=converter,
            mode=mode,
            as_frame=as_frame,
            usteps=usteps,
            **kwargs,
        )

    def get_cap(
        self,
        cycle=None,
        cycles=None,
        method='back-and-forth',
        insert_nan=None,
        shift=0.0,
        categorical_column=False,
        label_cycle_number=False,
        split=False,
        interpolated=False,
        dx=0.1,
        number_of_points=None,
        ignore_errors=True,
        inter_cycle_shift=True,
        interpolate_along_cap=False,
        capacity_then_voltage=False,
        mode='gravimetric',
        mass=None,
        area=None,
        volume=None,
        cycle_mode=None,
        usteps=None,
        dynamic=False,
        **kwargs,
    ):
        """Gets the capacity for the run. See :func:`cellpy.readers.capacity_curves.get_cap`."""
        return capacity_curves.get_cap(
            self,
            cycle=cycle,
            cycles=cycles,
            method=method,
            insert_nan=insert_nan,
            shift=shift,
            categorical_column=categorical_column,
            label_cycle_number=label_cycle_number,
            split=split,
            interpolated=interpolated,
            dx=dx,
            number_of_points=number_of_points,
            ignore_errors=ignore_errors,
            inter_cycle_shift=inter_cycle_shift,
            interpolate_along_cap=interpolate_along_cap,
            capacity_then_voltage=capacity_then_voltage,
            mode=mode,
            mass=mass,
            area=area,
            volume=volume,
            cycle_mode=cycle_mode,
            usteps=usteps,
            dynamic=dynamic,
            **kwargs,
        )

    def _get_cap(
        self,
        cycle=None,
        cap_type='charge',
        trim_taper_steps=None,
        steps_to_skip=None,
        steptable=None,
        converter=None,
        usteps=False,
        detailed=False,
    ):
        """ See :func:`cellpy.readers.capacity_curves._get_cap`."""
        return capacity_curves._get_cap(
            self,
            cycle=cycle,
            cap_type=cap_type,
            trim_taper_steps=trim_taper_steps,
            steps_to_skip=steps_to_skip,
            steptable=steptable,
            converter=converter,
            usteps=usteps,
            detailed=detailed,
        )

    def get_ocv(
        self,
        cycles=None,
        direction='up',
        remove_first=False,
        interpolated=False,
        dx=None,
        number_of_points=None,
    ):
        """Get the open circuit voltage relaxation curves. See :func:`cellpy.readers.capacity_curves.get_ocv`."""
        return capacity_curves.get_ocv(
            self,
            cycles=cycles,
            direction=direction,
            remove_first=remove_first,
            interpolated=interpolated,
            dx=dx,
            number_of_points=number_of_points,
        )
    def get_number_of_cycles(self, steptable=None):
        """Get the number of cycles in the test."""
        if steptable is None:
            d = self.data.raw
            number_of_cycles = externals.numpy.amax(
                d[self.headers_normal.cycle_index_txt]
            )
        else:
            number_of_cycles = externals.numpy.amax(
                steptable[self.headers_step_table.cycle]
            )
        return number_of_cycles

    def get_rates(self, steptable=None, agg="first", direction=None):
        """
        Get the rates in the test (only valid for constant current).

        Args:
            steptable: provide custom steptable (if None, the steptable from the cellpydata object will be used).
            agg (str): perform an aggregation if more than one step of charge or
                discharge is found (e.g. "mean", "first", "max"). For example, if agg='mean', the average rate
                for each cycle will be returned. Set to None if you want to keep all the rates.
            direction (str or list of str): only select rates for this direction (e.g. "charge" or "discharge").

        Returns:
            ``pandas.DataFrame`` with cycle, type, and rate_avr (i.e. C-rate) columns.
        """

        if steptable is None:
            steptable = self.data.steps
        rates = steptable[
            [
                self.headers_step_table.cycle,
                self.headers_step_table.type,
                self.headers_step_table.rate_avr,
            ]
        ].dropna()

        if agg:
            rates = (
                rates.groupby(
                    [self.headers_step_table.cycle, self.headers_step_table.type]
                )
                .agg(agg)
                .reset_index()
            )

        if direction is not None:
            if not isinstance(direction, (list, tuple)):
                direction = [direction]
            rates = rates.loc[rates[self.headers_step_table.type].isin(direction), :]

        return rates

    def get_cycle_numbers(
        self,
        steptable=None,
        rate=None,
        rate_on=None,
        rate_std=None,
        rate_agg="first",
        inverse=False,
    ):
        """Get a array containing the cycle numbers in the test.

        Args:
            steptable (pandas.DataFrame): the step-table to use (if None, the step-table
                from the cellpydata object will be used).
            rate (float): the rate to filter on. Remark that it should be given
                as a float, i.e. you will have to convert from C-rate to
                the actual numeric value. For example, use rate=0.05 if you want
                to filter on cycles that has a C/20 rate.
            rate_on (str): only select cycles if based on the rate of this step-type (e.g. on="discharge").
            rate_std (float): allow for this inaccuracy in C-rate when selecting cycles
            rate_agg (str): perform an aggregation on rate if more than one step of charge or discharge is found
                (e.g. "mean", "first", "max"). For example, if agg='mean', the average rate for each cycle
                will be returned. Set to None if you want to keep all the rates.
            inverse (bool): select steps that does not have the given C-rate.

        Returns:
            numpy.ndarray of cycle numbers.
        """

        # TODO: add support for selecting cycles based on other criteria (for example, based on the
        #   existence of particular step-types, or max, min values of current, voltage, etc)

        logging.debug("getting cycle numbers")

        if steptable is None:
            d = self.data.raw
            cycles = d[self.headers_normal.cycle_index_txt].dropna().unique()
            steptable = self.data.steps
        else:
            logging.debug("steptable is given as input parameter")
            cycles = steptable[self.headers_step_table.cycle].dropna().unique()

        if rate is None:
            return cycles

        logging.debug("filtering on rate")

        if rate is None:
            rate = 0.05

        if rate_std is None:
            rate_std = 0.1 * rate

        if rate_on is None:
            rate_on = ["charge", "discharge"]
        rates = self.get_rates(steptable=steptable, agg=rate_agg, direction=rate_on)
        rate_column = self.headers_step_table.rate_avr
        cycles_mask = (rates[rate_column] < (rate + rate_std)) & (
            rates[rate_column] > (rate - rate_std)
        )

        if inverse:
            cycles_mask = ~cycles_mask

        filtered_rates = rates[cycles_mask]
        filtered_cycles = filtered_rates[self.headers_step_table["cycle"]].unique()

        return filtered_cycles

    def get_ir(self):
        """Get the IR data (Deprecated)."""
        raise DeprecatedFeature

    def has_data_point_as_index(self):
        """Check if the raw data has data_point as index."""
        return self.data.raw.index.name == self.headers_normal.data_point_txt

    def has_data_point_as_column(self):
        """Check if the raw data has data_point as column."""
        return self.headers_normal.data_point_txt in self.data.raw.columns

    def has_no_full_duplicates(self):
        """Check if the raw data has no full duplicates."""
        return not self.data.raw.duplicated().any()

    def has_no_partial_duplicates(self, subset="data_point"):
        """Check if the raw data has no partial duplicates."""
        if subset == "data_point":
            subset = self.headers_normal.data_point_txt
        return not self.data.raw.duplicated(subset=subset).any()

    def total_time_at_voltage_level(
        self,
        cycles=None,
        voltage_limit=0.5,
        sampling_unit="S",
        at="low",
    ):
        """Experimental method for getting the total time spent at low / high voltage.

        Args:
            cycles: cycle number (all cycles if None).
            voltage_limit: voltage limit (default 0.5 V). Can be a tuple (low, high) if at="between".
            sampling_unit: sampling unit (default "S")
                    H: hourly frequency
                    T, min: minutely frequency
                    S: secondly frequency
                    L, ms:  milliseconds
                    U, us: microseconds
                    N: nanoseconds
            at (str): "low", "high", or "between" (default "low")
        """

        from pandas.api.types import is_datetime64_any_dtype as is_datetime

        if at not in ["low", "high", "between"]:
            raise ValueError("at must be either 'low', 'high', or 'between'")

        if sampling_unit not in ["S"]:
            logging.critical("Only 'S' (seconds) has been tested so far.")
            logging.critical(
                f"It might work with sampling_unit='{sampling_unit}'"
                f"however, the result you get is probably in {sampling_unit} and not"
                f"seconds."
            )

        date_time_hdr = "date_time"
        cycle_index_hdr = "cycle_index"
        voltage_hdr = "voltage"
        date_time_format = prms._date_time_format

        if cycles is not None:
            if not isinstance(cycles, (list, tuple)):
                cycles = [cycles]
            v = self.data.raw.loc[
                self.data.raw[cycle_index_hdr].isin(cycles),
                [date_time_hdr, cycle_index_hdr, voltage_hdr],
            ].copy()
        else:
            v = self.data.raw[[date_time_hdr, cycle_index_hdr, voltage_hdr]].copy()

        # make sure data_time is datetime64[ns] (not sure if this works for all tester formats/loaders):
        col_has_date_time_dtype = is_datetime(v[date_time_hdr])
        duplicated = v[date_time_hdr].duplicated().any()

        if not col_has_date_time_dtype:
            logging.debug("converting date_time to datetime64[ns]")
            v[date_time_hdr] = externals.pandas.to_datetime(
                v[date_time_hdr], format=date_time_format
            )

        if duplicated:
            logging.debug("removing duplicated date_time values")
            v = v.loc[~v[date_time_hdr].duplicated(), :]

        v = v.set_index(date_time_hdr, drop=True)
        # Convert 'S' to 's' to avoid pandas FutureWarning about deprecated frequency alias
        resample_unit = "s" if sampling_unit == "S" else sampling_unit
        v = v.resample(resample_unit).ffill().bfill()
        v["is_at_target"] = 0

        if at == "low":
            v.loc[v[voltage_hdr] < voltage_limit, "is_at_target"] = 1
        elif at == "high":
            v.loc[v[voltage_hdr] > voltage_limit, "is_at_target"] = 1
        elif at == "between":
            v.loc[
                (v[voltage_hdr] > voltage_limit[0])
                & (v[voltage_hdr] < voltage_limit[1]),
                "is_at_target",
            ] = 1
        else:
            # This will never occur, but keeping it here for completeness
            raise ValueError("at must be either 'low' or 'high'")

        # missing option - convert to seconds
        return v.is_at_target.sum()

    def nominal_capacity_as_absolute(
        self,
        value=None,
        specific=None,
        nom_cap_specifics=None,
        convert_charge_units=False,
    ):
        """Get the nominal capacity as absolute value.

        Delegated to ``cellpycore.units.nominal_capacity_as_absolute``
        (#451, unit plan Phase 2). A ``DimensionalityError`` here usually
        means the nominal capacity is given in a different unit than the
        chosen ``nom_cap_specifics`` — e.g. ``nom_cap='1.2 mAh/cm**2'`` with
        gravimetric specifics; pass ``nom_cap_specifics='areal'`` (or set it
        on the cell before processing).
        """
        return core_units.nominal_capacity_as_absolute(
            data=self.data,
            value=value,
            specific=specific,
            nom_cap_specifics=nom_cap_specifics or "gravimetric",
            convert_charge_units=convert_charge_units,
            cellpy_units=self.cellpy_units,
        )

    def with_cellpy_unit(self, parameter, as_str=False):
        """Return quantity as `pint.Quantity` object."""
        _look_up = {
            "nom_cap": "nominal_capacity",
            "active_electrode_area": "area",
        }
        _parameter = parameter
        if parameter in _look_up.keys():
            _parameter = _look_up[parameter]

        try:
            _unit = self.cellpy_units[_parameter]
        except KeyError:
            print(f"Did not find any units registered for {parameter}")
            return

        try:
            _value = getattr(self.data, parameter)
        except AttributeError:
            print(
                f"{parameter} is not a valid cellpy data attribute (but the unit is {_unit})"
            )
            return

        if as_str:
            return f"{_value} {_unit}"

        return ds.Q(_value, _unit)

    def to_cellpy_unit(self, value, physical_property):
        """Convert value to cellpy units.

        Args:
            value (numeric, pint.Quantity or str): what you want to convert from
            physical_property (str): What this value is a measure of
                (must correspond to one of the keys in the CellpyUnits class).

        Returns (numeric):
            the value in cellpy units
        """
        # Delegated to cellpycore.units.convert_value (#451); pint Quantity
        # inputs are handled here since core's public API takes plain values.
        if isinstance(value, externals.pint.Quantity):
            return value.to(self.cellpy_units[physical_property]).m
        try:
            raw_units = self.data.raw_units
        except NoDataFound:
            raise NoDataFound(
                "If you dont have any cells you cannot convert"
                " values to cellpy units without providing what"
                " unit to convert from!"
            )
        return core_units.convert_value(
            value,
            physical_property,
            from_units=raw_units,
            to_units=self.cellpy_units,
        )

    def unit_scaler_from_raw(self, unit, physical_property):
        """Get the conversion factor going from raw to given unit.

        Args:
            unit (str): what you want to convert to
            physical_property (str): what this value is a measure of
                (must correspond to one of the keys in the CellpyUnits class).

        Returns (numeric):
            conversion factor (scaler)
        """
        # Delegated to cellpycore.units.calculate_scaler (#451).
        return core_units.calculate_scaler(
            self.data.raw_units[physical_property], unit
        )

    def get_converter_to_specific(
        self,
        dataset: ds.Data = None,
        value: float = None,
        from_units: CellpyUnits = None,
        to_units: CellpyUnits = None,
        mode: str = "gravimetric",
    ) -> float:
        """Convert from absolute units to specific (areal or gravimetric).

        The method provides a conversion factor that you can multiply your
        values with to get them into specific values.

        Args:
            dataset: data instance
            value: value used to scale on.
            from_units: defaults to data.raw_units.
            to_units: defaults to cellpy_units.
            mode (str): gravimetric, areal or absolute

        Returns:
            conversion factor (float)

        """
        # TODO @jepe: implement handling of edge-cases
        # TODO @jepe: fix all the instrument readers (replace floats in raw_units with strings)
        # Delegated to cellpycore.units (#451, unit plan Phase 2); the core
        # port is the extended verbatim copy, guarded by converter-parity
        # fixtures on both sides.
        if mode is None:
            return 1.0
        if dataset is None:
            dataset = self.data
        return core_units.get_converter_to_specific(
            data=dataset,
            value=value,
            from_units=from_units,
            to_units=to_units or self.cellpy_units,
            mode=mode,
        )

    def _set_mass(self, value):
        # TODO: replace with setter
        try:
            self.data.meta_common.mass = value
        except AttributeError as e:
            logging.info("This test is empty")
            logging.info(e)

    def _set_tot_mass(self, value):
        # TODO: replace with setter
        try:
            self.data.meta_common.tot_mass = value
        except AttributeError as e:
            logging.info("This test is empty")
            logging.info(e)

    def _set_nom_cap(self, value):
        # TODO: replace with setter
        try:
            self.data.meta_common.nom_cap = value
        except AttributeError as e:
            logging.info("This test is empty")
            logging.info(e)

    def _set_run_attribute(self, attr, val, validated=None):
        # Sets the val (vals) for the test (datasets).
        # Remark! This is left-over code from old ages when we thought we needed
        #   to have data-sets with multiple cells. And before we learned about
        #   setters and getters in Python. Feel free to refactor it.

        # TODO: deprecate it

        if attr == "mass":
            setter = self._set_mass
        elif attr == "tot_mass":
            setter = self._set_tot_mass
        elif attr == "nom_cap":
            setter = self._set_nom_cap

        if not self.data:
            logging.info("No datasets have been loaded yet")
            logging.info(f"Cannot set {attr} before loading datasets")
            sys.exit(-1)

        if validated is None:
            setter(val)
        else:
            if validated:
                setter(val)
            else:
                logging.debug("_set_run_attribute: this set is empty")

    def set_mass(self, mass, validated=None):
        """

        Warning:
            This function is deprecated. Use the setter instead (mass = value).

        """

        warnings.warn(
            "This function is deprecated. Use the setter instead (mass = value).",
            DeprecationWarning,
            stacklevel=2,
        )
        self._set_run_attribute("mass", mass, validated=validated)

    def set_tot_mass(self, mass, validated=None):
        """

        Warning:
            This function is deprecated. Use the setter instead (tot_mass = value).

        """
        warnings.warn(
            "This function is deprecated. Use the setter instead (tot_mass = value).",
            DeprecationWarning,
            stacklevel=2,
        )

        self._set_run_attribute("tot_mass", mass, validated=validated)

    def set_nom_cap(self, nom_cap, validated=None):
        """

        Warning:
            This function is deprecated. Use the setter instead (nom_cap = value).

        """
        warnings.warn(
            "This function is deprecated. Use the setter instead (nom_cap = value).",
            DeprecationWarning,
            stacklevel=2,
        )

        self._set_run_attribute("nom_cap", nom_cap, validated=validated)

    @staticmethod
    def set_col_first(df, col_names):
        """Set selected columns first in a pandas.DataFrame.

        This function sets cols with names given in  col_names (a list) first in
        the DataFrame. The last col in col_name will come first (processed last)

        """

        column_headings = df.columns
        column_headings = column_headings.tolist()
        try:
            for col_name in col_names:
                _ = column_headings.index(col_name)
                column_headings.pop(column_headings.index(col_name))
                column_headings.insert(0, col_name)

        finally:
            df = df.reindex(columns=column_headings)

        return df

    def get_summary(self, use_summary_made=False):
        """Retrieve summary returned as a pandas DataFrame.

        Warning:
            This function is deprecated. Use the CellpyCell.data.summary property instead.

        """

        cell = self.data

        # This is a bit convoluted; in the old days, we used an attribute
        # called summary_made,
        # that was set to True when the summary was made successfully.
        # It is most likely never
        # used anymore. And will most probably be deleted.

        warnings.warn(
            "get_summary is deprecated. Use the CellpyCell.data.summary property instead.",
            DeprecationWarning,
        )

        if use_summary_made:
            summary_made = cell.has_summary
        else:
            summary_made = True

        if not summary_made:
            warnings.warn("Summary is not made yet")
            return None
        else:
            logging.info("Returning datasets[test_no].summary")
            return cell.summary

    # -----------internal-helpers-----------------------------------------------

    @staticmethod
    def _is_empty_array(v):
        try:
            if not v:
                return True
            else:
                return False
        except Exception:
            try:
                if v.empty:
                    return True
                else:
                    return False
            except Exception:
                if v.isnull:
                    return False
                else:
                    return True

    @staticmethod
    def _is_listtype(x):
        if isinstance(x, (list, tuple)):
            return True
        else:
            return False

    @staticmethod
    def _bounds(x):
        return externals.numpy.amin(x), externals.numpy.amax(x)

    @staticmethod
    def _roundup(x):
        n = 1000.0
        x = externals.numpy.ceil(x * n)
        x /= n
        return x

    def _rounddown(self, x):
        x = self._roundup(-x)
        x = -x
        return x

    @staticmethod
    def _reverse(x):
        x = x[::-1]
        # x = x.sort_index(ascending=True)
        return x

    def _select_y(self, x, y, points):
        # uses interpolation to select y = f(x)
        from scipy import interpolate

        min_x, max_x = self._bounds(x)
        if x[0] > x[-1]:
            # need to reverse
            x = self._reverse(x)
            y = self._reverse(y)
        f = interpolate.interp1d(y, x)
        y_new = f(points)
        return y_new

    def _select_last(self, raw):
        # this legacy method gives a set of indexes pointing to the last
        # datapoints for each cycle in the dataset (only used in the old
        # summary method and for the new summary method if use_cellpy_stat_file is True)

        c_txt = self.headers_normal.cycle_index_txt
        d_txt = self.headers_normal.data_point_txt
        steps = []
        unique_steps = raw[c_txt].unique()
        max_step = max(raw[c_txt])
        for j in range(int(max_step)):
            if j + 1 not in unique_steps:
                logging.debug(f"Warning: Cycle {j + 1} is missing!")
            else:
                last_item = max(raw.loc[raw[c_txt] == j + 1, d_txt])
                steps.append(last_item)

        last_items = raw[d_txt].isin(steps)
        return last_items

    # ----------making-summary------------------------------------------------------
    def make_summary(
        self,
        find_ir=False,
        find_end_voltage=True,
        use_cellpy_stat_file=None,
        ensure_step_table=True,
        remove_duplicates=True,
        normalization_cycles=None,
        nom_cap=None,
        nom_cap_specifics=None,
        create_copy=False,
        exclude_types=None,
        exclude_steps=None,
        selector_type=None,
        selector=None,
        exclude_step_types=None,
        **kwargs,
    ):
        """Convenience function that makes a summary of the cycling data.

        Args:
            find_ir (bool): if True, the internal resistance will be calculated.
            find_end_voltage (bool): if True, the end voltage will be calculated.
            use_cellpy_stat_file (bool): if True, the summary will be made from
                the cellpy_stat file (soon to be deprecated).
            ensure_step_table (bool): if True, the step-table will be made if it does not exist.
            remove_duplicates (bool): if True, duplicates will be removed from the summary.
            normalization_cycles (int or list of int): cycles to use for normalization.
            nom_cap (float or str): nominal capacity (if None, the nominal capacity from the data will be used).
            nom_cap_specifics (str): gravimetric, areal, or volumetric.
            create_copy (bool): if True, a copy of the cellpy object will be returned.
            exclude_types (list of str): deprecated, has no effect.
            exclude_steps (list of int): deprecated, has no effect.
            selector_type (str): deprecated, has no effect.
            selector (callable): deprecated, has no effect.
            exclude_step_types (list of str): step-type *prefixes* whose capacity
                contributions are excluded from the summary (issue #509, core #54).
                E.g. ``["cv_"]`` matches ``cv_charge`` and ``cv_discharge``; the
                capacity gained during the excluded steps is subtracted per cycle
                from the cycle-end charge/discharge capacities before derived
                columns (coulombic efficiency, losses, cumulated and specific
                columns) are computed — a summary "as if those steps never
                happened". Replaces the removed selector-based exclusion.
            **kwargs: additional keyword arguments sent to internal method (check source for info).

        Returns:
            cellpy.CellpyData: cellpy object with the summary added to it.
        """
        if any(
            v is not None
            for v in (selector, selector_type, exclude_types, exclude_steps)
        ):
            warnings.warn(
                "The 'selector', 'selector_type', 'exclude_types' and "
                "'exclude_steps' arguments to make_summary are deprecated and "
                "have no effect: the cellpy-core summary engine selects "
                "cycle-end data points internally and ignores custom selectors.",
                DeprecationWarning,
                stacklevel=2,
            )

        # TODO: @jepe  - make it is possible to update only new data by implementing
        #  from_cycle (only calculate summary from a given cycle number).
        #  Probably best to keep the old summary and make
        #  a new one for the rest, then use pandas.concat to merge them.
        #  Might have to create the cumulative cols etc after merging?

        # first - check if we need some "instrument-specific" prms
        if ensure_step_table is None:
            ensure_step_table = self.ensure_step_table

        if use_cellpy_stat_file is None:
            use_cellpy_stat_file = config.reader.use_cellpy_stat_file
            logging.debug("using use_cellpy_stat_file from prms")
            logging.debug(f"use_cellpy_stat_file: {use_cellpy_stat_file}")

        txt = "creating summary for file "
        try:
            test = self.data
        except NoDataFound:
            logging.info("Empty test (no data found)")
            return

        self._guard_mixed_cycle_modes()

        if isinstance(test.loaded_from, (list, tuple)):
            for f in test.loaded_from:
                txt += f"{f}\n"
        else:
            txt += str(test.loaded_from)

        logging.debug(txt)

        data = self._make_summary(
            find_ir=find_ir,
            find_end_voltage=find_end_voltage,
            use_cellpy_stat_file=use_cellpy_stat_file,
            ensure_step_table=ensure_step_table,
            remove_duplicates=remove_duplicates,
            normalization_cycles=normalization_cycles,
            nom_cap=nom_cap,
            nom_cap_specifics=nom_cap_specifics,
            create_copy=create_copy,
            exclude_step_types=exclude_step_types,
            **kwargs,
        )
        if create_copy:
            other = copy.deepcopy(self)
            other.data = data
            return other
        else:
            # TODO: check if anything is using this feature (returning self), if not, remove it.
            return self

    def _make_summary(
        self,
        mass=None,
        nom_cap=None,
        nom_cap_specifics=None,
        update_mass=False,
        select_columns=True,
        find_ir=True,
        find_end_voltage=False,
        ensure_step_table=True,
        remove_duplicates=True,
        sort_my_columns=True,
        use_cellpy_stat_file=False,
        normalization_cycles=None,
        create_copy=True,
        exclude_step_types=None,
        **kwargs,
    ):
        # ---------------- discharge loss --------------------------------------
        # Assume that both charge and discharge is defined as positive.
        # The gain for cycle n (compared to cycle n-1)
        # is then cap[n] - cap[n-1]. The loss is the negative of gain.
        # discharge loss = discharge_cap[n-1] - discharge_cap[n]

        # ---------------- charge loss -----------------------------------------
        # charge loss = charge_cap[n-1] - charge_cap[n]

        # --------- shifted capacities ------------------------------------------
        #  as defined by J. Dahn et al.
        # Note! Should double-check this (including checking
        # if it is valid in cathode mode).

        # --------- relative irreversible capacities -----------------------------
        #  as defined by Gauthier et al.
        # RIC = discharge_cap[n-1] - charge_cap[n] /  charge_cap[n-1]
        # RIC_SEI = discharge_cap[n] - charge_cap[n-1] / charge_cap[n-1]
        # RIC_disconnect = charge_cap[n-1] - charge_cap[n] / charge_cap[n-1]

        # --------- notes --------------------------------------------------------
        # @jepe 2022.09.11: trying to use .assign from now on
        #   as it is recommended (but this will likely increase memory usage)

        for k in kwargs:
            if cell_type := kwargs.get("cell_type", None):
                self.cycle_mode = cell_type.lower()
            else:
                warnings.warn(f"Unknown keyword argument: {k}")

        # TODO: add this to arguments and possible prms:
        if nom_cap_specifics is None:
            nom_cap_specifics = self.nom_cap_specifics
        specifics = ["gravimetric", "areal", "absolute"]
        # Polars Phase A (#457): keys live in columns, never in an index.
        cycle_index_as_index = False
        time_00 = time.time()
        logging.debug("start making summary")

        if create_copy:
            data = copy.deepcopy(self.data)
        else:
            data = self.data

        if not mass:
            mass = data.mass or 1.0
        else:
            if update_mass:
                data.mass = mass

        if use_cellpy_stat_file:
            warnings.warn(
                "using cellpy 'statfile' - this feature is not properly supported anymore"
            )

        if nom_cap is None:
            nom_cap = data.nom_cap

        logging.info(f"Using the following nominal capacity: {nom_cap}")

        # cellpy has historically assumed that the nominal capacity (nom_cap) is specific gravimetric
        # (i.e. in units of for example mAh/g), but now we need it in absolute units (e.g. Ah). The plan
        # is to set stuff like this during initiation of the cell (but not yet)

        # generating absolute nominal capacity (this should be refactored):
        if nom_cap_specifics == "gravimetric":
            nom_cap_abs = self.nominal_capacity_as_absolute(
                nom_cap, mass, nom_cap_specifics
            )
        elif nom_cap_specifics == "areal":
            nom_cap_abs = self.nominal_capacity_as_absolute(
                nom_cap, data.active_electrode_area, nom_cap_specifics
            )
        elif nom_cap_specifics == "absolute":
            nom_cap_abs = self.nominal_capacity_as_absolute(
                nom_cap, 1.0, nom_cap_specifics
            )

        # TODO: this will break because cell.volume (data.volume) is not set yet
        elif nom_cap_specifics == "volumetric":
            nom_cap_abs = self.nominal_capacity_as_absolute(
                nom_cap, data.volume, nom_cap_specifics
            )

        else:
            nom_cap_abs = self.nominal_capacity_as_absolute(
                nom_cap, mass, nom_cap_specifics
            )

        # ensuring that a step table exists:
        if ensure_step_table:
            logging.debug("ensuring existence of step-table")
            if not data.has_steps:
                logging.debug("dataset.step_table_made is not True")
                logging.info("running make_step_table")

                # update nom_cap in case it is given as argument to make_summary:
                data.nom_cap = nom_cap
                self.make_step_table()

        if not self.data.raw.index.is_unique:
            warnings.warn(f"{self.cell_name}: index is not unique for raw data")
            if remove_duplicates:
                logging.debug("removing duplicates before making summary")
                self.data.raw = self.data.raw[
                    ~self.data.raw.index.duplicated(keep="first")
                ]
            else:
                warnings.warn(
                    "You should remove the duplicates before making summary. For example using"
                    "c.data.raw = c.data.raw[~raw.index.duplicated(keep='first')]"
                )

        # cellpy-core seam: delegate the per-cycle summary pipeline to the ds.
        # ``make_core_summary`` builds the base summary (cycle-end selection +
        # index reset + column pruning) and the absolute / IR / end-voltage /
        # C-rate columns; ``add_scaled_summary_columns`` adds the meta-dependent
        # (equivalent-cycle and gravimetric/areal/absolute) columns. cellpy keeps
        # the nominal-capacity resolution, step-table/dedup handling above and
        # the column sort / index post-processing below.
        # cellpy-core takes unit conversions by value: cellpy (the consumer, which
        # owns cellpy_units and pint) computes the factors and passes them in, so
        # the core summary engine needs no pint.
        current_conversion_factor = core_units.calculate_current_conversion_factor(
            data.raw_units["current"], to_units=self.cellpy_units
        )
        specific_conversion_factors = {
            mode: self.get_converter_to_specific(
                dataset=data, mode=mode, to_units=self.cellpy_units
            )
            for mode in specifics
        }
        data = self.core.make_core_summary(
            data,
            find_ir=find_ir,
            find_end_voltage=find_end_voltage,
            select_columns=select_columns,
            current_conversion_factor=current_conversion_factor,
            exclude_step_types=exclude_step_types,
        )
        data = self.core.add_scaled_summary_columns(
            data,
            nom_cap_abs=nom_cap_abs,
            normalization_cycles=normalization_cycles,
            specifics=specifics,
            specific_conversion_factors=specific_conversion_factors,
        )

        if sort_my_columns:
            if self.native_schema:
                # #511 opt-in: the legacy first-column names do not exist on the
                # native summary; keep the engine's column order.
                logging.debug("native path: skipping legacy column sort")
            else:
                logging.debug("sorting columns")
                new_first_col_list = [
                    self.headers_normal.datetime_txt,
                    self.headers_normal.test_time_txt,
                    self.headers_normal.data_point_txt,
                    self.headers_normal.cycle_index_txt,
                ]
                data.summary = self.set_col_first(data.summary, new_first_col_list)

        if cycle_index_as_index:
            index_col = self.headers_summary.cycle_index
            try:
                data.summary.set_index(index_col, inplace=True)
            except KeyError:
                logging.debug("Setting cycle_index as index failed")

        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return data

    def add_to_summary(
        self,
        column: str,
        method: str = "last",
        new_name: Optional[str] = None,
    ) -> "CellpyCell":
        """Augment the summary frame with one value per cycle pulled from raw.

        For every cycle present in ``self.data.summary``, group the raw
        rows of ``column`` by ``cycle_index`` and reduce them with
        ``method``. The result is written onto the summary frame in place.

        Args:
            column: name of the column in ``self.data.raw`` to look up.
            method: groupby reducer applied per cycle. One of
                ``"last"`` (default), ``"first"``, ``"mean"``,
                ``"min"``, ``"max"``.
            new_name: name to use for the new summary column. Defaults
                to ``column``.

        Returns:
            self (chainable).

        Raises:
            ValueError: if ``column`` is not present in the raw frame or
                ``method`` is not one of the supported reducers.
            NoDataFound: propagated from ``self.data`` if no data is loaded.
        """
        allowed = {"last", "first", "mean", "min", "max"}
        if method not in allowed:
            raise ValueError(
                f"add_to_summary: method must be one of {sorted(allowed)}, "
                f"got {method!r}"
            )

        raw = self.data.raw
        summary = self.data.summary

        if column not in raw.columns:
            raise ValueError(
                f"add_to_summary: column {column!r} not found in raw "
                f"(available: {sorted(raw.columns)})"
            )

        hdrn_cycle = self.headers_normal.cycle_index_txt
        hdrs_cycle = self.headers_summary.cycle_index
        target = new_name or column

        per_cycle = raw.groupby(hdrn_cycle)[column].agg(method)

        if hdrs_cycle in summary.columns:
            summary[target] = summary[hdrs_cycle].map(per_cycle)
        else:
            summary[target] = per_cycle.reindex(summary.index)

        logging.debug(
            "add_to_summary: added %r (method=%s, %d non-null / %d rows)",
            target,
            method,
            summary[target].notna().sum(),
            len(summary),
        )
        return self

    def filtered_summary(
        self,
        *,
        rate=None,
        rate_columns=None,
        **extra_filters,
    ):
        """Return a filtered copy of the summary DataFrame.

        Thin wrapper around :func:`cellpy.filters.filter_summary` that
        resolves the rate column names from ``self.headers_summary``.
        See the underlying function for the full range semantics; in
        short ``(low, high)`` keeps rows where ``low < value <= high``
        and ``{"value": v, "delta": d}`` keeps rows where
        ``v - d < value <= v + d``.

        Note:
            The name deliberately reads as a property-style "give me a
            filtered summary" - the return is just the summary
            DataFrame. The slot ``CellpyCell.filter_summary`` is
            reserved for a future method that returns a full
            ``CellpyCell`` with the summary, raw, and steps frames all
            filtered consistently.

        Args:
            rate: Range filter applied to the rate columns. ``None``
                disables it (default).
            rate_columns: Override which rate columns are filtered.
                Defaults to both
                ``(headers_summary.charge_c_rate,
                headers_summary.discharge_c_rate)``. Pass a single
                string to filter on only one side.
            **extra_filters: Additional range filters registered with
                :func:`cellpy.filters.register_range_filter`.

        Returns:
            Filtered copy of ``self.data.summary`` (cycle index reset
            to a column so the result is a plain DataFrame).
        """
        from cellpy.filters import filter_summary as _fs

        h = self.headers_summary
        if rate_columns is None:
            rate_columns = (h.charge_c_rate, h.discharge_c_rate)
        return _fs(
            self.data.summary.reset_index(),
            rate=rate,
            rate_columns=rate_columns,
            **extra_filters,
        )

    def inspect_nominal_capacity(self, cycles=None):
        """Method for estimating the nominal capacity

        Args:
            cycles (list of ints): the cycles where it is assumed that the data reaches nominal capacity.

        Returns:
            Nominal capacity (float).
        """
        logging.debug("inspecting: nominal capacity")
        print("Sorry! This method is still under development.")
        print("Maybe you can plot your data and find the nominal capacity yourself?")
        if cycles is None:
            cycles = [1, 2, 3]

        summary = self.data.summary

        try:
            nc = summary.loc[
                summary[self.headers_normal.cycle_index_txt].isin(cycles),
                self.headers_summary.discharge_capacity,
            ].mean()
            print("All I can say for now is that the average discharge capacity")
            print(f"for the cycles {cycles} is {nc:0.2f}")
            nc = float(nc)

        except ZeroDivisionError:
            print("zero division error")
            nc = None

        return nc


def merge_cells(cells, mode="campaign", **kwargs) -> "CellpyCell":
    """Merge several cells into a new CellpyCell without mutating any of them.

    Convenience wrapper around :meth:`CellpyCell.merge` (issue #507): the
    first cell is deep-copied and the rest are folded in. See the method
    docstring for the "campaign" vs "continuation" semantics.

    Args:
        cells: sequence of CellpyCell (or Data) instances; order matters.
        mode (str): "campaign" (default) or "continuation".
        **kwargs: forwarded to :meth:`CellpyCell.merge`.

    Returns:
        A new CellpyCell holding the merged object.
    """
    cells = list(cells)
    if not cells:
        raise ValueError("merge_cells() needs at least one cell")
    first, rest = cells[0], cells[1:]
    if isinstance(first, CellpyCell):
        merged = copy.deepcopy(first)
    else:
        merged = CellpyCell(initialize=True)
        merged.data = copy.deepcopy(first)
    if rest:
        merged.merge(rest, mode=mode, **kwargs)
    return merged


def get(
    filename=None,
    instrument=None,
    instrument_file=None,
    cellpy_file=None,
    cycle_mode=None,
    mass: Union[str, numbers.Number] = None,
    nominal_capacity: Union[str, numbers.Number] = None,
    nom_cap_specifics=None,
    loading=None,
    area: Union[str, numbers.Number] = None,
    estimate_area=True,
    logging_mode=None,
    custom_log_dir=None,
    custom_log_config_path=None,
    auto_pick_cellpy_format=True,
    auto_summary=True,
    units=None,
    step_kwargs=None,
    summary_kwargs=None,
    selector=None,
    testing=False,
    refuse_copying=False,
    initialize=False,
    debug=False,
    **kwargs,
):
    """Create a CellpyCell object.

    Args:
        filename (str, os.PathLike, OtherPath, or list of raw-file names): path to file(s) or data-set(s) to load.
        instrument (str): instrument to use (defaults to the one in your cellpy config file).
        instrument_file (str or path): yaml file for custom file type.
        cellpy_file (str, os.PathLike, or OtherPath): if both filename (a raw-file) and cellpy_file (a cellpy file)
            is provided, cellpy will try to check if the raw file has been updated since the
            creation of the cellpy-file and select this instead of the raw file if cellpy thinks
            they are similar (use with care!).
        logging_mode (str): "INFO" or "DEBUG".
        cycle_mode (str): the cycle mode (e.g. "anode" or "full_cell").
        mass (float or str): mass of active material in cellpy_units (default mg)
            (defaults to mass given in cellpy-file or 1.0). Pass a string with unit
            (e.g. "1.14 mg") to override cellpy_units.
        nominal_capacity (float or str): nominal capacity in cellpy_units (default mAh/g;
            used for finding C-rates). Pass a string with unit (e.g. "155 mAh/g") to
            override cellpy_units. The expected unit depends on nom_cap_specifics
            (gravimetric/areal/volumetric/absolute).
        nom_cap_specifics (str): either "gravimetric" (per mass), or "areal" (per area).
            ("volumetric" is not fully implemented yet - let us know if you need it).
        loading (float or str): loading in units [mass] / [area] (cellpy_units).
        area (float or str): active electrode area in cellpy_units (default cm**2;
            e.g. used for finding the areal capacity). Pass a string with unit
            (e.g. "2.12 cm**2") to override cellpy_units.
        estimate_area (bool): calculate area from loading if given (defaults to True).
        auto_pick_cellpy_format (bool): decide if it is a cellpy-file based on suffix.
        auto_summary (bool): (re-) create summary.
        units (dict): update cellpy units (used after the file is loaded, e.g. when creating summary).
        step_kwargs (dict): sent to make_steps.
        summary_kwargs (dict): sent to make_summary.
        selector (dict): passed to load (when loading cellpy-files).
        testing (bool): set to True if testing (will for example prevent making .log files)
        refuse_copying (bool): set to True if you do not want to copy the raw-file before loading.
        initialize (bool): set to True if you want to initialize the CellpyCell object (probably only
            useful if you want to return a cellpy-file with no data in it).
        debug (bool): set to True if you want to debug the loader.
        **kwargs: sent to the loader.

    Transferred Parameters:
        model (str): model to use (only for loaders that supports models).
        bad_steps (list of tuples): (c, s) tuples of steps s (in cycle c) to skip loading ("arbin_res").
        dataset_number (int): the data set number ('Test-ID') to select if you are dealing
            with arbin files with more than one data-set. Defaults to selecting all data-sets
            and merging them ("arbin_res").
        data_points (tuple of ints): load only data from data_point[0] to
            data_point[1] (use None for infinite) ("arbin_res").
        increment_cycle_index (bool): increment the cycle index if merging several datasets (default True)
            ("arbin_res").
        sep (str): separator used in the file ("maccor_txt", "neware_txt", "local_instrument", "custom").
        skip_rows (int): number of rows to skip in the beginning of the file
            ("maccor_txt", "neware_txt", "local_instrument", "custom").
        header (int): row number of the header ("maccor_txt", "neware_txt", "local_instrument", "custom").
        encoding (str): encoding of the file ("maccor_txt", "neware_txt", "local_instrument", "custom").
        decimal (str): decimal separator ("maccor_txt", "neware_txt", "local_instrument", "custom").
        thousand (str): thousand separator ("maccor_txt", "neware_txt", "local_instrument", "custom").
        pre_processor_hook (callable): pre-processors to use ("maccor_txt", "neware_txt", "local_instrument", "custom").
        bad_steps (list of tuples): (c, s) tuples of steps s (in cycle c) to skip loading
            (not implemented yet) ("pec_csv").

    Returns:
        CellpyCell object (if successful, None if not).

    Examples:
        >>> # read an arbin .res file and create a cellpy object with
        >>> # populated summary and step-table:
        >>> c = cellpy.get("my_data.res", instrument="arbin_res", mass=1.14, area=2.12, loading=1.2, nom_cap=155.2)
        >>>
        >>> # load a cellpy-file:
        >>> c = cellpy.get("my_cellpy_file.clp")
        >>>
        >>> # load a txt-file exported from Maccor:
        >>> c = cellpy.get("my_data.txt", instrument="maccor_txt", model="one")
        >>>
        >>> # load a raw-file if it is newer than the corresponding cellpy-file,
        >>> # if not, load the cellpy-file:
        >>> c = cellpy.get("my_data.res", cellpy_file="my_data.clp")
        >>>
        >>> # load a file with a custom file-description:
        >>> c = cellpy.get("my_file.csv", instrument_file="my_instrument.yaml")
        >>>
        >>> # load three subsequent raw-files (of one cell) and merge them:
        >>> c = cellpy.get(["my_data_01.res", "my_data_02.res", "my_data_03.res"])
        >>>
        >>> # load a data set and get the summary charge and discharge capacities
        >>> # in Ah/g:
        >>> c = cellpy.get("my_data.res", units=dict(capacity="Ah"))
        >>>
        >>> # get an empty CellpyCell instance:
        >>> c = cellpy.get()  # or c = cellpy.get(initialize=True) if you want to initialize it.

    """

    # TODO: implement volume as parameter and 'volumetric' as nom_cap_specifics option.

    from cellpy import log

    db_readers = list(DB_READER_INSTRUMENTS)
    instruments_with_colliding_file_suffix = ["arbin_sql_h5"]

    step_kwargs = step_kwargs or {}
    summary_kwargs = summary_kwargs or {}
    load_cellpy_file = False
    logging_mode = "DEBUG" if testing else logging_mode
    log.setup_logging(
        default_level=logging_mode,
        testing=testing,
        custom_log_dir=custom_log_dir,
        default_json_path=custom_log_config_path,
    )
    logging.debug("-------running-get--------")
    cellpy_instance = CellpyCell(debug=debug, initialize=initialize)
    logging.debug("created CellpyCell instance")

    logging.debug(f"{cellpy_file=}")
    logging.debug(f"{filename=}")

    # used if all you want is an empty CellpyCell object
    if filename is None:
        if cellpy_file is None:
            logging.info("Running cellpy.get without a filename")
            logging.info("Returning an empty CellpyCell object.")
            cellpy_instance = _update_meta(
                cellpy_instance,
                cycle_mode=cycle_mode,
                mass=mass,
                nominal_capacity=nominal_capacity,
                nom_cap_specifics=nom_cap_specifics,
                area=area,
                loading=loading,
                estimate_area=estimate_area,
                units=units,
            )
            return cellpy_instance

        else:
            load_cellpy_file = True
            filename = internals.OtherPath(cellpy_file)

    if isinstance(filename, (list, tuple)):
        logging.debug("got a list or tuple of names")
        load_cellpy_file = False
    else:
        logging.debug("got a single name")
        logging.debug(f"{filename=}")
        filename = internals.OtherPath(filename)
        if (
            auto_pick_cellpy_format
            and instrument not in instruments_with_colliding_file_suffix
            and filename.suffix in [".h5", ".hdf5", ".cellpy", ".cpy"]
        ):
            load_cellpy_file = True

    if filename and cellpy_file and not load_cellpy_file:
        try:
            similar = cellpy_instance.check_file_ids(filename, cellpy_file)
            logging.debug("checked if the files were similar")
            if similar:
                load_cellpy_file = True
                filename = internals.OtherPath(cellpy_file)
        except Exception as e:
            logging.debug(f"Error during checking if similar: {e}")
            logging.debug("Setting load_cellpy_file to False")

    if load_cellpy_file:
        logging.info(f"Loading cellpy-file: {filename}")
        if kwargs.pop("post_processor_hook", None) is not None:
            logging.warning(
                "post_processor_hook is not allowed when loading cellpy-files"
            )

        cellpy_instance.load(filename, selector=selector, **kwargs)
        cellpy_instance = _update_meta(
            cellpy_instance,
            cycle_mode=cycle_mode,
            mass=mass,
            nominal_capacity=nominal_capacity,
            nom_cap_specifics=nom_cap_specifics,
            area=area,
            loading=loading,
            estimate_area=estimate_area,
            units=units,
        )
        return cellpy_instance

    logging.debug("Prepare for loading raw-file(s)")
    logging.debug("checking instrument and instrument_file")

    if instrument_file is not None:
        logging.debug(f"got instrument file {instrument_file=}")
        cellpy_instance.set_instrument(
            instrument="custom", instrument_file=instrument_file
        )

    elif instrument is not None:
        logging.debug(f"got instrument in stead of instrument file, {instrument=}")
        model = kwargs.pop("model", None)
        cellpy_instance.set_instrument(instrument=instrument, model=model, **kwargs)

    is_a_file = True
    if cellpy_instance.tester in db_readers:
        is_a_file = False

    logging.info(f"Loading raw-file: {filename}")
    cellpy_instance.from_raw(
        filename, is_a_file=is_a_file, refuse_copying=refuse_copying, **kwargs
    )

    if not cellpy_instance:
        print("Could not load file: check log!")
        print("Returning None")
        return

    # fix for allowing for setting nom_cap_specifics the "old" way:
    if nom_cap_specifics is None:
        nom_cap_specifics = summary_kwargs.pop("nom_cap_specifics", None)

    cellpy_instance = _update_meta(
        cellpy_instance,
        cycle_mode=cycle_mode,
        mass=mass,
        nominal_capacity=nominal_capacity,
        nom_cap_specifics=nom_cap_specifics,
        area=area,
        loading=loading,
        estimate_area=estimate_area,
        units=units,
    )

    if auto_summary:
        logging.info("Creating step table")
        cellpy_instance.make_step_table(**step_kwargs)
        logging.info("Creating summary data")
        cellpy_instance.make_summary(**summary_kwargs)

    logging.info("Created CellpyCell object")
    return cellpy_instance


def _update_meta(
    cellpy_instance,
    cycle_mode=None,
    mass=None,
    nominal_capacity=None,
    nom_cap_specifics=None,
    area=None,
    loading=None,
    estimate_area=None,
    units=None,
    volume=None,  # not implemented yet
):
    """Used by get to update metadata in the CellpyCell object."""
    # Note: this is a bit messy, but it is a quick fix for now.
    #       I will clean it up later.
    # Note: if you want to add more metadata or similar for use by the get function,
    #       please also add a property to the CellpyCell class (e.g. don't update
    #       the data object directly, especially if handling units).

    if cycle_mode is not None:
        logging.debug("Setting cycle mode")
        cellpy_instance.cycle_mode = cycle_mode

    if nom_cap_specifics is not None:
        logging.info(f"Setting nom_cap_specifics as given {nom_cap_specifics=}")
        cellpy_instance.nom_cap_specifics = nom_cap_specifics

    if units is not None:
        logging.debug(f"Updating units: {units}")
        cellpy_instance.cellpy_units.update(units)

    if mass is not None:
        logging.info(f"Setting mass: {mass}")
        cellpy_instance.mass = mass

    if nominal_capacity is not None:
        logging.info(f"Setting nominal capacity: {nominal_capacity}")
        if nom_cap_specifics is not None and not isinstance(
            nominal_capacity, numbers.Number
        ):
            logging.info(
                "Providing nominal capacity as string might override the given nom_cap_specifics"
            )
        cellpy_instance.nom_cap = nominal_capacity

    if area is not None:
        logging.debug(f"got area: {area}")
        cellpy_instance.active_electrode_area = area

    elif loading and estimate_area:
        logging.debug("-------------AREA-CALC----------------")
        logging.debug(f"got loading: {logging}")
        area = cellpy_instance.data.mass / loading
        logging.debug(
            f"calculating area from loading ({loading}) and mass ({cellpy_instance.data.mass}): {area}"
        )
        cellpy_instance.active_electrode_area = area

    else:
        logging.debug("using default area")

    if volume is not None:
        logging.debug(f"got volume: {volume}")
        logging.critical("Volume not implemented yet")

    return cellpy_instance


def instruments_dict():
    """
    Create a dictionary with the available instrument loaders.

    The dictionary keys are the instrument names and the values are lists of the available models.
    If no models are available, the list will be empty.

    Returns:
        dict: dictionary with the available instrument loaders.
    """
    instruments = dict()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, value in ds.instrument_configurations().items():
            instruments[name] = []
            instrument_models = value["__all__"].copy()
            instrument_models.remove("default")
            if len(instrument_models) > 0:
                instruments[name].extend(instrument_models)
    return instruments


def print_instruments():
    """Prints out the available instrument loaders and their models."""
    print(80 * "=")
    print("Implemented instrument loaders")
    print(80 * "=")
    for name, value in ds.instrument_configurations().items():
        print(name)
        instrument_models = value["__all__"].copy()
        instrument_models.remove("default")
        if len(instrument_models) > 0:
            model_text = "  models: "
            model_text += ", ".join(instrument_models)
            print(model_text)


