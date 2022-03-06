import os
import pathlib
import sys

from cellpy.parameters.internal_settings import get_headers_journal
from cellpy.parameters.legacy.internal_settings import (
    headers_journal_v0 as hdr_journal_old,
)
from cellpy.utils.batch_tools.batch_journals import LabJournal

hdr_journal_new = get_headers_journal()

trans_dict = {hdr_journal_old[key]: hdr_journal_new[key] for key in hdr_journal_new}
print(trans_dict)

root_dir = pathlib.Path("/scripts/processing_cellpy").resolve()
all_files = list(root_dir.rglob("cellpy_batch*.json"))
test_file = r"C:\scripts\cellpy\testdata\batchfiles\cellpy_batch_test.json"
test_file2 = r"C:\scripts\cellpy\testdata\db\cellpy_batch_test.json"
all_files.extend([test_file, test_file2])
for f in all_files:
    print(f"processing {f}")
    journal = LabJournal(db_reader=None)
    journal.from_file(f, paginate=False)
    print(journal.pages.columns)
    print(journal.pages.head())
    journal.pages.rename(columns=trans_dict, inplace=True)
    print(journal.pages.head())
    journal.to_file(f, paginate=False)
