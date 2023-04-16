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
Fixed

### 243-refactor-and-update-dbreader-etc
Steps:
1. clean up b.update (in progress)
   [x] implement cellpy.loadcell into cellpy.get
   [x] implement cellpy.loadcell into cellpy.get
3. clean up simple db reader (or whatever it is called inside journal etc) (in progress)
4. clean up dbreader (in progress)
5. implement/test using an ORM (SQAlchemy?) (in progress)

### 250-improve-collectors

### 249-access-raw-files-ssh
1. Added a subclass of pathlib.Path that can be used to access files on a remote server using ssh.
2. Added new methods to the base loader and implemented new restrictions/requirements on the loaders.
   1. all .loader methods must now start with assigning self.name and
      running self.copy_to_temporary() to copy the file to a local temporary
   2. fid is generated through running self.generate_fid() and fid is
      added to the Data instances using self.fid as argument.


3. Modify AtomicLoad in base.py so that it can handle
   the new Path subclass and use it to load files from a remote server.
   1. After some trail and errors, the next step now will be to implement the
      actual ssh connection and file transfer in core.copy_external_file

4. Implement the ssh connection and file transfer in core.copy_external_file
   1. This will be done by using the paramiko library.
   2. The connection will be established in core.copy_external_file and
      the file will be copied to a temporary directory on the local machine.
   3. The temporary directory will be deleted after the file has been copied.
   4. Test is in test_cell_reader.py (test_copy_external_file) copied as txt in local/notes.md

5. Update filefinder and prms to handle the new Path subclass.
6. Check if loaders can be updated to automatically run the new methods
   in the base loader (self.name and self.copy_to_temporary()).
7. Update dependencies (setup.py, requirements.txt etc)
