import logging
import os
import tempfile
import time

import pytest

import cellpy.readers.data_structures
import cellpy.utils.helpers
from cellpy import config, log

from . import fdv

log.setup_logging(default_level="DEBUG", testing=True)


def test_conftest(hello_world):
    assert hello_world == "hello cellpy!"


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def setup_module():
    import os

    try:
        os.mkdir(fdv.output_dir)
    except Exception:
        print("could not make directory")


def test_logger(clean_dir):
    test_logging_json = os.path.join(fdv.data_dir, "test_logging.json")
    config.paths.filelogdir = fdv.log_dir

    log.setup_logging(testing=True)
    tmp_logger = logging.getLogger()
    assert tmp_logger.level == logging.DEBUG

    tmp_logger.info("default: testing logger (info)")
    tmp_logger.debug("default: testing logger (debug)")
    tmp_logger.error("default: testing logger (error)")

    for handler in tmp_logger.handlers:
        if handler.name == "console":
            assert handler.level == logging.CRITICAL
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(default_level="DEBUG", testing=True)
    tmp_logger = logging.getLogger()
    tmp_logger.info("default: testing logger (info)")
    tmp_logger.debug("default: testing logger (debug)")
    tmp_logger.error("default: testing logger (error)")

    for handler in tmp_logger.handlers:
        if handler.name == "console":
            assert handler.level == logging.DEBUG
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(default_level="INFO", testing=True)
    for handler in logging.getLogger().handlers:
        if handler.name == "console":
            assert handler.level == logging.INFO
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(
        default_json_path="./a_file_that_does_not_exist.json", testing=True
    )
    assert len(logging.getLogger().handlers) == 4

    log.setup_logging(default_json_path=test_logging_json, testing=True)
    log.setup_logging(custom_log_dir=clean_dir)
    tmp_logger = logging.getLogger()
    tmp_logger.info("customdir, default: testing logger (info)")
    tmp_logger.debug("customdir, default: testing logger (debug)")
    tmp_logger.error("customdir, default: testing logger (error)")


def test_logger_advanced(clean_dir):
    log.setup_logging(reset_big_log=True, testing=True)
    tmp_logger = logging.getLogger()
    tmp_logger.info("customdir, default: testing logger (info)")
    tmp_logger.debug("customdir, default: testing logger (debug)")
    tmp_logger.error("customdir, default: testing logger (error)")
    for handler in logging.getLogger().handlers:
        if handler.name == "console":
            assert handler.level == logging.CRITICAL
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG


@pytest.mark.timeout(5.0)
def test_load_and_save_res_file(clean_dir):
    import os

    f_in = os.path.join(fdv.raw_data_dir, fdv.res_file_name)
    new_file = cellpy.utils.helpers.load_and_save_resfile(f_in, None, clean_dir)
    assert os.path.isfile(new_file)


@pytest.mark.benchmark(
    group="group-name",
    min_time=0.1,
    max_time=0.5,
    min_rounds=2,
    timer=time.time,
    disable_gc=True,
    warmup=False,
)
def test_load_arbin_res_file_diagnostics(clean_dir, benchmark):
    import os

    from cellpy import prms

    config.reader.diagnostics = True
    f_in = os.path.join(fdv.raw_data_dir, fdv.res_file_name)
    new_file = benchmark(
        cellpy.utils.helpers.load_and_save_resfile, f_in, None, clean_dir
    )
    assert os.path.isfile(new_file)


def test_get_pec():
    print()
    print(" load pec file ".center(80, "-"))
    print(fdv.pec_file_path)
    cellpy.get(
        filename=fdv.pec_file_path,
        logging_mode="DEBUG",
        instrument="pec_csv",
        mass=50_000,
        cycle_mode="cathode",
        testing=True,
    )


@pytest.mark.essential
def test_get_cellpy():
    cellpy.get(filename=fdv.cellpy_file_path, testing=True)


@pytest.mark.essential
def test_get_h5_instrument_skips_native_autopick(monkeypatch, tmp_path):
    """instrument= on .h5 must not route through CellpyCell.load (#819)."""
    from cellpy.readers.cellreader import CellpyCell

    h5_path = tmp_path / "raw_sample.h5"
    h5_path.write_bytes(b"not-a-cellpy-file")
    cellpy_path = tmp_path / "native_sample.cellpy"
    cellpy_path.write_bytes(b"not-a-cellpy-file")
    routes = {"load": 0, "from_raw": 0}

    def fake_load(self, *args, **kwargs):
        routes["load"] += 1

    def fake_from_raw(self, *args, **kwargs):
        routes["from_raw"] += 1

    monkeypatch.setattr(CellpyCell, "load", fake_load)
    monkeypatch.setattr(CellpyCell, "from_raw", fake_from_raw)
    monkeypatch.setattr(CellpyCell, "set_instrument", lambda self, **kwargs: None)
    monkeypatch.setattr(CellpyCell, "__bool__", lambda self: True)

    import cellpy

    cellpy.get(
        filename=str(h5_path),
        instrument="arbin_sql_h5",
        auto_summary=False,
        testing=True,
    )
    assert routes["from_raw"] == 1
    assert routes["load"] == 0

    routes["load"] = routes["from_raw"] = 0
    cellpy.get(filename=str(h5_path), auto_summary=False, testing=True)
    assert routes["load"] == 1
    assert routes["from_raw"] == 0

    routes["load"] = routes["from_raw"] = 0
    cellpy.get(
        filename=str(cellpy_path),
        instrument="arbin_res",
        auto_summary=False,
        testing=True,
    )
    assert routes["load"] == 1
    assert routes["from_raw"] == 0


def test_get_empty():
    cellpy.get(testing=True)


def test_get_cellpy_with_post_processor_hook():
    def _my_post_processor(c):
        print(c)
        return c

    cellpy.get(
        filename=fdv.cellpy_file_path,
        post_processor_hook=_my_post_processor,
        testing=True,
    )  # should only give a warning


@pytest.mark.essential
def test_get_arbin_res_with_postprocessor_hook():
    def _my_post_processor(c):
        print(c)
        return c

    cellpy.get(
        filename=fdv.res_file_path, post_processor_hook=_my_post_processor, testing=True
    )  # should print


# @pytest.mark.unimportant
def test_humanize_bytes():
    assert cellpy.readers.data_structures.humanize_bytes(1) == "1 byte"
    assert cellpy.readers.data_structures.humanize_bytes(1024) == "1.0 kB"
    assert cellpy.readers.data_structures.humanize_bytes(1024 * 123) == "123.0 kB"
    assert cellpy.readers.data_structures.humanize_bytes(1024 * 12342) == "12.0 MB"
    assert cellpy.readers.data_structures.humanize_bytes(1024 * 12342, 2) == "12.00 MB"
    assert cellpy.readers.data_structures.humanize_bytes(1024 * 1234, 2) == "1.00 MB"
    assert cellpy.readers.data_structures.humanize_bytes(1024 * 1234 * 1111, 2) == "1.00 GB"
    assert cellpy.readers.data_structures.humanize_bytes(1024 * 1234 * 1111, 1) == "1.0 GB"


@pytest.mark.essential
def test_make_step_table():
    c = cellpy.get(
        fdv.res_file_path,
        nominal_capacity=3600,
        mass=0.74,
        logging_mode="DEBUG",
        auto_summary=False,
        testing=True,
    )
    c.make_step_table()


def teardown_module():
    import shutil

    shutil.rmtree(fdv.output_dir)
