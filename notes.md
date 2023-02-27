# My `cellpy` notes

Use this to write down notes and follow the progress of the project.
This will be particularly useful for updating the HISTORY.rst file before
releases.

## Unspecified

### Need to use API token for PyPI
First, generate an API token for your account or project at https://pypi.org/manage/account/token/

Then, use this token when publishing instead of your username and password.

See https://pypi.org/help/#apitoken for help using API tokens to publish.

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
Status: implemented - but missing documentation

### 233-multi-template-system
Made new repository (cellpy_cookies)
Populated with two templates (standard and ife)
Checked and updated standard template, but needs more tweaking (functioning, though)
Not checked and updated code in ife template(TODO)

### fix missing area:
Added area to HeadersJournal and updated the update method in batch_experiments.py and the loadcell method to
optionally receive loading and/or area and set area from area or from mass/loading if area is not given.

Have not checked if it works properly with the simple db-reader (if the key-word/header etc is set), but
no point until the new version of dbreader is made.

### 243-refactor-and-update-dbreader-etc
Steps:
1. clean up b.update
2. clean up simple db reader (or whatever it is called inside journal etc)
3. clean up dbreader
4. implement/test using an ORM (SQAlchemy?)
