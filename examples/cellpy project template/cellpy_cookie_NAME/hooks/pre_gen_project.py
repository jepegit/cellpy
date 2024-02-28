import os
import sys


MIN_CELLPY_MAJOR, MIN_CELLPY_MINOR = 1, 0
cellpy_version = "{{ cookiecutter.cellpy_version }}"
major, minor = cellpy_version.split(".")[:2]
major, minor = int(major), int(minor)
too_old = False

if major < MIN_CELLPY_MAJOR:
    too_old = True

if major == MIN_CELLPY_MAJOR:
    if minor < MIN_CELLPY_MINOR:
        too_old = True

# additional test for patch version since v.1.0.0 -> v.1.0.1 introduced a new batch method.
if major == MIN_CELLPY_MAJOR and minor == MIN_CELLPY_MINOR:
    patch = cellpy_version.split(".")[2]
    if patch.startswith("0"):
        print()
        print(" ERROR ".center(80, "="))
        print()
        print("  Cellpy Cookie says: 'OH NO!!!!'")
        print("  Cellpy Cookie says: 'Your version of cellpy is too old - aborting!'")
        print("  Cellpy Cookie says: 'Please update cellpy to the latest version'")
        print()
        print("    $ python -m pip install cellpy --upgrade")
        print()
        print("  Cellpy Cookie says: 'or use the cookie standard_1_0_0 instead!'")
        print()
        print("    $ cellpy new --template starndard_1_0_0")
        print()
        print(80 * "=")
        print()
        sys.exit(1)

# end of additional test

if too_old:
    print()
    print(" ERROR ".center(80, "="))
    print()
    print("  Cellpy Cookie says: 'OH NO!!!!'")
    print("  Cellpy Cookie says: 'Your version of cellpy is too old - aborting!'")
    print()
    print(80 * "=")
    print()
    sys.exit(1)
print("   Cellpy Cookie says: 'using cookie from the cellpy_cookies repository'")
print("   Cellpy Cookie says: 'setting up project in the following directory:'")
print(f"      {os.getcwd()}'")
print()
