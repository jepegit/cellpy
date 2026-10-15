# Issue #1149: Error when reding .ndax files

Source: https://github.com/jepegit/cellpy/issues/1149

## Original issue text

cellpy 2.1.5.post4

Loading the cycling data with filename: 20261013_nor110_04_fcnmp_cyc_20261013151333
Results in wrong gravimetric discharge capacity and C-rate produced by the `b.plot()` function.
Likey off by 1000.

<img width="1000" height="950" alt="Image" src="https://github.com/user-attachments/assets/7095a22e-fbb2-4dde-ae9b-2373b724ed67" />

It also shows wrong current in the plot prodced by:
```
label = b.cell_names[0]
c = b.cells[label]
plotutils.raw_plot(c)
```
The current is supposed to be 56 mA, so this is off by something else than 1000 exactly.

<img width="1248" height="727" alt="Image" src="https://github.com/user-attachments/assets/480344b3-882a-4402-bd89-954cb5252ba1" />

The current was likely set correctly since this is an aged cell which was cycled at C/20 with respect to initial capacity, and the full cycle took about 30 hours

<img width="1000" height="600" alt="Image" src="https://github.com/user-attachments/assets/c39b651e-18c9-4b71-bd41-99bde6b38983" />

(I'm currently having issues with BTSDA, so I cannot view the data on the Neware computer to confirm what the current is registered as there).

## Comments (curated summary)

- **Clarifications / constraints**:
  - The `cellpy_db` cell_log row was copied from this cell's earlier Arbin cycling, where that same entry is correct. Keep the journal mass and nominal capacity as the known-good reference. The error is in the `.ndax` load.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @inger-emma on 2026-10-15._
