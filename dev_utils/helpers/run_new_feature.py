"""python file for test-running of new features"""

import os
import pathlib
import sys

import box

from cellpy import cellreader, prms


def set_temp(tempdir="/temp"):
    prms.Paths.rawdatadir = tempdir
    prms.Paths.filelogdir = tempdir
    prms.Paths.cellpydir = tempdir


def print_prms():
    """this function will show only the 'box'-type attributes and their content in the cellpy.prms module"""
    print("running")
    print("--goal:")
    print("  convenience function for prms")
    print(type(prms))
    print(prms.__name__)

    for key in prms.__dict__:
        if isinstance(prms.__dict__[key], box.Box):
            print()
            print(80 * "=")
            print(f"prms.{key}:")
            print(80 * "-")
            for subkey in prms.__dict__[key]:
                print(f"prms.{key}.{subkey} = ", f"{prms.__dict__[key][subkey]}")
            print(80 * "=")


if __name__ == "__main__":
    print_prms()
