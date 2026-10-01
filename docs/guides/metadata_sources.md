# Pull cell metadata from a lab database (BatBase)

You have the raw file from the cycler. The **mass, electrode area, nominal
capacity and cell type** live somewhere else — in your lab's database. This
page shows how to let cellpy fetch them instead of typing them in, using
IFE's BatBase as the example. The same steps apply to any *metadata source*
plugin.

If you only want the one-liner, see [How do I…?](../how_do_i.md#set-the-cell-up-correctly).

## What you get

```python
import cellpy

c = cellpy.get("20250925_siba001_01_hcicc_lif_01.res", instrument="arbin_res")
c.fetch_meta("batbase")          # looks the cell up by its name in BatBase
c.refresh_after()                # recompute the summary with the new mass etc.

c.data.meta_common.mass          # → 2.35  (mg, from the electrode record)
c.data.meta_common.nom_cap       # → 3579.0 (mAh/g)
c.external_links["batbase"]      # → where it came from (row id + URL)
```

`fetch_meta` is read-only towards the database and applies the record the same
way a batch-journal row would: **above** what the instrument file wrote,
**below** anything you pass explicitly (`mass=…`) afterwards. If the database
is unreachable, the cell still loads — you get a warning and no metadata layer.

When BatBase also knows *where the files are*, you can drop the filename
altogether — `cellpy.get(source="batbase", key="SAL_010", kind="tag")` — see
[step 5](#5-let-the-database-find-the-files).

## 1. Install the connector

Metadata sources are plugins. BatBase lives in the `cellpy-connectors`
package; install it into the same environment as cellpy:

```bash
pip install cellpy-connectors            # or: uv pip install cellpy-connectors
```

Check that cellpy sees it:

```python
from cellpy.readers import metadata_sources
metadata_sources.names()   # → ('batbase',)
```

If the tuple is empty, the package went into a different environment than the
one running cellpy.

## 2. Give cellpy your credentials — once

BatBase issues each user an **API client id and secret** (OAuth2 client
credentials; ask your BatBase admin, or create one on your BatBase profile
page). Store them in your operating system's keyring:

```bash
cellpy connectors configure batbase
```

You are prompted for the id and the secret; nothing is echoed and nothing is
written to a file. On a machine without a keyring (a compute cluster, CI), use
environment variables instead:

| Variable | Meaning |
| --- | --- |
| `CELLPY_BATBASE_CLIENT_ID` | the client id |
| `CELLPY_BATBASE_CLIENT_SECRET` | the client secret |
| `CELLPY_BATBASE_URL` | the server, e.g. `https://batbase.example.org` (defaults to a local dev server) |

Then prove the connection works:

```bash
cellpy connectors batbase check
```

It prints a small JSON block with `"authenticated": true` and the scope
(`read`). A wrong secret says so in plain words; fix it with `configure`
again. cellpy never reads these secrets from its YAML config file, so do not
put them there.

## 3. Fetch

`fetch_meta(source, key, kind=…)` needs to know **what to look for**. BatBase
accepts four kinds of key:

| `kind=` | `key` is … | Typical use |
| --- | --- | --- |
| `"cell_name"` (default) | the cellpy **label** BatBase stores for the test, falling back to the test name or the cell name | one cell, named the same in both places |
| `"tag"` | a **cellpy tag** name (add `project=` if the same tag exists in several projects) | all tests of a campaign |
| `"external_id"` | the journal row **id** | you copied the id from the BatBase page |
| `"test_name"` | BatBase's own test name (`20250925_siba001_01_hcicc_lif`) | scripted lookups |

```python
c.fetch_meta("batbase")                                  # key = c.cell_name
c.fetch_meta("batbase", "siba_01", kind="cell_name")     # a different label
c.fetch_meta("batbase", "SAL_010", kind="tag", project="3")
c.fetch_meta("batbase", "42", kind="external_id")
```

The call returns the matching records (a tuple). Empty means *nothing found,
nothing changed*:

```python
records = c.fetch_meta("batbase", "typo_here")
if not records:
    print("not in BatBase — set the mass by hand")
```

A tag usually matches **several** tests. `fetch_meta` applies the *first*
record and logs a warning; when you want to pick yourself, look before you
apply:

```python
records = c.fetch_meta("batbase", "SAL_010", kind="tag", apply=False)
for r in records:
    print(r.external_id, r.test.get("cell_name"), r.cell.get("mass"))
```

## 4. Recompute, then check what changed

Fetching writes the metadata but does **not** rebuild the summary. Do that
explicitly:

```python
c.refresh_after()      # cheap: only the mass/area/nom_cap-dependent columns
# or c.make_summary() for a full rebuild
```

To see exactly which fields BatBase supplied:

```python
link = c.external_links["batbase"]
link.fields        # ('active_electrode_area', 'cell_name', 'cell_type', 'mass', ...)
link.source_uri    # 'https://…/api/test-cellpy-journal/42/'
link.fetched_at    # when
```

The link is saved inside the cellpy file, so a colleague opening
`my_cell.cellpy` later can see where the mass came from.

## What BatBase fills in

| BatBase | cellpy (`meta_common`) | Unit after fetch |
| --- | --- | --- |
| electrode mass (`mass`, `total_mass`) | `mass`, `tot_mass` | mg |
| electrode `area`, `loading` | `active_electrode_area`, `active_electrode_loading` | cm², mg/cm² |
| nominal capacity + unit | `nom_cap`, `nom_cap_specifics` | mAh/g (gravimetric), mAh/cm² (areal) or mAh (absolute) |
| cell configuration `hc` / `fc` / `3e` / `sym` | `cell_type` | `half_cell` / `full_cell` / … |
| test mode normal / inverted | `cycle_mode` | `cathode` or `full_cell` / `anode` |
| test label | `cell_name` | — |
| comments, schedule file | `comment`, `schedule_file_name` | — |

The units follow cellpy's conventions described in
[Units, mass, area and C-rates](units.md); you do not convert anything
yourself. If BatBase has no electrode record for the cell, those fields are
simply not touched.

## When it does not work

**`fetch_meta` returns `()` and logs "had nothing for …"** — the key did not
match. Check the label in BatBase, or try `kind="external_id"` with the row id
from the web page. Also make sure you are a *member* of the project in
BatBase: the API only shows rows from projects you belong to.

**`MetadataSourceAuthError`** — credentials missing or rejected. This is never
swallowed, even without `strict=True`, because silently loading a cell
*without* its mass is worse than stopping. Run `cellpy connectors batbase
check`.

**Warning "metadata source 'batbase' unavailable … continuing without it"** —
read the bit in parentheses. `UnknownMetadataSource` means the connector
package is not installed in *this* environment (step 1); a connection error
means network or server down. Either way the cell loaded without the database
layer. Re-run `fetch_meta` later, or pass `strict=True` if your script must
not continue without it (then these become exceptions).

**The summary still shows the old mass** — you forgot step 4
(`c.refresh_after()`).

## 5. Let the database find the files

If BatBase also records *where* a test's files live (the `files` list on an
experiment — a raw export, a `.cellpy` archive, or both), you can skip the
filename entirely:

```python
c = cellpy.get(source="batbase", key="SAL_010", kind="tag")
```

cellpy asks BatBase for the record, opens the files it points at (a
`.cellpy` archive is preferred when it is newer than the raw file, exactly
like `cellpy.get(raw, cellpy_file=...)`), applies the metadata, and keeps
the paths it used in `c.external_links["batbase"].files`. `filefinder` — the
glob over `rawdatadir` — only runs when the record has no file pointers, in
which case it searches for the record's cell name as usual.

Two things differ from the plain `fetch_meta` call:

- **Errors are loud.** With no filename to fall back on, an unreachable or
  unknown source raises instead of returning `()`, and a key with no record
  raises `NoDataFound`. Pass `strict=False` to get the quiet behaviour back.
- **Your keywords still win.** `cellpy.get(source=..., mass=2.0)` loads the
  files BatBase pointed at but keeps *your* mass.

Giving both a filename and a source (`cellpy.get("cell.res", source="batbase")`)
is the enrichment case: the file is loaded, the record (looked up by the
file's stem) is applied on top, and a missing record is only a warning.
`CellpyCell.from_source("batbase", "SAL_010", kind="tag")` is the same call
spelled as a constructor.

## Batch workflows

The batch utility resolves metadata through the same layers, so a journal
built from the Excel sheet ([Set up the cellpy database](batch_database.md))
and a record fetched from BatBase end up in the same place.

A whole batch straight from a BatBase tag:

```python
from cellpy import batch

b = batch.from_source("batbase", "SAL_010")      # kind="tag" by default
b.update()                                       # opens the pointed-at files
b.cells["SAL_010_01"].external_links["batbase"]  # the back-link per cell
```

`from_source` builds the journal pages from the records — one row per test
with `mass`, `area`, `loading`, `nom_cap`, `cycle_mode`, the instrument hint
and the raw / `.cellpy` paths — and stores the back-links in the journal
session, so a saved journal remembers where each row came from. Rows whose
record has no file pointers go through the normal `filefinder` search
(`file_search=False` leaves them empty instead). `project=` scopes both the
BatBase lookup and the journal; `name=` overrides the default
`batbase_tag_SAL_010`. Anything else (`channel=3`) is passed to the source as
a filter.

What the batch path does **not** do: re-resolve per-field provenance
(`Resolution.origin_of`) on each cell — the journal row is the layer, the
`ExternalLink` names the source. Using `size` / `mtime` from the pointers to
skip stat-ing raw files on `update()` is planned for a later release.

## For developers

The plugin contract (`MetadataSource`, `MetaQuery`, `MetaRecord`, the
`cellpy.metadata_sources` entry-point group) is documented in the
[API reference](../api/readers.md#external-metadata-sources) and in
`cellpy.readers.metadata_sources.testing.check_metadata_source`, a conformance
check you can run against your own source.
