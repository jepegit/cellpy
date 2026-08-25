# Issue #947: collector plots missing units

Source: https://github.com/jepegit/cellpy/issues/947

## Original issue text

Check if this is still a problem, or if it is fixed

Units on y-axis labels are missing!

```python
# pick the summary columns you want - without `columns` you get every summary
# column, and the plot gets one facet per column
cap_summaries = summary_collector(
b,
columns=[
"charge_capacity_gravimetric",
"discharge_capacity_gravimetric",
"coulombic_efficiency",
],
group_it=True,
custom_group_labels={
1: "run-14",
2: "run-15",
},
)
```

<img width="2297" height="1517" alt="Image" src="https://github.com/user-attachments/assets/a665d310-3aa6-42af-b317-bf2d6a12188b" />

## Comments (curated summary)

- **Additional tasks**:
  - Legend must use `custom_group_labels` (e.g. `run-14` / `run-15`), not bare group numbers.
  - Confirm vertical facet order matches the `columns=` argument; document it if that order is deliberate.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 3, last comment by @jepegit on 2026-08-25._
