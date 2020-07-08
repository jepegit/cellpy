import json
import logging
import warnings
import os
import pathlib
import platform

import pandas as pd

from cellpy.exceptions import UnderDefined
from cellpy.parameters import prms
from cellpy.readers import dbreader
from cellpy.parameters.internal_settings import get_headers_journal
from cellpy.parameters.legacy.internal_settings import (
    headers_journal_v0 as hdr_journal_old,
)
from cellpy.utils.batch_tools.batch_core import BaseJournal
from cellpy.utils.batch_tools.engines import simple_db_engine

hdr_journal = get_headers_journal()

trans_dict = {}
missing_keys = []
for key in hdr_journal:
    if key in hdr_journal_old:
        trans_dict[hdr_journal_old[key]] = hdr_journal[key]
    else:
        missing_keys.append(key)


class LabJournal(BaseJournal):
    def __init__(self, db_reader="default"):
        super().__init__()
        if db_reader == "default":
            self.db_reader = dbreader.Reader()
        else:
            logging.debug(f"Remark! db_reader: {db_reader}")
            self.db_reader = db_reader
        self.batch_col = "b01"

    def _check_file_name(self, file_name):
        if file_name is None:
            if not self.file_name:
                self.generate_file_name()
            file_name = self.file_name
        return file_name

    def from_db(self, project=None, name=None, batch_col=None):
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
            srnos = self.db_reader.select_batch(name, batch_col)
            self.pages = simple_db_engine(self.db_reader, srnos)
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
        self.generate_folder_names()
        self.paginate()

    @staticmethod
    def _fix_cellpy_paths(p):
        if platform.system() != "Windows":
            if p.find("\\") >= 0:
                # convert from win to posix
                p = pathlib.PureWindowsPath(p)
        else:
            if p.find("/") >= 0:
                # convert from posix to win
                p = pathlib.PurePosixPath(p)
        return pathlib.Path(p)

    @classmethod
    def read_journal_jason_file(cls, file_name):
        logging.debug(f"json loader starting on {file_name}")
        with open(file_name, "r") as infile:
            top_level_dict = json.load(infile)
        pages_dict = top_level_dict["info_df"]
        meta_dict = top_level_dict["metadata"]
        pages = pd.DataFrame(pages_dict)

        logging.debug("checking path-names")
        try:
            pages[hdr_journal.cellpy_file_name] = pages[
                hdr_journal.cellpy_file_name
            ].apply(cls._fix_cellpy_paths)
        except KeyError:
            logging.warning("old journal file - updating")
            pages.rename(columns=trans_dict, inplace=True)
            pages[hdr_journal.cellpy_file_name] = pages[
                hdr_journal.cellpy_file_name
            ].apply(cls._fix_cellpy_paths)

        for column_name in missing_keys:
            if column_name not in pages.columns:
                warnings.warn(f"old journal format - missing: {column_name}")
                pages[column_name] = None

        return pages, meta_dict

    def from_file(self, file_name=None, paginate=True):
        """Loads a DataFrame with all the needed info about the experiment"""

        file_name = self._check_file_name(file_name)
        logging.debug(f"reading {file_name}")
        pages, meta_dict = self.read_journal_jason_file(file_name)
        logging.debug(f"got pages and meta_dict")
        self.pages = pages
        self.file_name = file_name
        self._prm_packer(meta_dict)
        self.generate_folder_names()
        if paginate:
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

    def to_file(self, file_name=None, paginate=True):
        """Saves a DataFrame with all the needed info about the experiment"""
        file_name = self._check_file_name(file_name)
        pages = self.pages
        top_level_dict = {"info_df": pages, "metadata": self._prm_packer()}
        jason_string = json.dumps(
            top_level_dict,
            default=lambda info_df: json.loads(info_df.to_json(default_handler=str)),
        )
        if paginate:
            self.paginate()

        with open(file_name, "w") as outfile:
            outfile.write(jason_string)

        self.file_name = file_name
        logging.info("Saved file to {}".format(file_name))

    def generate_folder_names(self):
        """Set appropriate folder names."""
        if self.project:
            self.project_dir = os.path.join(prms.Paths.outdatadir, self.project)
        else:
            print("Could not create project dir (missing project definition)")
        if self.name:
            self.batch_dir = os.path.join(self.project_dir, self.name)
            self.raw_dir = os.path.join(self.batch_dir, "raw_data")
        else:
            print("Could not create batch_dir and raw_dir", "(missing batch name)")

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
        file_name = "cellpy_batch_%s.json" % self.name
        self.file_name = os.path.join(project_dir, file_name)

    # v.1.0.0:
    def look_for_file(self):
        pass

    def get_column(self, header):
        """populate new column from db"""
        pass

    def get_cell(self, srno):
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
