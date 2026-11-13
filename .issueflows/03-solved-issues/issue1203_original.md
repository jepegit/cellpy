# Issue #1203: problems with ica_collector

Source: https://github.com/jepegit/cellpy/issues/1203

## Original issue text

imports correctly. but the line

```
icas_collected = ica_collector(b, cycles=(2,3,4))
```
gives error:

```
ValueError: cycle frame is empty. The requested cycle may be missing from the source data.
```
which is weird, because cycle_collector works.

i have tested different cycles arguments, and without and it doesnt work.
is there a limit to how many cells you can view in ica_collector, but not in cycle_collector?

also newly installed both anaconda and cellpy.
cellpy version: cellpy 2.1.5.post8. no further updates with `conda update -c conda-forge cellpy`
