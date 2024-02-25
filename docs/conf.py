import os
import sys

INCLUDE_SOURCE_FILES = False

project_root = os.path.abspath("../")
name = "cellpy"
version_ns = {}
with open(os.path.join(project_root, name, "_version.py")) as f:
    exec(f.read(), {}, version_ns)

if INCLUDE_SOURCE_FILES:
    project_prmsdir = os.path.join(project_root, r"cellpy\parameters")
    project_utils = os.path.join(project_root, r"cellpy\utils")
    project_scripts = os.path.join(project_root, r"cellpy\scripts")
    project_readers = os.path.join(project_root, r"cellpy\readers")
    project_internals = os.path.join(project_root, r"cellpy\internals")

    sys.path.insert(0, project_root)
    sys.path.insert(0, project_prmsdir)
    sys.path.insert(0, project_utils)
    sys.path.insert(0, project_scripts)
    sys.path.insert(0, project_readers)
    sys.path.insert(0, project_internals)

extensions = [
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    # "myst_nb",
    "myst_parser",
    "sphinx.ext.graphviz",
    # "autodoc2",
    "nbsphinx",
    "autoapi.extension",
]

# Note about myst_nb:
# It is possible to use myst_nb (that can parse notebooks with myst markdown)
# instead of nbsphinx, but at the moment it is difficult to get the plotly plots to
# work properly. Setting plotly to make the plots in iframes is a workaround, but
# this will only work smoothly if the jupyter notebook are in the root of the documentation
# folder. If not, the paths to the plots (iframes) will be wrong (and you will have to copy the folder with
# the iframes somehow to the same location as the built notebooks).

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "cellpy"
copyright = "2024, Jan Petter Maehlen"
version = version_ns["__version__"]
release = version_ns["__version__"]

exclude_patterns = [
    "_build",
    "_autoapi_templates",
    "jupyter_execute",
    "examples/.ipnb_checkpoints",
]

add_function_parentheses = True
add_module_names = False
pygments_style = "sphinx"
modindex_common_prefix = ["cellpy."]

html_theme = "sphinx_book_theme"
html_theme_path = ["_themes"]
html_static_path = ["_static"]
# html_js_files = ["js/plotly-latest.min.js"]
# html_css_files = ["css/cellpy.css"]
htmlhelp_basename = "cellpydoc"
latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #'preamble': '',
}
latex_documents = [
    ("index", "cellpy.tex", "cellpy Documentation", "Jan Petter Maehlen", "manual")
]
man_pages = [("index", "cellpy", "cellpy Documentation", ["Jan Petter Maehlen"], 1)]
texinfo_documents = [
    (
        "index",
        "cellpy",
        "cellpy Documentation",
        "Jan Petter Maehlen",
        "cellpy",
        "Utilities for handling data from battery cell cycling.",
        "Miscellaneous",
    )
]
nbsphinx_kernel_name = "python3"
nbsphinx_execute = "never"
autoapi_dirs = ["../cellpy"]
# autodoc2_packages = ["../cellpy"]
autoapi_template_dir = "_templates/_autoapi_templates"

# autodoc2_render_plugin = "myst"

autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "show-inheritance-diagram",
]
autoapi_ignore = ["*dev_*"]
autoapi_python_class_content = "both"
autoapi_member_order = "groupwise"
autoapi_keep_files = True
# myst settings
# see https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
myst_enable_extensions = [
    "colon_fence",
    "substitution",
]
myst_substitutions = {
    "ProjectVersion": version,
}

# nb_execution_mode = "cache"
# nb_execution_in_temp = True
