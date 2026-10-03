# MCP remote raw listing and load (#1089)

**Context:** Epic #1074 Scenario 2. `rawdatadir` may be an `OtherPath` URI.
The pathlib sandbox cannot contain a remote share.

**Decision:** List remote raw via `filefinder.find_by_project`. `load_cell`
accepts a URI only when it is under configured `rawdatadir` /
`cellpydatadir` (prefix + no `..`). Do not add `/` as a pathlib root.
`cellpy.get` copies remote → temp.

**Rejected:** Refuse all remote load (story fails when raw is OtherPath);
widen the sandbox to `/`.
