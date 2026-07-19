"""The 2.0 dependency budget (#570).

Four packages left the required set: ``python-box`` (replaced by a 20-line
``AttrDict``), ``ruamel.yaml`` (swapped for PyYAML, which was already in every
install as a transitive of cookiecutter), ``python-dotenv`` (guaranteed
transitively by pydantic-settings, which declares it as a hard requirement),
and ``tables`` (moved behind the ``legacy-files`` extra — the default on-disk
format is v9, so a plain install no longer pays for the HDF5 stack).

These tests pin the manifest and the behaviour that replaced each package.
"""

from __future__ import annotations

import importlib.util
import logging
import tomllib
from pathlib import Path

import pytest

from cellpy import log

log.setup_logging(default_level=logging.DEBUG, testing=True)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _bare_names(dependencies) -> set[str]:
    return {
        d.split(">")[0].split("<")[0].split("=")[0].split(";")[0].split("[")[0].strip()
        for d in dependencies
    }


# --- the manifest -------------------------------------------------------------


@pytest.mark.essential
def test_the_four_packages_left_the_required_set(pyproject):
    declared = _bare_names(pyproject["project"]["dependencies"])
    for gone in ("python-box", "ruamel.yaml", "python-dotenv", "tables"):
        assert gone not in declared, f"{gone} is back in the required dependencies"


@pytest.mark.essential
def test_pyyaml_is_declared_because_it_is_imported(pyproject):
    """Unlike dotenv, yaml has no dependency in the tree that guarantees it
    for us on purpose — cookiecutter happens to pull it today, but nothing
    about cookiecutter promises that. We import it, so we declare it."""
    declared = _bare_names(pyproject["project"]["dependencies"])
    assert "pyyaml" in declared


@pytest.mark.essential
def test_dotenv_arrives_via_its_guarantor(pyproject):
    """python-dotenv is undeclared but still imported (config/loader.py):
    pydantic-settings declares it as a hard requirement, so it is present
    wherever the config stack runs. If pydantic-settings leaves the
    dependency list, this test is the alarm."""
    declared = _bare_names(pyproject["project"]["dependencies"])
    assert "pydantic-settings" in declared
    assert importlib.util.find_spec("dotenv") is not None


@pytest.mark.essential
def test_tables_lives_in_the_legacy_files_extra(pyproject):
    extras = pyproject["project"]["optional-dependencies"]
    assert "legacy-files" in extras
    assert _bare_names(extras["legacy-files"]) == {"tables"}
    # `all` keeps its promise of being everything
    assert "tables" in _bare_names(extras["all"])


@pytest.mark.essential
def test_tables_stays_in_the_dev_group(pyproject):
    """The test suite reads and writes v8 HDF5 fixtures throughout, so dev
    environments (and both CI jobs, which run `uv sync`) must carry tables
    even though plain installs do not."""
    dev = _bare_names(pyproject["dependency-groups"]["dev"])
    assert "tables" in dev


@pytest.mark.essential
@pytest.mark.parametrize(
    "manifest",
    [
        "environment.yml",
        "environment_dev.yml",
        "github_actions_environment.yml",
        "dev/conda-recipes/cellpy/meta.yaml",
    ],
)
def test_the_dropped_packages_left_the_other_manifests(manifest):
    path = REPO_ROOT / manifest
    if not path.is_file():
        pytest.skip(f"missing {manifest}")
    text = path.read_text(encoding="utf-8")
    for gone in ("python-box", "ruamel.yaml", "python-dotenv"):
        offenders = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith(f"- {gone}")
        ]
        assert not offenders, f"{manifest} still lists {gone}"


@pytest.mark.essential
def test_no_source_file_imports_the_dropped_packages():
    """The manifest tests alone would pass with a stray import still around."""
    offenders = []
    roots = [REPO_ROOT / "cellpy", REPO_ROOT / "tests", REPO_ROOT / "dev"]
    for py in (f for root in roots for f in root.rglob("*.py")):
        if "libs" in py.parts or py.name == "test_dependency_budget.py":
            continue
        for line in py.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import box", "from box ", "from ruamel", "import ruamel")):
                offenders.append(f"{py.relative_to(REPO_ROOT)}: {stripped}")
    assert not offenders, offenders


# --- AttrDict, the box replacement --------------------------------------------


@pytest.mark.essential
def test_attrdict_behaves_like_the_box_it_replaced():
    from cellpy.parameters.prms import AttrDict

    settings = AttrDict({"default_model": "one"})
    assert settings.default_model == "one"
    settings.default_model = "two"
    assert settings["default_model"] == "two"
    assert settings.to_dict() == {"default_model": "two"}
    assert isinstance(settings.to_dict(), dict)
    with pytest.raises(AttributeError):
        settings.not_a_key


@pytest.mark.essential
def test_the_instrument_settings_still_convert_to_dicts():
    """prmreader._convert_instruments_to_dict duck-types .to_dict()."""
    from cellpy.parameters import prmreader, prms

    instruments = prms.InstrumentsClass(
        tester=None,
        custom_instrument_definitions_file=None,
        Arbin=prms.Arbin,
        Maccor=prms.Maccor,
        Neware=prms.Neware,
        Batmo=prms.Batmo,
    )
    d = prmreader._convert_instruments_to_dict(instruments)
    assert isinstance(d["Arbin"], dict)
    assert d["Arbin"]["office_version"] == prms.Arbin.office_version
    assert d["Maccor"] == {"default_model": "one"}


# --- the pyyaml swap ----------------------------------------------------------


@pytest.mark.essential
def test_migrate_still_reads_legacy_yaml():
    from cellpy.config.migrate import convert_yaml_to_toml_dict

    legacy = """---
Paths:
  outdatadir: out
Db:
  db_type: simple_excel_reader
...
"""
    converted = convert_yaml_to_toml_dict(legacy)
    assert converted, "conversion produced nothing"


@pytest.mark.essential
def test_prmreader_yaml_round_trip(tmp_path):
    """Writing and re-reading a legacy conf must survive the ruamel->pyyaml swap."""
    from cellpy.parameters import prmreader

    target = tmp_path / "_cellpy_prms_test.conf"
    prmreader._write_prm_file(target)
    assert target.is_file()

    text = target.read_text(encoding="utf-8")
    assert text.startswith("---")

    import yaml

    parsed = yaml.safe_load(text)
    assert "Paths" in parsed


# --- the pytables guard -------------------------------------------------------


@pytest.mark.essential
def test_require_hdf5_support_is_quiet_when_tables_is_present():
    from cellpy.readers.cellpy_file.format import require_hdf5_support

    require_hdf5_support("a test")  # dev env carries tables; must not raise


@pytest.mark.essential
def test_require_hdf5_support_names_the_extra(monkeypatch):
    """The error must carry its own fix."""
    import importlib.util as ilu

    from cellpy.exceptions import OptionalDependencyError
    from cellpy.readers.cellpy_file.format import require_hdf5_support

    real_find_spec = ilu.find_spec

    def missing_tables(name, *args, **kwargs):
        if name == "tables":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(ilu, "find_spec", missing_tables)

    with pytest.raises(OptionalDependencyError, match=r"legacy-files"):
        require_hdf5_support("loading an old file")


@pytest.mark.essential
def test_loading_a_v8_file_without_tables_raises_the_typed_error(monkeypatch):
    """Acceptance: the guard fires on the real load path, before pandas does."""
    import importlib.util as ilu

    from cellpy.exceptions import OptionalDependencyError
    from cellpy.readers import cellpy_file
    from tests import fdv

    source = Path(fdv.cellpy_file_path)
    if not source.is_file():
        pytest.skip("missing the standard cellpy .h5 fixture")

    real_find_spec = ilu.find_spec

    def missing_tables(name, *args, **kwargs):
        if name == "tables":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(ilu, "find_spec", missing_tables)

    with pytest.raises(OptionalDependencyError, match=r"legacy-files"):
        cellpy_file.load(source)


@pytest.mark.essential
def test_v9_files_do_not_need_tables(tmp_path, monkeypatch):
    """The whole point of the extra: the default format works without HDF5."""
    import importlib.util as ilu

    from cellpy import cellreader
    from tests import fdv

    source = Path(fdv.cellpy_file_path)
    if not source.is_file():
        pytest.skip("missing the standard cellpy .h5 fixture")

    # make the v9 file while tables is still "installed"
    c = cellreader.CellpyCell().load(source)
    v9_path = tmp_path / "roundtrip.cellpy"
    c.save(v9_path)

    real_find_spec = ilu.find_spec

    def missing_tables(name, *args, **kwargs):
        if name == "tables":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(ilu, "find_spec", missing_tables)

    reloaded = cellreader.CellpyCell().load(v9_path)
    assert len(reloaded.data.raw) == len(c.data.raw)
