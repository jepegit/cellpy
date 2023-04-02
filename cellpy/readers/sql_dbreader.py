import logging
import os
import pathlib
import re
import tempfile
import time
import warnings
from dataclasses import asdict
from datetime import datetime

import numpy as np
import pandas as pd
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import DateTime


from cellpy.parameters import prms

# logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Cell(Base):
    __tablename__ = "cells"
    pk: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    label: Mapped[str] = mapped_column()
    cell_exists: Mapped[str] = Column(Boolean)
    cell_group: Mapped[str] = Column(String)
    raw_data: Mapped[List["RawData"]] = relationship(back_populates="cell", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Cell(pk={self.pk!r}, name={self.name!r}, label={self.label!r})"


class RawData(Base):
    __tablename__ = "raw_data"
    pk: Mapped[int] = mapped_column(primary_key=True)
    cell_pk: Mapped[int] = mapped_column(ForeignKey("cells.pk"))
    cell: Mapped["Cell"] = relationship(back_populates="raw_data")
    is_file: Mapped[bool] = mapped_column()
    name: Mapped[str] = mapped_column()

    def __repr__(self) -> str:
        return f"RawData(pk={self.pk!r}, name={self.name!r}, cell={self.cell!r})"


class SQLReader:
    def __init__(self, use_mapping_from_prms=False):
        if use_mapping_from_prms:
            warnings.warn("Using mapping from prms is not fully implemented yet.")
            self.cell_table = _mapping_from_config()
        else:
            self.cell_table = Cell()
        self.raw_data_table = RawData()
        self.engine = None

    def __str__(self):
        txt = f"SQLReader:\n {self.cell_table}\n {self.raw_data_table}\n"
        return txt

    def open_db(self, db_path=None, echo=False):
        ...

    def save_db(self, db_path=None, echo=False):
        ...

    def create_db(self, db_path="sqlite://", db_filename=None, echo=False):
        self.engine = create_engine(db_path, echo=echo)
        Base.metadata.create_all(self.engine)

    def create_mock_data(self):
        with Session(self.engine) as session:
            for j in range(10):
                raw_data = []
                for k in range(3):
                    r = RawData(name=f"test_{j:02}_{k:02}", is_file=True)
                    raw_data.append(r)
                cell = Cell(
                    name=f"test_{j:02}", label=f"my-test{j:02}", cell_exists=True, cell_group=f"first",
                    raw_data=raw_data,
                )
                session.add(cell)
            session.commit()

    def get_mock_data(self):
        session = Session(self.engine)
        stmt = select(Cell).where(Cell.name.in_(["test"]))
        for cell in session.scalars(stmt):
            print(cell)

    @staticmethod
    def _parse_argument_str(argument_str: str) -> dict:
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


def check_sql_reader():
    reader = SQLReader()
    reader.create_db(echo=True)
    reader.create_mock_data()
    reader.get_mock_data()


if __name__ == "__main__":
    check_sql_reader()
