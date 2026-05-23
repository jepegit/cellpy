# Issue #363: Add filtering possibility to plotters in plotutils

Source: https://github.com/jepegit/cellpy/issues/363

## Original issue text

I need to filter out the characterisation cycles (typically slow C-rate).

It can be done working directly on the dataframes, but it would be good to also have it accessible directly when plotting (plotutils).

Plan:

1. Add an option for having a subplot with rate in one of the summary_plot predefined sets. Should also be possible to provide nominal_capacity as optional input-parameter (so that the C-rates can be calculated properly; if so, it should scale by the new nominal_capacity (and remove the scale by the old, i.e. the objects set nominal_capacity)).

2. Add optional filtering parameter (at least for rate). Make it extendable so that we later can add more filtering options. It must be possible to filter with a "delta" (i.e. between value-delta to value+delta). Or a given range (low<value<=high).

For task 2, It would be good if the actual filtering machinery mainly lived inside the cellpy/filters folder and was also accessible as a method of the CellpyCell object.

