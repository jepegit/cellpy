# Issue #962: better feedback when running batch.load

Source: https://github.com/jepegit/cellpy/issues/962

## Original issue text

The user ran batch.load using the "excel database" solution. It looked like everything went well, but it turned out that the filefinder had not found any of the raw-files. The user used external location for the raw files (OtherPath). It should be obvious for the user if some of the files were not found.
