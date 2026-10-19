# Issue #1152: improve function ica_collector

Source: https://github.com/jepegit/cellpy/issues/1152

## Original issue text

function does not work on some of my data. gives error: "ValueError: cycle frame is empty. The requested cycle may be missing from the source data."

why does it give this error?
make it possible to say which cells are bad, and if they are the reason for the whole function to not work. for instance skipping those bad cells, naming/printing them, and continue.
other thing to do is define in function docstring that this is possible and general edit of the information.
