import pathlib
import os
import sys

from cellpy.parameters.legacy.internal_settings import headers_journal_v0 as hdr_journal_old
from cellpy.parameters.internal_settings import get_headers_journal

hdr_journal_new = get_headers_journal()

trans_dict = {
    hdr_journal_old[key]: hdr_journal_new[key]
    for key in hdr_journal_new
}
print(trans_dict)

root_dir = pathlib.Path("/scripts/processing_cellpy").resolve()
ff = root_dir.rglob("cellpy_batch*.json")
for f in ff:
    print(f)
