# Issue #982: Default group name from cellpy_db

Source: https://github.com/jepegit/cellpy/issues/982

## Original issue text

In cellpy_db, there is a column called group. I often use it to describe what makes a few cells in one batrch different from some of the others in the same batch. The name I use, is often what I would end up setting as `custom_group_labels` in the `summary_collector` function later. Therefore, it would be very nice if cellpy could just read the text given in the "group" column in cellpy_db and use that as default.
