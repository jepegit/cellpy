# Issue #375: Add support for remote paths for raw data and cellpy data access

Source: https://github.com/jepegit/cellpy/issues/375

## Original issue text

- Loading raw data from remote locations
- Searching/listing remote raw-data directories
- Reading and possibly writing cellpy files stored remotely
- handling of authentication and credentials
- when direct remote access is not possible: Predictable local caching / temporary copy behavior 

 ## Questions to resolve
  - Which remote schemes do we want to support initially?
      - ssh://
      - sftp://
      - scp://
      - others?
- What happens if the remote connection isn't accessible to the user? Additional permissions necessary?    
- Should support be limited to raw data first?
- How should credentials be provided?
      - environment variables
      - SSH config / agent
      - key file path
      - password fallback
- What should the expected behavior be for:
      - exists()
      - is_file()
      - glob() / rglob()
      - copying to local temp storage
      - saving back to remote



## Acceptance criteria

  - A user can configure a remote raw-data directory and load supported raw files from it.
  - Remote raw-file discovery works in a documented and tested way.
  - Credential handling is documented and tested.
  - Behavior for remote cellpy file loading/saving is explicitly supported or explicitly rejected with a clear error.
  - The supported remote-path workflows are covered by tests and documented in the user docs.

Notes

  This issue is about remote path support as a feature. Refactoring the internal path abstraction should be treated as a separate issue unless it is
  strictly necessary to complete this work.

## Comments (curated summary)

- **Clarifications / constraints**:
  - Linked to / related work: jepegit/cellpy#371

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-06-14._
