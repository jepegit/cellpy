import logging
import os
import pathlib
import re
import tempfile
import time
import warnings
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime

import numpy as np
import pandas as pd
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import select
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy.ext.automap import automap_base

import cellpy
from cellpy.parameters.internal_settings import (
    ATTRS_TO_IMPORT_FROM_EXCEL_SQLITE,
BATCH_ATTRS_TO_IMPORT_FROM_EXCEL_SQLITE,
    COLUMNS_RENAMER,
    TABLE_NAME_SQLITE,
)

from cellpy.parameters import prms
from cellpy.readers.core import BaseDbReader

# raise NotImplementedError("This module is not yet implemented")


# ----------------- USED WHEN CONVERTING FROM EXCEL -----------------
DB_FILE_EXCEL = prms.Paths.db_filename
DB_FILE_SQLITE = prms.Db.db_file_sqlite
TABLE_NAME_EXCEL = prms.Db.db_table_name
HEADER_ROW = prms.Db.db_header_row
UNIT_ROW = prms.Db.db_unit_row

# ------------------- USED BY NEW CELLPY DB --------------------------
DB_URI = f"sqlite:///cellpy.db"


class Base(DeclarativeBase):
    pass


batch_cell_association_table = Table(
    "batch_cell_association_table",
    Base.metadata,
    Column("batches_pk", ForeignKey("batches.pk"), primary_key=True),
    Column("cells_pk", ForeignKey("cells.pk"), primary_key=True),
)


class Cell(Base):
    __tablename__ = "cells"
    pk: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()  # cell_name
    test_date: Mapped[Optional[str]] = mapped_column()
    label: Mapped[Optional[str]] = mapped_column()  # label
    project: Mapped[Optional[str]] = mapped_column()  # project
    cell_group: Mapped[Optional[str]] = mapped_column()  # cell_group
    cellpy_file_name: Mapped[Optional[str]] = mapped_column()  # cellpy_file_name
    instrument: Mapped[Optional[str]] = mapped_column()  # instrument
    channel: Mapped[Optional[str]] = mapped_column()  # channel
    cell_type: Mapped[Optional[str]] = mapped_column()  # cell_type
    cell_design: Mapped[Optional[str]] = mapped_column()  # cell_design
    separator: Mapped[Optional[str]] = mapped_column()  # separator
    electrolyte: Mapped[Optional[str]] = mapped_column()  # electrolyte
    experiment_type: Mapped[Optional[str]] = mapped_column()  # experiment_type
    mass_active: Mapped[Optional[float]] = mapped_column()  # active_material
    area: Mapped[Optional[float]] = mapped_column()  # area
    mass_total: Mapped[Optional[float]] = mapped_column()  # total_material
    loading_active: Mapped[Optional[float]] = mapped_column()  # loading
    nominal_capacity: Mapped[Optional[float]] = mapped_column()  # nom_cap
    comment_slurry: Mapped[Optional[str]] = mapped_column()  # comment_slurry
    comment_cell: Mapped[Optional[str]] = mapped_column()  # comment_cell
    comment_general: Mapped[Optional[str]] = mapped_column()  # comment_general
    comment_history: Mapped[
        Optional[str]
    ] = mapped_column()  # div information from legacy Excel file
    selected: Mapped[Optional[bool]] = mapped_column()  # selected
    freeze: Mapped[Optional[bool]] = mapped_column()  # freeze
    argument: Mapped[Optional[str]] = mapped_column()  # argument
    cell_exists: Mapped[Optional[bool]] = mapped_column()  # cell_exists
    active_material_mass_fraction: Mapped[Optional[float]] = mapped_column()
    pasting_thickness: Mapped[Optional[str]] = mapped_column()
    solvent_solid_ratio: Mapped[Optional[str]] = mapped_column()
    schedule: Mapped[Optional[str]] = mapped_column()
    inactive_additive_mass: Mapped[Optional[float]] = mapped_column()
    temperature: Mapped[Optional[float]] = mapped_column()
    formation: Mapped[Optional[str]] = mapped_column()
    material_class: Mapped[Optional[str]] = mapped_column()
    material_label: Mapped[Optional[str]] = mapped_column()
    material_group_label: Mapped[Optional[str]] = mapped_column()
    material_sub_label: Mapped[Optional[str]] = mapped_column()
    material_solvent: Mapped[Optional[str]] = mapped_column()
    material_pre_processing: Mapped[Optional[str]] = mapped_column()
    material_surface_processing: Mapped[Optional[str]] = mapped_column()
    raw_data: Mapped[List["RawData"]] = relationship(
        back_populates="cell", cascade="all, delete-orphan"
    )
    batches: Mapped[Optional[List["Batch"]]] = relationship(
        secondary=batch_cell_association_table, back_populates="cells"
    )

    def __repr__(self) -> str:
        return (
            f"Cell(pk={self.pk!r}, name={self.name!r}, "
            f"label={self.label!r}, project={self.project!r}, "
            f"cell_group={self.cell_group!r}, cellpy_file_name={self.cellpy_file_name!r}, "
            f"instrument={self.instrument!r}, cell_type={self.cell_type!r}, "
            f"experiment_type={self.experiment_type!r}, mass_active={self.mass_active!r}, "
            f"area={self.area!r}, mass_total={self.mass_total!r}, "
            f"loading_active={self.loading_active!r}, "
            f"nominal_capacity={self.nominal_capacity!r}, comment_slurry={self.comment_slurry!r}, "
            f"comment_cell={self.comment_cell!r}, comment_general={self.comment_general!r}, "
            f"comment_history={self.comment_history!r}, "
            f"selected={self.selected!r}, freeze={self.freeze!r}, argument={self.argument!r}, "
            f"cell_exists={self.cell_exists!r}, raw_data={self.raw_data!r}, batches={self.batches!r}"
        )

    def __str__(self) -> str:
        return f"cell: '{self.name}' (#{self.pk})"


class RawData(Base):
    __tablename__ = "raw_data"
    pk: Mapped[int] = mapped_column(primary_key=True)
    cell_pk: Mapped[int] = mapped_column(ForeignKey("cells.pk"))
    cell: Mapped["Cell"] = relationship(back_populates="raw_data")
    is_file: Mapped[bool] = mapped_column()
    name: Mapped[str] = mapped_column()

    def __repr__(self) -> str:
        return f"RawData(pk={self.pk!r}, name={self.name!r}, cell={self.cell_pk!r})"


class Batch(Base):
    __tablename__ = "batches"
    pk: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    comment: Mapped[Optional[str]] = mapped_column()
    cells: Mapped[List["Cell"]] = relationship(
        secondary=batch_cell_association_table, back_populates="batches"
    )

    def __repr__(self) -> str:
        return f"Batch(pk={self.pk!r}, name={self.name!r}, cells={self.cells!r})"

    def __str__(self) -> str:
        return f"batch: '{self.name}' (#{self.pk})"


class SQLReader(BaseDbReader):
    def __init__(self, db_connection: str = None, batch: str = None, **kwargs) -> None:
        self.cell_table = Cell()
        self.raw_data_table = RawData()
        self.batch_table = Batch()
        self.engine = None
        self.other_engine = None
        self.old_cell_table = None

    def __str__(self) -> str:
        txt = f"SQLReader:\n {self.cell_table}\n {self.raw_data_table}\n  {self.batch_table}\n"
        return txt

    def create_db(self, db_uri: str = DB_URI, echo: bool = False, **kwargs) -> None:
        self.engine = create_engine(db_uri, echo=echo, **kwargs)
        Base.metadata.create_all(self.engine)

    def open_db(self, db_uri: str = DB_URI, echo: bool = False, **kwargs) -> None:
        self.create_db(db_uri, echo, **kwargs)

    def select_batch(self, batch_name: str) -> List[int]:
        with self.engine.connect() as conn:
            stmt = select(self.cell_table).where(
                self.cell_table.batches.any(name=batch_name)
            )
            result = conn.execute(stmt)
            return [row.pk for row in result]

    def get_mass(self, pk: int) -> float:
        pass

    def get_area(self, pk: int) -> float:
        pass

    def get_loading(self, pk: int) -> float:
        pass

    def get_nom_cap(self, pk: int) -> float:
        pass

    def get_total_mass(self, pk: int) -> float:
        pass

    def get_cell_name(self, pk: int) -> str:
        pass

    def get_cell_type(self, pk: int) -> str:
        pass

    def get_label(self, pk: int) -> str:
        pass

    def get_comment(self, pk: int) -> str:
        pass

    def get_group(self, pk: int) -> str:
        pass

    def get_args(self, pk: int) -> dict:
        pass

    def get_experiment_type(self, pk: int) -> str:
        pass

    def get_instrument(self, pk: int) -> str:
        pass

    def inspect_hd5f_fixed(self, pk: int) -> int:
        pass

    def load_excel_sqlite(self, db_path: str, echo: bool = False) -> None:
        """Load an old sqlite cellpy database created from an Excel file.

        You can use the cellpy.utils.batch_tools.sqlite_from_excel.run() function to
        convert an Excel file to a sqlite database.

        """
        assert pathlib.Path(db_path).is_file()
        db_path = f"sqlite:///{db_path}"
        self.other_engine = create_engine(db_path, echo=echo)
        self.old_cell_table = Table(
            "cells", MetaData(), autoload_with=self.other_engine
        )

    def view_old_excel_sqlite_table_columns(self) -> None:
        if self.old_cell_table is None:
            raise ValueError("No old db loaded - use load_old_db() first")

        print("class Cell(Base):")
        print("    __tablename__ = 'cells'")
        for col in self.old_cell_table.c:
            n = col.name
            t = f"    {n}: Mapped[Optional[str]] = mapped_column()"
            print(t)

    def import_cells_from_excel_sqlite(self, allow_duplicates: bool = False, allow_updates: bool = True, process_batches=True, clear=False) -> None:
        """Import cells from old db to new db.

        Args:
            allow_duplicates: will not import if cell already exists in new db.
            allow_updates: will update existing cells in new db.
            process_batches: will process batches (if any) in old db.
            clear: will clear all rows in new db before importing.

        Returns:
            None
        """

        if self.old_cell_table is None:
            raise ValueError("No old db loaded - use load_old_db() first")
        old_session = Session(self.other_engine)
        new_session = Session(self.engine)
        missing_attributes = []
        batches = defaultdict(list)

        if clear:
            confirmation = input("Are you sure you want to clear the new db? (y/n)")
            if confirmation != "y":
                print("Aborting import without clearing new db.")
                return
            new_session.query(Batch).delete()
            new_session.commit()
            new_session.query(batch_cell_association_table).delete()
            new_session.commit()
            new_session.query(RawData).delete()
            new_session.commit()
            new_session.query(Cell).delete()
            new_session.commit()

        for i, row in enumerate(old_session.query(self.old_cell_table).all()):
            if not clear:
                old_cell = new_session.query(Cell).filter(Cell.name == row.name).first()
                if old_cell:
                    if not allow_updates and not allow_duplicates:
                        logging.debug(f"{i:05d} skipping (already exists - updates or duplicates not allowed):{row.name}")
                        continue
                    elif allow_updates and not allow_duplicates:
                        cell = old_cell
                    else:
                        cell = Cell()
                else:
                    cell = Cell()
            else:
                cell = Cell()

            logging.debug(f"{i:05d} importing: {row.name}")
            for attr in ATTRS_TO_IMPORT_FROM_EXCEL_SQLITE:
                row_attr = getattr(row, attr, None)
                if row_attr is not None:
                    setattr(cell, attr, row_attr)
                else:
                    missing_attributes.append(attr)

            new_session.add(cell)
            new_session.commit()

            if process_batches:
                for b in BATCH_ATTRS_TO_IMPORT_FROM_EXCEL_SQLITE:
                    b_name = getattr(row, b, None)
                    if b_name:
                        if cell.project is not None:
                            batch_name = f"{b}_{cell.project}_{b_name}"
                        else:
                            batch_name = f"{b}_NN_{b_name}"
                        batches[batch_name].append(cell.pk)

        if process_batches:
            for batch_name, cell_pks in batches.items():
                if not clear:
                    old_batch = new_session.query(Batch).filter(Batch.name == batch_name).first()
                    if old_batch:
                        if not allow_updates and not allow_duplicates:
                            logging.debug(f"skipping batch (already exists - updates or duplicates not allowed):{batch_name}")
                            continue
                        elif allow_updates and not allow_duplicates:
                            batch = old_batch
                            old_batch.comment = "batch imported from old db"
                        else:
                            batch = Batch(name=batch_name, comment="batch imported from old db")
                    else:
                        batch = Batch(name=batch_name, comment="batch imported from old db")
                else:
                    batch = Batch(name=batch_name, comment="batch imported from old db")
                cell_pks = set(cell_pks)
                for pk in cell_pks:
                    batch.cells.append(new_session.get(Cell, pk))
                new_session.add(batch)
        new_session.commit()
        old_session.close()
        new_session.close()
        if missing_attributes:
            logging.debug("missing attributes:")
            logging.debug(set(missing_attributes))

    @staticmethod
    def _parse_argument_str(argument_str: str) -> Optional[dict]:
        # the argument str must be on the form:
        # "keyword-1=value-1;keyword-2=value2"
        if argument_str is None:
            return
        sep = ";"
        parts = [part.strip() for part in argument_str.split(sep=sep)]
        sep = "="
        arguments = {}
        for p in parts:
            k, v = p.split(sep=sep)
            arguments[k.strip()] = v.strip()
        return arguments

    @staticmethod
    def _extract_date_from_cell_name(
        cell_name, strf="%Y%m%d", regexp=None, splitter="_", position=0, start=0, end=12
    ):
        """Extract date given a cell name (or filename).

        Uses regexp if given to find date txt, if not it uses splitter if splitter is not None or "",
        else start-stop. Uses strf to parse for date in date txt.
        if regexp is "auto", regexp is interpreted from strf

        Args:
            cell_name (str): extract date from.
            strf (str): datetime string formatter.
            regexp (str | "auto"): regular expression.
            splitter (str): split parts into sub-parts.
            position (int): selected sub-part.
            start (int): number of first character in the date part.
            end (int): number of last character in the date part.

        Returns:
            datetime.datetime object
        """

        if regexp is not None:
            if regexp == "auto":
                year_r = r"%Y"
                month_r = r"%m"
                day_r = r"%d"

                regexp = strf.replace("\\", "\\\\").replace("-", r"\-")
                regexp = (
                    regexp.replace(year_r, "[0-9]{4}")
                    .replace(month_r, "[0-9]{2}")
                    .replace(day_r, "[0-9]{2}")
                )
                regexp = f"({regexp})"

            m = re.search(regexp, cell_name)
            datestr = m[0]

        elif splitter:
            datestr = cell_name.split(splitter)[position]

        else:
            datestr = cell_name[start:end]

        try:
            date = datetime.strptime(datestr, strf)
        except ValueError as e:
            logging.debug(e)
            return None

        return date

    def extract_date_from_cell_name(self, force=False):
        ...


def check_import_cells_from_excel_sqlite(cellpy_db_uri, sqlite_path):
    reader = SQLReader()
    reader.create_db(cellpy_db_uri, echo=False)
    reader.load_excel_sqlite(sqlite_path)
    # 2023.04.06 missing in test excel file:
    #   {'channel', 'cell_design', 'nominal_capacity', 'loading_active', 'experiment_type'}
    reader.import_cells_from_excel_sqlite()


def check():
    cellpy_db_file = r"C:\scripting\cellpy\testdata\db\cellpy.db"
    sqlite_path = r"C:\scripting\cellpy\testdata\db\excel.db"
    cellpy_db_uri = f"sqlite:///{cellpy_db_file}"

    check_import_cells_from_excel_sqlite(cellpy_db_uri, sqlite_path)
    reader = SQLReader()
    reader.open_db(cellpy_db_uri, echo=False)
    with Session(reader.engine) as session:
        statement = select(Cell).where(Cell.name.contains("test")).where(Cell.cell_group == 2)
        result = session.execute(statement)
        for cells in result.all():
            cell = cells[0]
            print(cell.comment_history)


# TODO: add processing of batches from excel db
# TODO: add method (use find-files) to find files and add to db
# TODO: also add cellpy_filename
# TODO:


if __name__ == "__main__":
    check()
