# Issue #778: L6: golden equality test — incremental update() == full load

Source: https://github.com/jepegit/cellpy/issues/778

## Original issue text

Epic L of **cellpy 2.2 (Stage 5)**. Design: [live-incremental](https://github.com/cellpy/architecture-plan/blob/main/cellpy2-live-incremental-design.md) §7 item 6. **Author first** — this is the correctness anchor for the whole epic.

Load a truncated file, append the tail, and assert `update()` == a full load of the whole file (summary equality). *Incremental refresh of a split file must equal a full load of the whole file.*
