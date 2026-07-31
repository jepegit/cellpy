# Issue #799: Lightweight metadata read: read_meta(path) without a full get()

Source: https://github.com/jepegit/cellpy/issues/799

## Original issue text

Split from #791 (item a). Listing many `.cellpy` files (a project browser) currently needs a full `cellpy.get(...)` per file just to show mass / area / #cycles. A cheap `read_meta(path)` that reads the header metadata (v9 `meta.json` sidecar / hdf5 metadata) **without** materialising raw/steps/summary would make file browsers snappy.

Relates to the v9 container (`readers/cellpy_file/`, meta.json is already a separate zip member) and the metadata models.
