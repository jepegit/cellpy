# Issue #961: need more detailed error messages for OtherPath

Source: https://github.com/jepegit/cellpy/issues/961

## Original issue text

A user had env_file = ".env_cellpy" in the cellpy.toml file. His .env_cellpy file was located on C:\users\<username>\. And cellpy could not find it. However, the error message he got was "UnderDefined: You must define either CELLPY_PASSWORD or CELLPY_KEY_FILENAME environment variables."
This did not help the user finding out that the .env_cellpy file was not found.
