# Issue #662: problem with v1.0.1

Source: https://github.com/jepegit/cellpy/issues/662

## Original issue text

Has there been any changes in cellpy (running v1.0.1post1) modifying otherpath? I got this error (running batch.load):

```
2026-07-23 22:21:29 - root - CRITICAL (create_journal): auto_use_file_list is True - this is an experimental feature
2026-07-23 22:21:29 - root - DEBUG (create_journal): The file_list will be used for searching for files
2026-07-23 22:21:29 - root - DEBUG (create_journal): in stead of doing individual glob searches in the raw-file directory
2026-07-23 22:21:29 - root - DEBUG (create_journal): reducing the number of ssh-connections to the remote servers.
2026-07-23 22:21:29 - root - DEBUG (create_journal): file_list_kwargs: {}
2026-07-23 22:21:29 - root - INFO (find_in_raw_file_directory): --- EXPERIMENTAL ---
2026-07-23 22:21:29 - root - INFO (find_in_raw_file_directory): This function uses 'find' and 'ssh' to search for files.
2026-07-23 22:21:29 - root - INFO (find_in_raw_file_directory): Not all systems have these commands available.
2026-07-23 22:21:29 - root - DEBUG (_check_external): Running _check_external for OtherPath
2026-07-23 22:21:29 - root - INFO (find_in_raw_file_directory): Searching for files matching: *
2026-07-23 22:21:29 - root - DEBUG (__str__): external path, returning _original
2026-07-23 22:21:29 - root - DEBUG (find_in_raw_file_directory): searching in folder: scp://odin/home/jepe@ad.ife.no/projects
could not create journal: You must define either CELLPY_PASSWORD or CELLPY_KEY_FILENAME environment variables.
you might have duplicates in your database index or cell names
```

both my config and env file is set and they have worked before
