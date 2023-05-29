import json
import logging
import os
import pathlib
import platform
import shutil
import tempfile
import warnings
from abc import ABC

import pandas as pd

from cellpy.exceptions import UnderDefined
from cellpy.parameters import prms
from cellpy.parameters.internal_settings import (
    get_headers_journal,
    keys_journal_session,
)
from cellpy.parameters.legacy.update_headers import (
    headers_journal_v0 as hdr_journal_old,
)
from cellpy.readers import dbreader
from cellpy.utils.batch_tools.batch_core import BaseJournal
from cellpy.utils.batch_tools.engines import simple_db_engine, sql_db_engine

hdr_journal = get_headers_journal()

trans_dict = {}
missing_keys = []
for key in hdr_journal:
    if key in hdr_journal_old:
        trans_dict[hdr_journal_old[key]] = hdr_journal[key]
    else:
        missing_keys.append(key)


class LabJournal(BaseJournal, ABC):
    def __init__(self, db_reader="default", engine=None, batch_col=None, **kwargs):
        """Journal for selected batch.

        The journal contains pages (pandas.DataFrame) with prms for
        each cell (one cell pr row).

        Args:
            db_reader: either default (a simple excel reader already
                implemented in cellpy) or other db readers that implement
                the needed API.
            engine: defaults to simple_db_engine for parsing db using the
                db_reader
                    self.pages = simple_db_engine(
                        self.db_reader, id_keys, **kwargs
                    )
            batch_col: the column name for the batch column in the db (used by simple_db_engine).
            **kwargs: passed to the db_reader
        """

        super().__init__()
        if db_reader is None:
            return

        if isinstance(db_reader, str):
            if db_reader == "off":
                self.db_reader = None
                return
            if db_reader == "default":
                db_reader = prms.Db.db_type
            if db_reader == "simple_excel_reader":
                self.db_reader = dbreader.Reader()
                self.engine = simple_db_engine
            elif db_reader == "sql_db_reader":
                raise NotImplementedError("sql_db_reader is not implemented yet")
                # self.db_reader = sql_dbreader.SqlReader()
                # self.engine = sql_db_engine
            else:
                raise UnderDefined(f"The db-reader '{db_reader}' is not supported")
        else:
            logging.debug(f"Remark! db_reader: {db_reader}")
            self.db_reader = db_reader

        if engine is None:
            self.engine = simple_db_engine

        self.batch_col = batch_col or "b01"

    def _repr_html_(self):
        txt = f"<h2>LabJournal-object</h2> id={hex(id(self))}"
        txt += "<h3>Main attributes</h3>"
        txt += f"""
        <table>
            <thead>
                <tr>
                    <th>Attribute</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><b>name</b></td><td>{self.name}</td></tr>
                <tr><td><b>project</b></td><td>{self.project}</td></tr>
                <tr><td><b>file_name</b></td><td>{self.file_name}</td></tr>
                <tr><td><b>db_reader</b></td><td>{self.db_reader}</td></tr>
        """
        if self.db_reader == "default":
            txt += f"<tr><td><b>batch_col</b></td><td>{self.batch_col}</td></tr>"
        txt += f"""
                <tr><td><b>time_stamp</b></td><td>{self.time_stamp}</td></tr>
                <tr><td><b>project_dir</b></td><td>{self.project_dir}</td></tr>
                <tr><td><b>raw_dir</b></td><td>{self.raw_dir}</td></tr>
                <tr><td><b>batch_dir</b></td><td>{self.batch_dir}</td></tr>
            </tbody>
        </table>
        """
        txt += "<h3>Session info</h3>"
        for key in self.session:
            txt += f"<p><b>{key}</b>: {self.session[key]}</p>"

        txt += "<h3>Pages</h3>"
        try:
            txt += self.pages._repr_html_()  # pylint: disable=protected-access
        except AttributeError:
            txt += "<p><b>pages</b><br> not found!</p>"
        except ValueError:
            txt += "<p><b>pages</b><br> not readable!</p>"
        return txt

    def _check_file_name(self, file_name, to_project_folder=False):
        if file_name is None:
            if not self.file_name:
                self.generate_file_name()
            file_name = pathlib.Path(self.file_name)

        else:
            file_name = pathlib.Path(file_name)
        if to_project_folder:
            file_name = file_name.with_suffix(".json").name
            project_dir = pathlib.Path(self.project_dir)

            file_name = project_dir / file_name
        self.file_name = file_name  # updates object (maybe not smart)
        return file_name

    def from_db(self, project=None, name=None, batch_col=None, **kwargs):
        """populate journal from db.

        Args:
            project (str): project name.
            name (str): experiment name.
            batch_col (int): batch column.

        **kwargs: sent to engine.

        simple_db-engine -> filefinder.search_for_files:
            run_name(str): run-file identification.
            raw_extension(str): optional, extension of run-files (without the '.').
            cellpy_file_extension(str): optional, extension for cellpy files
                (without the '.').
            raw_file_dir(path): optional, directory where to look for run-files
                (default: read prm-file)
            cellpy_file_dir(path): optional, directory where to look for
                cellpy-files (default: read prm-file)
            prm_filename(path): optional parameter file can be given.
            file_name_format(str): format of raw-file names or a glob pattern
                (default: YYYYMMDD_[name]EEE_CC_TT_RR) [not finished yet].
            reg_exp(str): use regular expression instead (defaults to None) [not finished yet].
            sub_folders (bool): perform search also in sub-folders.
            file_list (list of str): perform the search within a given list
                of filenames instead of searching the folder(s). The list should
                not contain the full filepath (only the actual file names). If
                you want to provide the full path, you will have to modify the
                file_name_format or reg_exp accordingly.
            pre_path (path or str): path to prepend the list of files selected
                 from the file_list.

        Returns:
            None
        """
        logging.debug("creating journal from db")
        if batch_col is None:
            batch_col = self.batch_col
        if project is not None:
            self.project = project
        if name is None:
            name = self.name
        else:
            self.name = name
        logging.debug(f"batch_name, batch_col: {name}, {batch_col}")

        if self.db_reader is not None:
            if isinstance(self.db_reader, dbreader.Reader):  # Simple excel-db
                id_keys = self.db_reader.select_batch(name, batch_col)
                logging.debug(f"id_keys: {id_keys}")

                self.pages = self.engine(self.db_reader, id_keys, **kwargs)
            else:
                logging.debug(
                    "creating journal pages using advanced reader methods (not simple excel-db)"
                )
                self.pages = self.engine(self.db_reader, batch_name=name, **kwargs)

            if self.pages.empty:
                logging.critical(
                    f"EMPTY JOURNAL: are you sure you have provided correct input to batch?"
                )
                logging.critical(f"name: {name}")
                logging.critical(f"project: {self.project}")
                logging.critical(f"batch_col: {batch_col}")
        else:
            logging.debug("creating empty journal pages")
            self.pages = pd.DataFrame()

        self.generate_empty_session()
        self.generate_folder_names()
        self.paginate()

    def generate_empty_session(self):
        self.session = {}
        for item in keys_journal_session:
            self.session[item] = None

    @staticmethod
    def _fix_cellpy_paths(p):
        logging.debug("_fix_cellpy_paths does not work with OtherPaths yet")
        # if platform.system() != "Windows":
        #     if p.find("\\") >= 0:
        #         # convert from win to posix
        #         p = pathlib.PureWindowsPath(p)
        # else:
        #     if p.find("/") >= 0:
        #         # convert from posix to win
        #         p = pathlib.PurePosixPath(p)
        # p = pathlib.Path(p)
        return p

    @classmethod
    def read_journal_jason_file(cls, file_name, **kwargs):
        logging.debug(f"json loader starting on {file_name}")
        with open(file_name, "r") as infile:
            top_level_dict = json.load(infile)
        pages_dict = top_level_dict["info_df"]
        meta = top_level_dict["metadata"]
        session = top_level_dict.get("session", None)
        pages = pd.DataFrame(pages_dict)
        if pages.empty:
            logging.critical("could not find any pages in the journal")
            raise UnderDefined

        pages = cls._clean_pages(pages)

        if session is None:
            logging.debug(f"no session - generating empty one")
            session = dict()

        session, pages = cls._clean_session(session, pages)

        return pages, meta, session

    @classmethod
    def read_journal_excel_file(cls, file_name, **kwargs):
        sheet_names = {"meta": "meta", "pages": "pages", "session": "session"}
        project = kwargs.pop("project", "NaN")
        name = kwargs.pop("batch", pathlib.Path(file_name).stem)
        _meta = {
            "name": name,
            "project": project,
            "project_dir": pathlib.Path("."),
            "batch_dir": pathlib.Path("."),
            "raw_dir": pathlib.Path("."),
        }
        logging.debug(f"xlsx loader starting on {file_name}")

        meta_sheet_name = sheet_names["meta"]  # not tested yet
        pages_sheet_name = sheet_names["pages"]
        session_sheet_name = sheet_names["session"]  # not tested yet

        temporary_directory = tempfile.mkdtemp()
        temporary_file_name = shutil.copy(file_name, temporary_directory)
        try:
            pages = pd.read_excel(
                temporary_file_name, engine="openpyxl", sheet_name=pages_sheet_name
            )
        except KeyError:
            print(f"Worksheet '{pages_sheet_name}' does not exist.")
            return None

        try:
            session = pd.read_excel(
                temporary_file_name,
                sheet_name=session_sheet_name,
                engine="openpyxl",
                header=[0, 1],
            )
        except (KeyError, ValueError):
            print(f"Worksheet '{session_sheet_name}' does not exist.")
            session = None

        try:
            meta = pd.read_excel(
                temporary_file_name, sheet_name=meta_sheet_name, engine="openpyxl"
            )

        except (KeyError, ValueError):
            print(f"Worksheet '{meta_sheet_name}' does not exist.")
            meta = None

        if pages.empty:
            logging.critical("could not find any pages in the journal")
            raise UnderDefined
        pages = cls._clean_pages(pages)
        pages = pages.set_index(hdr_journal.filename)

        if meta is None:
            meta = _meta
        else:
            meta = cls._unpack_meta(meta) or _meta

        if session is None:
            logging.debug(f"no session - generating empty one")
            session = dict()
        else:
            session = cls._unpack_session(session)

        session, pages = cls._clean_session(session, pages)

        return pages, meta, session

    @classmethod
    def _unpack_session(cls, session):
        try:
            bcn2 = {
                l: list(sb["cycle_index"].values)
                for l, sb in session["bad_cycles"].groupby("cell_name")
            }
        except KeyError:
            bcn2 = []

        try:
            bc2 = list(session["bad_cells"]["cell_name"].dropna().values.flatten())
        except KeyError:
            bc2 = []

        try:
            s2 = list(session["starred"]["cell_name"].dropna().values.flatten())
        except KeyError:
            s2 = []

        try:
            n2 = list(session["notes"]["txt"].dropna().values.flatten())
        except KeyError:
            n2 = []

        session = {"bad_cycles": bcn2, "bad_cells": bc2, "starred": s2, "notes": n2}

        return session

    @classmethod
    def _unpack_meta(cls, meta):
        try:
            meta = meta.loc[:, ["parameter", "value"]]
        except KeyError:
            return
        meta = meta.set_index("parameter")
        return meta.to_dict()["value"]

    @classmethod
    def _clean_session(cls, session, pages):
        # include steps for cleaning up the session dict here
        if not session:
            logging.critical("no session found in your journal file")
        for item in keys_journal_session:
            session[item] = session.get(item, None)

        return session, pages

    @classmethod
    def _clean_pages(cls, pages: pd.DataFrame) -> pd.DataFrame:
        import ast

        logging.debug("removing empty rows")
        pages = pages.dropna(how="all")
        logging.debug("checking path-names")
        try:
            p = pages[hdr_journal.raw_file_names]
            new_p = []
            for f in p:
                if isinstance(f, str):
                    try:
                        new_f = ast.literal_eval(f"'{f}'")
                        if isinstance(new_f, list):
                            f = new_f
                    except Exception as e:
                        warnings.warn(e)
                        warnings.warn(f"Could not evaluate {f}")

                new_p.append(f)
            pages[hdr_journal.raw_file_names] = new_p

        except KeyError:
            print(
                "Tried but failed in converting raw_file_names into an appropriate list"
            )
        try:
            pages[hdr_journal.cellpy_file_name] = pages[
                hdr_journal.cellpy_file_name
            ].apply(cls._fix_cellpy_paths)
        except KeyError:
            # assumes it is an old type journal file
            print(f"The key '{hdr_journal.cellpy_file_name}' is missing!")
            print(f"Assumes that this is an old-type journal file.")
            try:
                pages.rename(columns=trans_dict, inplace=True)
                pages[hdr_journal.cellpy_file_name] = pages[
                    hdr_journal.cellpy_file_name
                ].apply(cls._fix_cellpy_paths)
                logging.warning("old journal file - updating")
            except KeyError:
                print("Error! Could still not parse the pages.")
                print(f"Missing key: {hdr_journal.cellpy_file_name}")
                pages[hdr_journal.cellpy_file_name] = None

        # only keep selected cells if keep column exists
        if "keep" in pages.columns:
            logging.debug("Journal contains 'keep' - selecting only 'keep' > 0.")
            pages = pages.loc[pages.keep > 0, :]

        for column_name in missing_keys:
            if column_name not in pages.columns:
                logging.debug(f"wrong journal format - missing: {column_name}")
                pages[column_name] = None

        for column_name in hdr_journal:
            if column_name not in pages.columns:
                if column_name != hdr_journal.filename:
                    pages[column_name] = None

        return pages

    def from_file(self, file_name=None, paginate=True, **kwargs):
        """Loads a DataFrame with all the needed info about the experiment"""
        file_name = self._check_file_name(file_name)
        logging.info(f"reading {file_name}")
        if pathlib.Path(file_name).suffix.lower() == ".xlsx":
            file_loader = self.read_journal_excel_file
        else:
            file_loader = self.read_journal_jason_file
        try:
            out = file_loader(file_name, **kwargs)
            if out is None:
                raise IOError(f"Error reading {file_name}.")
            pages, meta_dict, session = out
        except UnderDefined as e:
            logging.critical(f"could not load {file_name}")
            raise UnderDefined from e

        logging.debug(f"got pages and meta_dict")

        self.pages = pages
        self.session = session
        self.file_name = file_name
        self._prm_packer(meta_dict)

        if paginate:
            self.generate_folder_names()
            self.paginate()

    def from_frame(self, frame, name=None, project=None, paginate=None, **kwargs):
        if name is not None:
            self.name = name
        if project is not None:
            self.project = project

        self.pages = (
            frame  # TODO: include a check here to see if the pages are appropriate
        )
        for hdr in hdr_journal.values():
            if hdr not in self.pages.columns:
                self.pages[hdr] = None

        if hdr_journal.filename in self.pages.columns:
            self.pages = self.pages.set_index(hdr_journal.filename)

        if paginate is None:
            if self.name and self.project:
                paginate = True

        if paginate:
            logging.critical(f"paginating {project}/{name} ")
            self.generate_folder_names()
            self.paginate()

    def from_file_old(self, file_name=None):
        """Loads a DataFrame with all the needed info about the experiment"""

        file_name = self._check_file_name(file_name)

        with open(file_name, "r") as infile:
            top_level_dict = json.load(infile)

        pages_dict = top_level_dict["info_df"]
        pages = pd.DataFrame(pages_dict)
        pages[hdr_journal.cellpy_file_name] = pages[hdr_journal.cellpy_file_name].apply(
            self._fix_cellpy_paths
        )
        self.pages = pages
        self.file_name = file_name
        self._prm_packer(top_level_dict["metadata"])
        self.generate_folder_names()
        self.paginate()

    def create_empty_pages(self, description=None):
        if description is not None:
            print(f"Creating from {type(description)} is not implemented yet")

        logging.debug("Creating an empty journal")
        logging.debug(f"name: {self.name}")
        logging.debug(f"project: {self.project}")

        col_names = list(hdr_journal.values())
        pages = pd.DataFrame(columns=col_names)
        pages.set_index(hdr_journal.filename, inplace=True)
        return pages

    def duplicate_journal(self, folder=None) -> None:
        """Copy the journal to folder.

        Args:
            folder (str or pathlib.Path): folder to copy to (defaults to the
            current folder).
        """

        logging.debug(f"duplicating journal to folder {folder}")
        journal_name = pathlib.Path(self.file_name)
        if not journal_name.is_file():
            logging.info("No journal saved")
            return
        new_journal_name = journal_name.name
        if folder is not None:
            new_journal_name = pathlib.Path(folder) / new_journal_name
        try:
            shutil.copy(journal_name, new_journal_name)
        except shutil.SameFileError:
            logging.debug("same file exception encountered")

    def to_file(
        self,
        file_name=None,
        paginate=True,
        to_project_folder=True,
        duplicate_to_local_folder=True,
    ):
        """Saves a DataFrame with all the needed info about the experiment.

        Args:
            file_name (str or pathlib.Path): journal file name (.json or .xlsx)
            paginate (bool): make project folders
            to_project_folder (bool): save journal file to the folder containing your cellpy projects
            duplicate_to_local_folder (bool): save journal file to the folder you are in now also

        Returns:
            None
        """
        file_name = self._check_file_name(
            file_name, to_project_folder=to_project_folder
        )

        pages = self.pages
        session = self.session
        meta = self._prm_packer()
        top_level_dict = {"info_df": pages, "metadata": meta, "session": session}

        is_json = False
        is_xlsx = False

        if file_name.suffix == ".xlsx":
            is_xlsx = True

        if file_name.suffix == ".json":
            is_json = True

        if is_xlsx:
            df_session = self._pack_session(session)
            df_meta = self._pack_meta(meta)

            try:
                pages.index.name = "filename"
                with pd.ExcelWriter(file_name, mode="w", engine="openpyxl") as writer:
                    pages.to_excel(writer, sheet_name="pages", engine="openpyxl")
                    # no index is not supported for multi-index (update to index=False when pandas implement it):
                    df_session.to_excel(writer, sheet_name="session", engine="openpyxl")
                    df_meta.to_excel(
                        writer, sheet_name="meta", engine="openpyxl", index=False
                    )
            except PermissionError as e:
                print(f"Could not load journal to xlsx ({e})")

        if is_json:
            jason_string = json.dumps(
                top_level_dict,
                default=lambda info_df: json.loads(
                    info_df.to_json(default_handler=str)
                ),
            )

            with open(file_name, "w") as outfile:
                outfile.write(jason_string)

        self.file_name = file_name
        logging.info(f"Saved file to {file_name}")

        if paginate:
            self.paginate()

        if duplicate_to_local_folder:
            self.duplicate_journal()

    @staticmethod
    def _pack_session(session):
        frames = []
        keys = []
        try:
            l_bad_cycle_numbers = []

            for k, v in session["bad_cycles"].items():
                l_bad_cycle_numbers.append(pd.DataFrame(data=v, columns=[k]))

            df_bad_cycle_numbers = (
                pd.concat(l_bad_cycle_numbers, axis=1)
                .melt(var_name="cell_name", value_name="cycle_index")
                .dropna()
            )
            frames.append(df_bad_cycle_numbers)
            keys.append("bad_cycles")
        except (KeyError, AttributeError):
            logging.debug("missing bad cycle numbers")

        df_bad_cells = pd.DataFrame(session["bad_cells"], columns=["cell_name"])
        frames.append(df_bad_cells)
        keys.append("bad_cells")

        df_starred = pd.DataFrame(session["starred"], columns=["cell_name"])
        frames.append(df_starred)
        keys.append("starred")

        df_notes = pd.DataFrame(session["notes"], columns=["txt"])
        frames.append(df_notes)
        keys.append("notes")

        session = pd.concat(frames, axis=1, keys=keys)
        return session

    @staticmethod
    def _pack_meta(meta):
        meta = pd.DataFrame(meta, index=[0]).melt(
            var_name="parameter", value_name="value"
        )
        return meta

    def generate_folder_names(self):
        """Set appropriate folder names."""
        logging.debug("creating folder names")
        if self.project and isinstance(self.project, (pathlib.Path, str)):
            logging.debug("got project name")
            logging.debug(self.project)
            self.project_dir = os.path.join(prms.Paths.outdatadir, self.project)
        else:
            logging.critical(
                "Could not create project dir (missing project definition)"
            )
        if self.name:
            self.batch_dir = os.path.join(self.project_dir, self.name)
            self.raw_dir = os.path.join(self.batch_dir, "raw_data")
        else:
            logging.critical(
                "Could not create batch_dir and raw_dir", "(missing batch name)"
            )
        logging.debug(f"batch dir: {self.batch_dir}")
        logging.debug(f"project dir: {self.project_dir}")
        logging.debug(f"raw dir: {self.raw_dir}")

    def paginate(self):
        """Make folders where we would like to put results etc."""

        project_dir = self.project_dir
        raw_dir = self.raw_dir
        batch_dir = self.batch_dir

        if project_dir is None:
            raise UnderDefined("no project directory defined")
        if raw_dir is None:
            raise UnderDefined("no raw directory defined")
        if batch_dir is None:
            raise UnderDefined("no batch directory defined")

        # create the folders
        if not os.path.isdir(project_dir):
            os.mkdir(project_dir)
            logging.info(f"created folder {project_dir}")
        if not os.path.isdir(batch_dir):
            os.mkdir(batch_dir)
            logging.info(f"created folder {batch_dir}")
        if not os.path.isdir(raw_dir):
            os.mkdir(raw_dir)
            logging.info(f"created folder {raw_dir}")

        self.project_dir = project_dir
        self.batch_dir = batch_dir
        self.raw_dir = raw_dir

        return project_dir, batch_dir, raw_dir

    def generate_file_name(self):
        """generate a suitable file name for the experiment"""
        if not self.project:
            raise UnderDefined("project name not given")
        out_data_dir = prms.Paths.outdatadir
        project_dir = os.path.join(out_data_dir, self.project)
        file_name = f"cellpy_batch_{self.name}.json"
        self.file_name = os.path.join(project_dir, file_name)

    # v.1.0.0:
    def look_for_file(self):
        pass

    def get_column(self, header):
        """populate new column from db"""
        pass

    def get_cell(self, id_key):
        """get additional cell info from db"""
        pass

    def add_comment(self, comment):
        """add a comment (will be saved in the journal file)"""
        pass

    def remove_comment(self, comment_id):
        pass

    def view_comments(self):
        pass

    def remove_cell(self, cell_id):
        pass

    def add_cell(self, cell_id, **kwargs):
        """Add a cell to the pages"""
        pass


def _dev_journal_loading():
    from cellpy import log

    log.setup_logging(default_level="DEBUG")
    journal_file = pathlib.Path(
        "../../../testdata/batch_project/test_project.json"
    ).resolve()
    assert journal_file.is_file()

    logging.debug(f"reading journal file {journal_file}")
    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file, paginate=False)
    print(80 * "-")
    print(journal.pages)
    print(80 * "-")
    print(journal.session)

    # creating a mock session
    bad_cycle_numbers = {
        "20160805_test001_45_cc": [4, 337, 338],
        "20160805_test001_47_cc": [7, 8, 9],
    }
    bad_cells = ["20160805_test001_45_cc"]

    notes = {"date_stamp": "one comment for the road", "date_stamp2": "another comment"}
    session = {
        "bad_cycle_numbers": bad_cycle_numbers,
        "bad_cells": bad_cells,
        "notes": notes,
    }

    # journal.session = session

    new_journal_name = journal_file.with_name(f"{journal_file.stem}_tmp.xlsx")
    print(new_journal_name)
    journal.to_file(file_name=new_journal_name, paginate=False, to_project_folder=False)


if __name__ == "__main__":
    print(" running journal ".center(80, "-"))
    _dev_journal_loading()
    print(" finished ".center(80, "-"))
