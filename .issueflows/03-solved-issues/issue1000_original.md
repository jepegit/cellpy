# Issue #1000: prepare for changes in batch journal json file

Source: https://github.com/jepegit/cellpy/issues/1000

## Original issue text

We do not have any version label for the batch journal file. We should add it. Let us say that if the file misses the version label, it is version 1 (i.e. 1). It can also have the version label with 1 (and new files should be saved with the version number. Then when we decide to change the format, we can bump the version number.

Obviously, we also need to implement reading and saving the version number and prepare for possible version bumps.
