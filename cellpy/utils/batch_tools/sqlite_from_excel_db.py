from dataclasses import dataclass
import logging
import sqlite3
import pathlib
from pprint import pprint
import sqlalchemy as sa
import pandas as pd

import cellpy
from cellpy import prms
from cellpy.parameters.internal_settings import (
    TABLE_NAME_SQLITE,
    COLUMNS_RENAMER,
)

DB_FILE_EXCEL = prms.Paths.db_filename
DB_FILE_SQLITE = prms.Db.db_file_sqlite
TABLE_NAME_EXCEL = prms.Db.db_table_name
HEADER_ROW = prms.Db.db_header_row
UNIT_ROW = prms.Db.db_unit_row


@dataclass
class DbColsRenamer:
    cellpy_col: str = ""
    dtype: str = ""
    excel_col: str = ""
    db_col: str = ""


def create_column_names_from_prms():
    """Create a list of DbColsRenamer objects from the cellpy.prms.DbCols object."""
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


def load_xlsx(
    db_file=DB_FILE_EXCEL,
    table_name=TABLE_NAME_EXCEL,
    header_row=HEADER_ROW,
    unit_row=UNIT_ROW,
):
    """Load the Excel file and return a pandas dataframe."""
    work_book = pd.ExcelFile(db_file, engine="openpyxl")
    sheet = work_book.parse(table_name, header=header_row, skiprows=[unit_row])
    return sheet


def save_sqlite(
    sheet, out_file=DB_FILE_SQLITE, table_name=TABLE_NAME_SQLITE, set_index=False
):
    """Save the pandas dataframe to a sqlite database."""
    uri = f"sqlite:///{out_file}"
    logging.debug(f"Saving to sqlite ({uri})...")
    engine = sa.create_engine(uri, echo=False)
    if set_index:
        sheet = sheet.set_index(COLUMNS_RENAMER["id"])
    sheet.to_sql(table_name, con=engine, if_exists="replace")


def clean_up(df, columns):
    """Clean up the dataframe and return using 'proper cellpy headers'."""
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
        logging.debug(
            f"  {cellpy_col} = {excel_col} [{df[excel_col].dtype}]:({t}) --> "
        )
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
        final_columns[
            db_col
        ] = db_col  # modify this if you want to rename columns again
    logging.debug("Selecting...")
    df = df[final_columns.keys()]
    logging.debug("Renaming to cellpy names...")
    df = df.rename(columns=final_columns)
    return df


def run():
    db_exel_file = (
        pathlib.Path(cellpy.prms.Paths.db_path) / cellpy.prms.Paths.db_filename
    )
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


def _check():
    print("Settings:")
    print(f"{cellpy.prms.Paths.db_path=}")
    print(f"{cellpy.prms.Paths.db_filename=}")

    print("But choosing:")
    db_exel_file = pathlib.Path("2022_Cell_Analysis_db_001.xlsx").resolve()
    print(f"{db_exel_file=}")

    columns = create_column_names_from_prms()
    df = load_xlsx(db_file=db_exel_file)
    df = clean_up(df, columns=columns)
    print("cleaned up:")
    print(df.columns)
    save_sqlite(df)


if __name__ == "__main__":
    main()
