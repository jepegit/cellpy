# Set up your experiment using `cellpy_cookie_NAME` <- insert correct name here

The main reason for this repository is to let you easily create
a structure for performing a proper `cellpy` session.

The following template is suitable when processing a set of files
using the batch utility.


## Content

```bash

cellpy_project/
└── experiment_001
    ├── batch_file.json
    ├── data
    │   ├── external
    │   ├── interim
    │   ├── processed
    │   └── raw
    ├── out
    │   └── note.md
    ├── notebook: 01_experiment_001_processing.ipynb


```

## Notes
Remember to save your notebooks.