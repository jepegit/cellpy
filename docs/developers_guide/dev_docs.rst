.. highlight:: shell

Writing documentation
=====================

All contributions on documenting ``cellpy`` is highly welcomed.

Types of documentation
----------------------

Code can be documented by several means. All are valuable. For example:

- adding examples to the `examples` folder
- improving the documentation in the `docs` folder
- improving the doc-strings in the code
- adding descriptive tests to the code
- providing example data (e.g. raw-files in different formats)
- tutorials on YouTube
- blogs etc.
- apps

Add examples to the examples folder
-----------------------------------

Todo


Working on the main documentation
---------------------------------

The docs are hosted on Read the Docs

- Stable: https://cellpy.readthedocs.io/en/stable/
- Latest: https://cellpy.readthedocs.io/en/latest/
- Admin: https://readthedocs.org/projects/cellpy/

Sphinx is used to render the documentation.

Link to help: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

Notebooks can also be used.

Sphinx tooling
..............

List of extensions used

- sphinx.ext.autodoc
- sphinx.ext.viewcode
- sphinx.ext.napoleon
- sphinx.ext.intersphinx
- nbsphinx
- sphinx.ext.graphviz

Current HTML theme:

- sphinx_rtd_theme

Available "variables"::

    |ProjectVersion| -> writes "Version: <version number>"

Dependencies (python packages):

- pandoc
- sphinx-rtd-theme
- nbsphinx

Dependencies (non-python):

- pandoc
- graphviz

Creating the API documentation::

    # in the repository root folder
    sphinx-apidoc -o docs/source cellpy/


Conventions
...........

Order of headers::

    ========
    Header 1
    ========

    Header 2
    ========

    Header 3
    --------

    Header 4
    ........

    Header 5
    ~~~~~~~~

Note that many of the documents (.rst files) are linked through an
`index.rst` file. This file most likely contains the Header 1, so the
actual document you are working on needs to start with Header 2.

Doc-strings
-----------

Todo


Tests
-----

Todo

