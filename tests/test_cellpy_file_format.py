"""Tests for cellpy-file format spec (Stage 1.1, issue #446)."""

from __future__ import annotations

import pytest

from cellpy import prms
from cellpy.parameters import internal_settings
from cellpy.readers.cellpy_file.format import (
    CELLPY_FILE_VERSION,
    MINIMUM_CELLPY_FILE_VERSION,
    FORMAT_V4,
    FORMAT_V8,
    get_format,
)


@pytest.mark.essential
def test_format_v8_matches_prms_aliases():
    fmt = FORMAT_V8
    assert prms._cellpyfile_root == fmt.root
    assert prms._cellpyfile_raw == fmt.raw_dir
    assert prms._cellpyfile_step == fmt.step_dir
    assert prms._cellpyfile_summary == fmt.summary_dir
    assert prms._cellpyfile_fid == fmt.fid_dir
    assert prms._cellpyfile_common_meta == fmt.common_meta_dir
    assert prms._cellpyfile_test_dependent_meta == fmt.test_dependent_meta_dir
    assert prms._cellpyfile_raw_unit_pre_id == fmt.raw_unit_prefix
    assert prms._cellpyfile_raw_limit_pre_id == fmt.raw_limit_prefix
    assert prms._cellpyfile_complevel == fmt.complevel
    assert prms._cellpyfile_complib == fmt.complib
    assert prms._cellpyfile_raw_format == fmt.raw_format
    assert prms._cellpyfile_summary_format == fmt.summary_format
    assert prms._cellpyfile_stepdata_format == fmt.stepdata_format
    assert prms._cellpyfile_infotable_format == fmt.infotable_format
    assert prms._cellpyfile_fidtable_format == fmt.fidtable_format


@pytest.mark.essential
def test_v8_raw_limit_prefix_empty():
    assert FORMAT_V8.raw_limit_prefix == ""
    assert prms._cellpyfile_raw_limit_pre_id == ""


@pytest.mark.essential
def test_get_format_version_dispatch():
    v4 = get_format(4)
    assert v4.raw_dir == "/dfdata"
    assert v4.step_dir == "/step_table"
    assert v4.summary_dir == "/dfsummary"
    assert v4.fid_dir == "/fidtable"

    for version in (5, 6, 7, 8):
        fmt = get_format(version)
        assert fmt.raw_dir == "/raw"
        assert fmt.step_dir == "/steps"
        assert fmt.version == version


def test_version_constants_match_internal_settings():
    assert CELLPY_FILE_VERSION == internal_settings.CELLPY_FILE_VERSION
    assert MINIMUM_CELLPY_FILE_VERSION == internal_settings.MINIMUM_CELLPY_FILE_VERSION
