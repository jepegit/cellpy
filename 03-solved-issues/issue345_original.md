# Issue #345: batch - read custom json

Source: https://github.com/jepegit/cellpy/issues/345

## Original issue text

The batch utility should be able to get info from other JSON files than the currently supported ones.

We also need to allow for file searching after reading the JSON file.


# User story

User is using batbase (web interface / db) and selects the tests he wants to look at. He downloads in json format.

The user points cellpy batch to the downloaded file.

e.g. >> b = batch.load(batbase_journalfile.json)  # maybe we need to add a keyword argument, e.g. filetype = "batbase_v1"

batch reads the file, checks, and populates the journal (pages). Then batch continues as it normally do. The test filename indicators are used by cellpy filefinder as usual and both raw files field is populated as well as the appropriate cellpy filenames.