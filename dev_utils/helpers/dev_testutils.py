"""Tools used for simplifying the development process"""
import os

print(79 * "=")
print("  Tools for development")
print(79 * "=")

#  how to use the tasks.py file (invoke)
#  $ invoke clean build

# some commands
PIP_DEVELOPMENT_MODE = (
    "pip install -e ."  # will install in development mode for current virtualenv
)
MAKE_DIST = "python setup.py sdist"  # creates a build with version number name
UPLOAD_PYPI = "twine upload dist/*"  # uploads to pypi (note! remove old tar-files first if using *)
# use yolk to find out latest cellpy version
FIND_CELLPY_VERSION_ON_PYPI = (
    "yolk -V cellpy"  # First you might have to install yolk: pip install yolk3k
)
FIND_ALL_REQS = "pipreqs --savepath pipreqs_requirements.txt cellpy"
RUN_COVERAGE = "pytest -cov=cellpy tests/"

# some sphinx commands
# BUILD = "sphinx-build -b html sourcedir builddir" # not used
EASY_BUILD = "make html"  # inside the docs directory to make html docs
CREATE_APIDOC = "sphinx-apidoc -o source ../cellpy"  # inside the docs directory to make .rst files for docstrings etc.

# creating conda build
# --------------------
CONDA_UPDATE_DEV = "conda env update -f dev_environment.yml"  # update your development environment first
CONDA_CREATE_DEV = (
    "conda env create -f dev_environment.yml"  # or create a development environment
)
# and then install development version of cellpy (PIP_DEVELOPMENT_MODE)
# and its probably also best to run the test
# Then edit the recipe/metal.yaml file
# Next you run the build
CONDA_BUILD = "conda build recipe"  # build conda package
# Optionally: upload to anaconda
ANACONDA_UPLOAD = "anaconda upload PATH"  # upload to conda package
# e.g. anaconda upload win-32/cellpy-0.3.0-py37_0.tar.bz2
CONVERT_CONDA_BUILDS = (
    "conda convert --platform all PATH"  # convert to different platforms
)
# e.g. conda convert --platform  all /Users/jepe/miniconda3/envs/cellpy_dev/
#                               conda-bld/osx-64/cellpy-0.3.0-py37_0.tar.bz2
# and then upload each created version individually using anaconda upload

current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_dir = "../tests"
test_dir = os.path.abspath(os.path.join(current_file_path, relative_test_dir))
# consider picking the constants directly from the test-scripts...
relative_test_data_dir = "../cellpy/data_ex"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir, test_res_file)
test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_full = os.path.join(test_data_dir, test_cellpy_file)


def create_cellpyfile_in_example_dir(force=False):
    print(79 * "=")
    print("  Create cellpy-file in example folder")
    print(79 * "-")
    from cellpy import cellreader

    if os.path.isfile(test_cellpy_file_full):
        print("cellpy-file exists")
        print(test_cellpy_file_full)
    else:
        print("cellpy-file does not exist")
        print("creating")
        print(test_cellpy_file_full)
        force = True
    if force:
        d = cellreader.CellpyData()
        d.loadcell(test_res_file_full)
        d.make_summary(find_ir=True)
        d.make_step_table()
        d.save(test_cellpy_file_full)
    print(79 * "=")


if __name__ == "__main__":
    create_cellpyfile_in_example_dir()
