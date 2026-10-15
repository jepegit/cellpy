# Issue #1131: possible nominal capacity confusion

Source: https://github.com/jepegit/cellpy/issues/1131

## Original issue text

Several of the batches I have opened with cellpy-simple-gui have the nominal capacity given in Ah/g. Cellpy-simple-gui thinks it is in mAh/g. And I also think it should be that. Did we have a bug in cellpy earlier that created this (it could be the journal loader)? Might we still have this bug? Or is it just something wrong in the cellpy db (Excel sheet)? Do a thorough check at least to rule out this for the current cellpy version.
