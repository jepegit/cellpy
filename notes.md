# My `cellpy` notes

Use this to write down notes and follow the progress of the project.
This will be particularly useful for updating the HISTORY.rst file before
releases.

## Unspecified

### CI - Appveyor vs GitHub actions
- 2022-07-30 Tried to use GitHub actions for windows tests - failed most likely due to missing AccessDatabaseEngine.
- 2022-07-30 Changed from pip to conda install (dev_environment.yml) in Appveyor - fixed failed run!


## Plans and ideas

1. ?

## Branches

### 161-Arbin-sql-enhancement

Note: misspelling in the branch title.

Status: Mohammad might be working on it?

### 204-restructure-txt-loaders

Status: Finished!

### 209-additional-optional-parameters-from-journal-page-to-individual-cells

Status: Implemented - but missing documentation.

### 211-factory-pattern-for-loaders

https://realpython.com/factory-method-python/

Status: Implemented - but missing documentation.

### 219-more-complete-unit-handling-system

Status: implemented - but missing documentation

### 225-remove-completely-option-for-having-multiple-cells

Step 1: replace all occurrences of cells[0] with .cell property
    - cellreader: need to fix merge
        - removed it for now (used in dev_update.. but that must be changed anyway)
    - cellreader: need to fix from_raw
        - done with still some clean up left
        - add uid / hash?
    - cellreader: remove dataset_number as an argument
        - done
    - cellreader: remove for-loops for cells in all methods (summary, xxx)
        - done
    - cellreader: replace list with cell object for load and save cellpy-files
    - instruments: work on single cell instead of cells (list)
    - modify .cell property so that it sets and gets the cell object directly to self._cell

Step 2: rename the .cell property to .data
Step 3: rename the Cell object to Data

Step 5: rewrite merging / appending