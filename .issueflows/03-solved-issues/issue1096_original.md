# Issue #1096: Ugly legend in fig = cap_summaries.plot() suddenly appearing

Source: https://github.com/jepegit/cellpy/issues/1096

## Original issue text

Cellpy 2.5.1.post4
An ugly legend is suddenly showing up in  in `fig = cap_summaries.plot()`

<img width="900" height="800" alt="Image" src="https://github.com/user-attachments/assets/16c08766-2ff6-44dd-a14f-66401e05c573" />

The "Direction
---- discharge"
Legend in the bottom right corner is ugly and should not appear automatically. No matter wether the discharge or charge is plotted it should be a solid line (as long as it is only one of them per plot). If there is support to put both of them in the same plot, on can be dashed.
