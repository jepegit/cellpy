# Issue #938: Missing external tools fail silently: mdb-export raises bare FileNotFoundError, pyodbc ImportError hides two loaders

Source: https://github.com/jepegit/cellpy/issues/938

## Original issue text

Two related findings from deploying cellpy in a Linux container
([cellpy-simple-gui#121](https://github.com/cellpy/cellpy-simple-gui/issues/121)).
Both are cases where a missing *system* dependency produces a failure that is
easy to mistake for success.

## 1. `mdb-export` missing → bare `FileNotFoundError`

On posix, `arbin_res` reads `.res` by shelling out to `mdb-export` (mdbtools).
When it is not installed:

```
[Errno 2] No such file or directory: 'mdb-export'
```

An app catching that has to know that "mdb-export" means "install mdbtools", and
a user reading it in a toast has no chance. It cost us a genuinely misleading
green tick: our smoke test asserted the import job completed, the job *did*
complete, and zero cells were imported.

**Suggestion:** raise something named and actionable when the tool is absent,
e.g.

```
CellpyDependencyError:
  Reading Arbin .res on Linux/macOS needs mdbtools (provides `mdb-export`).
      Debian/Ubuntu:  apt install mdbtools
      macOS:          brew install mdbtools
```

A `shutil.which("mdb-export")` check before the call would be enough, and could
also feed a capability probe (below).

## 2. `libodbc.so.2` missing → two loaders disappear from discovery

`arbin_sql` and `arbin_sql_7` raise at import:

```
ImportError: libodbc.so.2: cannot open shared object file: No such file or directory
```

Anything enumerating instruments therefore sees **11 loaders instead of 13**,
with no indication that two were dropped or why. Our instrument picker simply
did not offer them, and nothing in the UI could explain the difference between
the Windows build and the container.

**Suggestion:** let discovery report unavailable loaders rather than omit them —
something like `(id, available: bool, reason: str)` — so a UI can grey the entry
out with a tooltip instead of silently narrowing the list. `registry.families()`
already does something like this well for plots (2.1.2, #868); the same shape
would suit instruments.

## What this looks like fixed

An app could then ask cellpy "what can you actually read here?" and show the
answer, instead of discovering the gaps one confused user at a time.

(For the record, the container fix is `apt install mdbtools unixodbc` — but the
point is that we found it by instrumenting our own test, not from any message
cellpy produced.)

## Comments (curated summary)

- **Additional tasks**: make the default `paths.examplesdir` absolute (`Path.home() / "cellpy_data" / "examples"`). A relative default resolves against process cwd, so a frozen Windows app wrote demo cells into its install folder.
- **Clarifications / constraints**: `config.reload()` after setting `CELLPY_PATHS__EXAMPLESDIR` is the workaround that already works; creating the relative directory is not a fix.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-08-16._

