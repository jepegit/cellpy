# Issue #800: Per-instrument metadata schema (which fields an instrument import needs)

Source: https://github.com/jepegit/cellpy/issues/800

## Original issue text

Split from #791 (item b). When importing raw files, an app has to guess which metadata an instrument needs (mass? area? nominal capacity? default units?). A **declared schema per instrument** would let apps generate the correct ingestion form instead of showing every field for every instrument.

Complements `cellpy.list_instruments()` (#786) and the loader contract (declarations, architecture plan §5); also relates to the external-metadata-source work (#784).
