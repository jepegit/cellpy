from dataclasses import dataclass
import logging
import sqlite3
import pathlib
from pprint import pprint
import sqlalchemy as sa
import pandas as pd

import cellpy


DB_FILE_EXCEL = "cellpy_db.xlsx"
DB_FILE_SQLITE = "excel.db"
TABLE_NAME_EXCEL = "db_table"
TABLE_NAME_SQLITE = "cells"
HEADER_ROW = 0
COLUMNS_RENAMER = {
    "id": "pk",
    "batch": "comment_history",
    "cell": "name",
    "exists": "cell_exists",
    "group": "cell_group",
    "raw_file_names": "raw_data",
    "argument": "cell_spec",
}


@dataclass
class DbColsRenamer:
    cellpy_col: str = ""
    dtype: str = ""
    excel_col: str = ""
    db_col: str = ""


def create_column_names_from_prms():
    logging.debug(cellpy.prms.DbCols.keys())
    logging.debug("----")
    attrs = cellpy.prms.DbCols.keys()
    dtypes = cellpy.prms._db_cols_unit
    columns = []
    for attr in attrs:
        if attr in COLUMNS_RENAMER:
            db_col = COLUMNS_RENAMER[attr]
        else:
            db_col = attr
        col = DbColsRenamer(
            cellpy_col=attr,
            dtype=getattr(dtypes, attr),
            excel_col=getattr(cellpy.prms.DbCols, attr),
            db_col=db_col,
        )
        columns.append(col)
        logging.debug(col)
        logging.debug("----")
    return columns


def load_xlsx(db_file=DB_FILE_EXCEL, table_name=TABLE_NAME_EXCEL, header_row=HEADER_ROW):
    work_book = pd.ExcelFile(db_file, engine="openpyxl")
    sheet = work_book.parse(table_name, header=header_row, skiprows=[1])
    return sheet


def save_sqlite(sheet, out_file=DB_FILE_SQLITE, table_name=TABLE_NAME_SQLITE):
    uri = f"sqlite:///{out_file}"
    logging.debug(f"Saving to sqlite ({uri})...")
    engine = sa.create_engine(uri, echo=False)
    sheet.to_sql(table_name, con=engine, if_exists="replace")


def clean_up(df, columns):
    logging.debug("Cleaning up ...")
    logging.debug(" converting ...")

    final_columns = {}
    for col in columns:
        excel_col = col.excel_col
        cellpy_col = col.cellpy_col
        t = col.dtype
        db_col = col.db_col
        if excel_col not in df.columns:
            logging.debug(f"  {excel_col} not in df.columns")
            continue
        logging.debug(f"  {cellpy_col} = {excel_col} [{df[excel_col].dtype}]:({t}) --> ")
        if t == "int":
            df[excel_col] = df[excel_col].fillna(0)
            try:
                df[excel_col] = df[excel_col].str.replace(",", ".")
            except AttributeError:
                pass
            df[excel_col] = df[excel_col].astype("int")
        elif t == "float":
            df[excel_col] = df[excel_col].fillna(0)
            try:
                df[excel_col] = df[excel_col].str.replace(",", ".")
            except AttributeError:
                pass
            if col == "temperature":
                df[excel_col] = df[excel_col].replace("RT", 25)
            df[excel_col] = df[excel_col].astype("float")
        elif t == "str":
            df[excel_col] = df[excel_col].fillna("")
            df[excel_col] = df[excel_col].astype("str")
        logging.debug(f"[{df[excel_col].dtype}]")
        df = df.rename(columns={excel_col: db_col})
        final_columns[db_col] = cellpy_col
    logging.debug("Selecting...")
    df = df[final_columns.keys()]
    logging.debug("Renaming to cellpy names...")
    df = df.rename(columns=final_columns)
    return df


def check():
    print("Settings:")
    print(f"{cellpy.prms.Paths.db_path=}")
    print(f"{cellpy.prms.Paths.db_filename=}")

    print("But choosing:")
    db_exel_file = pathlib.Path("2022_Cell_Analysis_db_001.xlsx").resolve()
    print(f"{db_exel_file=}")

    columns = create_column_names_from_prms()
    df = load_xlsx(db_file=db_exel_file)
    df = clean_up(df, columns=columns)
    save_sqlite(df)


def run():
    db_exel_file = pathlib.Path(cellpy.prms.Paths.db_path) / cellpy.prms.Paths.db_filename
    db_sqlite_file = pathlib.Path(cellpy.prms.Paths.db_path) / DB_FILE_SQLITE
    columns = create_column_names_from_prms()
    df = load_xlsx(db_file=db_exel_file)
    df = clean_up(df, columns=columns)
    save_sqlite(df, out_file=db_sqlite_file)


def main():
    db_exel_file = pathlib.Path(sys.argv[1])
    if not db_exel_file.exists():
        print(f"File not found: {db_exel_file}")
        sys.exit(1)
    db_sqlite_file = pathlib.Path(cellpy.prms.Paths.db_path) / DB_FILE_SQLITE
    columns = create_column_names_from_prms()
    df = load_xlsx(db_file=db_exel_file)
    df = clean_up(df, columns=columns)
    save_sqlite(df, out_file=db_sqlite_file)


if __name__ == "__main__":
    main()

