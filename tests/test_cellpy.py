import pytest
import tempfile
import os
import logging
import time

import cellpy.readers.core
from cellpy import log
from cellpy import prms
from . import fdv

log.setup_logging(default_level="DEBUG")


@pytest.fixture(scope="module")
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.CellpyData()


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def setup_module():
    import os
    try:
        os.mkdir(fdv.output_dir)
    except:
        print("could not make directory")


def test_logger(clean_dir):
    test_logging_json = os.path.join(fdv.data_dir, "test_logging.json")
    prms.Paths["filelogdir"] = fdv.log_dir

    log.setup_logging()
    tmp_logger = logging.getLogger()
    assert tmp_logger.level == logging.DEBUG

    tmp_logger.info("default: testing logger (info)")
    tmp_logger.debug("default: testing logger (debug)")
    tmp_logger.error("default: testing logger (error)")

    for handler in tmp_logger.handlers:
        if handler.name == "console":
            assert handler.level == logging.INFO
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(default_level="DEBUG")
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

    log.setup_logging(default_level="INFO")
    for handler in logging.getLogger().handlers:
        if handler.name == "console":
            assert handler.level == logging.INFO
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(default_json_path="./a_file_that_does_not_exist.json")
    assert len(logging.getLogger().handlers) == 4

    log.setup_logging(default_json_path=test_logging_json)
    log.setup_logging(custom_log_dir=clean_dir)
    tmp_logger = logging.getLogger()
    tmp_logger.info("customdir, default: testing logger (info)")
    tmp_logger.debug("customdir, default: testing logger (debug)")
    tmp_logger.error("customdir, default: testing logger (error)")


@pytest.mark.timeout(2.0)
def test_load_and_save_resfile(clean_dir):
    import os
    from cellpy import cellreader
    f_in = os.path.join(fdv.raw_data_dir, fdv.res_file_name)
    new_file = cellreader.load_and_save_resfile(f_in, None, clean_dir)
    assert os.path.isfile(new_file)


@pytest.mark.benchmark(
    group="group-name",
    min_time=0.1,
    max_time=0.5,
    min_rounds=2,
    timer=time.time,
    disable_gc=True,
    warmup=False
)
def test_load_resfile_diagnostics(clean_dir, benchmark):
    import os
    from cellpy import cellreader
    from cellpy import prms
    prms.Reader.diagnostics = True
    f_in = os.path.join(fdv.raw_data_dir, fdv.res_file_name)
    new_file = benchmark(
        cellreader.load_and_save_resfile,
        f_in,
        None,
        clean_dir
    )
    assert os.path.isfile(new_file)


def test_su_cellpy_instance():
    # somehow pytest fails to find the test if it is called test_setup_xxx
    from cellpy import cellreader
    cellreader.setup_cellpy_instance()


def test_cell():
    import cellpy
    cellpy.cell(
        filename=fdv.pec_file_path,
        instrument="pec_csv",
        mass=50_000,
        cycle_mode="cathode",
    )
    cellpy.cell(
        filename=fdv.cellpy_file_path,
    )
    cellpy.cell()


@pytest.mark.slowtest
@pytest.mark.smoketest
def test_just_load_srno():
    from cellpy import cellreader
    assert cellreader.just_load_srno(614) is True


@pytest.mark.smoketest
def test_setup_cellpy_instance():
    from cellpy import cellreader
    d = cellreader.setup_cellpy_instance()


# @pytest.mark.unimportant
def test_humanize_bytes():
    from cellpy import cellreader
    assert cellpy.readers.core.humanize_bytes(1) == '1 byte'
    assert cellpy.readers.core.humanize_bytes(1024) == '1.0 kB'
    assert cellpy.readers.core.humanize_bytes(1024 * 123) == '123.0 kB'
    assert cellpy.readers.core.humanize_bytes(1024 * 12342) == '12.0 MB'
    assert cellpy.readers.core.humanize_bytes(1024 * 12342, 2) == '12.00 MB'
    assert cellpy.readers.core.humanize_bytes(1024 * 1234, 2) == '1.00 MB'
    assert cellpy.readers.core.humanize_bytes(1024 * 1234 * 1111, 2) == '1.00 GB'
    assert cellpy.readers.core.humanize_bytes(1024 * 1234 * 1111, 1) == '1.0 GB'


def teardown_module():
    import shutil
    shutil.rmtree(fdv.output_dir)

