import json
import logging
import os

import pandas as pd

from cellpy.exceptions import UnderDefined
from cellpy.parameters import prms
from cellpy.readers import dbreader
from cellpy.utils.batch_tools.batch_core import BaseJournal
from cellpy.utils.batch_tools.engines import simple_db_engine
from cellpy.readers.core import doc_inherit

logger = logging.getLogger(__name__)


class LabJournal(BaseJournal):

    def __init__(self, db_reader="default"):
        super().__init__()
        if db_reader == "default":
            self.db_reader = dbreader.Reader()
        else:
            logger.debug(f"Remark! db_reader: {db_reader}")
            self.db_reader = db_reader
        self.batch_col = "b01"

    def _check_file_name(self, file_name):
        if file_name is None:
            if not self.file_name:
                self.generate_file_name()
            file_name = self.file_name
        return file_name

    @doc_inherit
    def from_db(self, project=None, name=None, batch_col=None):
        if batch_col is None:
            batch_col = self.batch_col
        if project is not None:
            self.project = project
        if name is None:
            name = self.name
        else:
            self.name = name
        logging.debug(
            f"batch_name, batch_col: {name}, {batch_col}"
        )
        if self.db_reader is not None:
            srnos = self.db_reader.select_batch(name, batch_col)
            self.pages = simple_db_engine(self.db_reader, srnos)
        else:
            logging.debug("creating empty journal pages")
            self.pages = pd.DataFrame()
        self.generate_folder_names()
        self.paginate()

    def from_file(self, file_name=None):
        """Loads a DataFrame with all the needed info about the experiment"""

        file_name = self._check_file_name(file_name)

        with open(file_name, 'r') as infile:
            top_level_dict = json.load(infile)

        pages_dict = top_level_dict['info_df']
        pages = pd.DataFrame(pages_dict)
        self.pages = pages
        self.file_name = file_name
        self._prm_packer(top_level_dict['metadata'])
        self.generate_folder_names()
        self.paginate()

    def to_file(self, file_name=None):
        """Saves a DataFrame with all the needed info about the experiment"""

        file_name = self._check_file_name(file_name)
        pages = self.pages

        top_level_dict = {
            'info_df': pages,
            'metadata': self._prm_packer()
        }

        jason_string = json.dumps(
            top_level_dict,
            default=lambda info_df: json.loads(
                info_df.to_json()
            )
        )

        self.paginate()

        with open(file_name, 'w') as outfile:
            outfile.write(jason_string)

        self.file_name = file_name
        logging.info("Saved file to {}".format(file_name))

    def generate_folder_names(self):
        """Set appropriate folder names."""
        self.project_dir = os.path.join(prms.Paths.outdatadir, self.project)
        self.batch_dir = os.path.join(self.project_dir, self.name)
        self.raw_dir = os.path.join(self.batch_dir, "raw_data")

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
            raise UnderDefined("no batcb directory defined")

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

        return project_dir, batch_dir, raw_dir

    def generate_file_name(self):
        """generate a suitable file name for the experiment"""
        if not self.project:
            raise UnderDefined("project name not given")

        out_data_dir = prms.Paths.outdatadir
        project_dir = os.path.join(out_data_dir, self.project)
        file_name = "cellpy_batch_%s.json" % self.name
        self.file_name = os.path.join(project_dir, file_name)

    def look_for_file(self):
        pass
