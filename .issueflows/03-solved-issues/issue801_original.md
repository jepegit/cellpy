# Issue #801: App-friendly collected figures: theme / label / height hook (or pass a FigureSpec)

Source: https://github.com/jepegit/cellpy/issues/801

## Original issue text

Split from #791 (item c). `collected_plot` returns faceted figures with default plotly styling (mirror axis boxes, right-side facet titles spelled `variable=charge_capacity_gravimetric`, auto height growing with facet count). A **theme / label / height hook** (or a `FigureSpec` the caller can pass) would let apps drop the figure in without re-styling every one.

Relates to the plotting `FigureSpec` pipeline and SPEED-30 label work.
