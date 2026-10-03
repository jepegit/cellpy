# Issue #780: L2: load_since() for cheap-partial loaders (arbin_res/sql, neware_txt, maccor_txt)

Source: https://github.com/jepegit/cellpy/issues/780

## Original issue text

Epic L of **cellpy 2.2 (Stage 5)**. Design: [live-incremental](https://github.com/cellpy/architecture-plan/blob/main/cellpy2-live-incremental-design.md) §7 item 2. Depends on **L1**.

Implement `load_since(source, marker)` for the sources that can re-read cheaply from a marker first: `arbin_res`, `arbin_sql`, `neware_txt`, `maccor_txt`. Return native-schema raw rows appended since the marker (may overlap the tail) + the new marker. Other loaders stay full-read and fall back.

## Epic context

Epic #783 stage 2 ("Cell update from a marker"). Depends on #779 (merged in
PR #1100). `CellpyCell.update()` is #164 and consumes the chunks produced here.
