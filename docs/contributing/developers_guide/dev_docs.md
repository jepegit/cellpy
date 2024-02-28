```{highlight} shell
```

# Writing documentation

All contributions to documenting `cellpy` is highly welcomed.

## Types of documentation

Code can be documented by several means. All are valuable. For example:

- adding examples to the `examples` folder
- improving the documentation in the `docs` folder
- improving the doc-strings in the code
- adding descriptive tests to the code
- providing example data (e.g. raw-files in different formats)
- tutorials on YouTube
- blogs etc.
- apps

## Add examples to the examples folder

The examples folder is a good place to add examples of how to
use `cellpy`. The examples should be self-contained
and easy to understand. It is recommended to use Jupyter notebooks (but not required).

Another contribution could be to add example data.

## Working on the main documentation

The docs are hosted on Read the Docs

- Stable: <https://cellpy.readthedocs.io/en/stable/>
- Latest: <https://cellpy.readthedocs.io/en/latest/>
- Admin: <https://readthedocs.org/projects/cellpy/>

Sphinx is used to render the documentation.

Link to help: <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>

Notebooks can also be used.

### Sphinx tooling

List of extensions used
- sphinx.ext.inheritance_diagram
- sphinx.ext.viewcode
- sphinx.ext.napoleon
- sphinx.ext.intersphinx
- myst_parser
- sphinx.ext.graphviz,
- nbsphinx
- autoapi.extension

Current HTML theme:

- sphinx_book_theme

Available variables:

```
ProjectVersion -> writes version number
```

Dependencies:

- python >=3.10
- pip
- Sphinx
- pandoc
- nbsphinx
- myst-parser
- sphinx-autoapi
- graphviz
- sphinx-book-theme


API documentation is created by autoapi.

### Doc-strings

- Use Google-style doc-strings
- In addition to the standard admonitions, you can also use:
  - Transferred Arguments
  - See Also

## Tests

- Use pytest
- Use descriptive test names
- Use fixtures and try to keep the tests organized in a logical way
- Use the `conftest.py` file to keep fixtures and other common stuff
- Parameters and variables (e.g. filenames) can be defined in the `fdv.py` file.
