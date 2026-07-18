"""Tabular exporters for CellpyCell (issue #518, V2-09 follow-up).

Moved verbatim from ``cellreader.py`` (the ``# TODO @jepe: move this to its
own module (e.g. as a cellpy-exporters?)`` cluster), following the #509
``capacity_curves`` pattern: functions take the ``CellpyCell`` instance as
their first argument; ``CellpyCell`` keeps thin delegate methods with
identical signatures, so the public API is unchanged. Cross-calls go through
the instance (``cell.get_cap(...)``, ``cell._export_normal(...)`` ...) to
preserve subclass dispatch exactly as before the move.

``cap_mod_summary`` / ``cap_mod_normal`` are not exporters but rode along in
the same cellreader cluster; they are near-dead (test-pinned only) and their
removal is deferred to the DI restructuring pass (#520).
"""

import csv
import datetime
import itertools
import logging
import os
import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from cellpycore.config import CurveCols

from cellpy.exceptions import NoDataFound
from cellpy.readers import externals

# get_cap emits native CurveCols names (#540): potential/cycle_num, not
# voltage/cycle.
_CCOLS = CurveCols()

if TYPE_CHECKING:
    from cellpy.readers.cellreader import CellpyCell


def export_cycles(
    cell: "CellpyCell",
    setname=None,
    sep=None,
    outname=None,
    shifted=False,
    method=None,
    shift=0.0,
    last_cycle=None,
):
    """Export voltage-capacity curves to a .csv file."""
    logging.debug("START exporing cycles")
    time_00 = time.time()
    lastname = "_cycles.csv"
    if sep is None:
        sep = cell.sep
    if outname is None:
        outname = setname + lastname

    logging.debug(f"outname: {outname}")

    list_of_cycles = cell.get_cycle_numbers()
    if last_cycle is not None:
        list_of_cycles = [c for c in list_of_cycles if c <= int(last_cycle)]
        logging.debug(f"only processing up to cycle {last_cycle}")
        logging.debug(f"you have {len(list_of_cycles)}cycles to process")
    out_data = []
    c = None
    if not method:
        method = "back-and-forth"
    if shifted:
        method = "back-and-forth"
        shift = 0.0
        _last = 0.0
    logging.debug(f"number of cycles: {len(list_of_cycles)}")
    for cycle in list_of_cycles:
        try:
            if shifted and c is not None:
                shift = _last
                # print(f"shifted = {shift}, first={_first}")
            df = cell.get_cap(cycle, method=method, shift=shift)
            if df.empty:
                logging.debug("NoneType from get_cap")
            else:
                c = df[_CCOLS.capacity]
                v = df[_CCOLS.potential]

                _last = c.iat[-1]
                _first = c.iat[0]

                c = c.tolist()
                v = v.tolist()
                header_x = "cap cycle_no %i" % cycle
                header_y = "voltage cycle_no %i" % cycle
                c.insert(0, header_x)
                v.insert(0, header_y)
                out_data.append(c)
                out_data.append(v)
                # txt = "extracted cycle %i" % cycle
                # logging.debug(txt)
        except IndexError as e:
            txt = "Could not extract cycle %i" % cycle
            logging.info(txt)
            logging.debug(e)

    # Saving cycles in one .csv file (x,y,x,y,x,y...)
    # print "saving the file with delimiter '%s' " % (sep)
    logging.debug("writing cycles to file")
    with open(outname, "w", newline="") as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(itertools.zip_longest(*out_data))
        # star (or asterix) means transpose (writing cols instead of rows)

    logging.info(f"The file {outname} was created")
    logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
    logging.debug("END exporting cycles")


def export_normal(cell: "CellpyCell", data, setname=None, sep=None, outname=None):
    """Export the raw frame to a .csv file."""
    time_00 = time.time()
    lastname = "_normal.csv"
    if sep is None:
        sep = cell.sep
    if outname is None:
        outname = setname + lastname
    txt = outname
    try:
        data.raw.to_csv(outname, sep=sep)
        txt += " OK"
    except Exception as e:
        txt += " Could not save it!"
        logging.debug(e)
        warnings.warn(f"Unhandled exception raised: {e}")
    logging.info(txt)
    logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")


def export_stats(cell: "CellpyCell", data, setname=None, sep=None, outname=None):
    """Export the summary frame to a .csv file."""
    time_00 = time.time()
    lastname = "_stats.csv"
    if sep is None:
        sep = cell.sep
    if outname is None:
        outname = setname + lastname
    txt = outname
    try:
        data.summary.to_csv(outname, sep=sep)
        txt += " OK"
    except Exception as e:
        txt += " Could not save it!"
        logging.debug(e)
        warnings.warn(f"Unhandled exception raised: {e}")
    logging.info(txt)
    logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")


def export_steptable(cell: "CellpyCell", data, setname=None, sep=None, outname=None):
    """Export the steps frame to a .csv file."""
    # TODO 259: rename to _export_steps_csv
    time_00 = time.time()
    lastname = "_steps.csv"
    if sep is None:
        sep = cell.sep
    if outname is None:
        outname = setname + lastname
    txt = outname
    try:
        data.steps.to_csv(outname, sep=sep)
        txt += " OK"
    except Exception as e:
        txt += " Could not save it!"
        logging.debug(e)
        warnings.warn(f"Unhandled exception raised: {e}")
    logging.info(txt)
    logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")


def to_excel(
    cell: "CellpyCell",
    filename=None,
    cycles=None,
    raw=False,
    steps=True,
    nice=True,
    get_cap_kwargs=None,
    to_excel_kwargs=None,
):
    """Saves the data as .xlsx file(s).

    Args:
        cell: the CellpyCell instance.
        filename: name of the Excel file.
        cycles: (None, bool, or list of ints) export voltage-capacity curves if given.
        raw: (bool) export raw-data if True.
        steps: (bool) export steps if True.
        nice: (bool) use nice formatting if True.
        get_cap_kwargs: (dict) kwargs for CellpyCell.get_cap method.
        to_excel_kwargs: (dict) kwargs for pandas.DataFrame.to_excel method.
    """
    to_excel_method_kwargs = {"index": True, "header": True}
    get_cap_method_kwargs = {
        "method": "forth-and-forth",
        "label_cycle_number": True,
        "categorical_column": True,
        "interpolated": True,
        "number_of_points": 1000,
        "capacity_then_voltage": True,
    }
    if to_excel_kwargs is not None:
        to_excel_method_kwargs.update(to_excel_kwargs)
    if get_cap_kwargs is not None:
        get_cap_method_kwargs.update(get_cap_kwargs)

    border = externals.openpyxl.styles.Border()
    face_color = "00EEEEEE"
    meta_alignment_left = externals.openpyxl.styles.Alignment(
        horizontal="left", vertical="bottom"
    )
    meta_width = 34
    meta_alignment_right = externals.openpyxl.styles.Alignment(
        horizontal="right", vertical="bottom"
    )
    fill = externals.openpyxl.styles.PatternFill(
        start_color=face_color, end_color=face_color, fill_type="solid"
    )

    if filename is None:
        pre = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pre}_cellpy.xlsx"
        filename = Path(filename).resolve()
        logging.critical(f"generating filename: {filename}")

    summary_frame = cell.data.summary
    meta_common_frame = cell.data.meta_common.to_frame()
    meta_test_dependent_frame = cell.data.meta_test_dependent.to_frame()
    cellpy_units = cell.cellpy_units.to_frame()
    cellpy_units.index = "cellpy_units_" + cellpy_units.index
    raw_units = cell.raw_units.to_frame()
    raw_units.index = "raw_units_" + raw_units.index

    meta_common_frame = externals.pandas.concat(
        [meta_common_frame, cellpy_units, raw_units]
    )

    with externals.pandas.ExcelWriter(filename, engine="openpyxl") as writer:
        meta_common_frame.to_excel(
            writer, sheet_name="meta_common", **to_excel_method_kwargs
        )
        meta_test_dependent_frame.to_excel(
            writer, sheet_name="meta_test_dependent", **to_excel_method_kwargs
        )
        summary_frame.to_excel(writer, sheet_name="summary", **to_excel_method_kwargs)

        if raw:
            # TODO: raw-table has two columns called "data_point" at the moment,
            #  so this should be fixed (probably the .set_index("data_point") should be checked)
            logging.debug("exporting raw data")
            raw = cell.data.raw
            max_len = 1_048_576
            if len(raw) < max_len:
                raw.to_excel(writer, sheet_name="raw", **to_excel_method_kwargs)
            else:
                logging.warning(
                    "Raw data is too large to fit in one sheet. "
                    "Splitting raw data into chunks. This is not tested yet"
                )
                n_chunks = len(raw) // max_len + 1
                for i in range(n_chunks):
                    raw.iloc[i * max_len : (i + 1) * max_len].to_excel(
                        writer, sheet_name=f"raw_{i:02}", **to_excel_method_kwargs
                    )

        if steps:
            logging.debug("exporting steps")
            # TODO: step-table has a columns called "index" at the moment,
            #  so setting index=False for dataframe.to_excel
            #  Maybe best to make sure that step table does not have a column called "index" in the future?
            cell.data.steps.to_excel(
                writer, sheet_name="steps", index=False, header=True
            )
        if cycles:
            logging.debug("exporting cycles")
            if cycles is True:
                cycles = cell.get_cycle_numbers()
            for cycle in cycles:
                try:
                    _curves = cell.get_cap(cycle=cycle, **get_cap_method_kwargs)
                    _curves.to_excel(
                        writer,
                        sheet_name=f"cycle_{cycle:03}",
                        index=False,
                        header=True,
                    )
                except Exception as e:
                    logging.debug(f"Could not export cycle {cycle}: {e}")
                    continue
        if nice:
            for sheet in writer.sheets.values():
                if sheet.title.startswith("meta"):
                    sheet.column_dimensions["A"].width = meta_width
                    for xl_cell in sheet["A"]:
                        xl_cell.alignment = meta_alignment_left
                        xl_cell.border = border
                    for xl_cell in sheet["B"]:
                        xl_cell.alignment = meta_alignment_right
                        xl_cell.border = border
                else:
                    for xl_cell in sheet["A"]:
                        xl_cell.border = border

                for xl_cell in sheet["1"]:
                    xl_cell.border = border
                    xl_cell.fill = fill


def to_csv(
    cell: "CellpyCell",
    datadir=None,
    sep=None,
    cycles=False,
    raw=True,
    summary=True,
    shifted=False,
    method=None,
    shift=0.0,
    last_cycle=None,
):
    """Saves the data as .csv file(s).

    Args:
        cell: the CellpyCell instance.
        datadir: folder where to save the data (uses current folder if not
            given).
        sep: the separator to use in the csv file
            (defaults to CellpyCell.sep).
        cycles: (bool) export voltage-capacity curves if True.
        raw: (bool) export raw-data if True.
        summary: (bool) export summary if True.
        shifted (bool): export with cumulated shift.
        method (str): how the curves are given:

            - "back-and-forth" - standard back and forth; discharge (or charge)
              reversed from where charge (or discharge) ends.
            - "forth" - discharge (or charge) continues along x-axis.
            - "forth-and-forth" - discharge (or charge) also starts at 0
              (or shift if not shift=0.0)

        shift: start-value for charge (or discharge)
        last_cycle: process only up to this cycle (if not None).

    Returns:
        None

    """
    if sep is None:
        sep = cell.sep

    logging.debug("saving to csv")

    try:
        data = cell.data
    except NoDataFound:
        logging.info("to_csv -")
        logging.info("NoDataFound: not saved!")
        return

    if isinstance(data.loaded_from, (list, tuple)):
        txt = "merged file"
        txt += "using first file as basename"
        logging.debug(txt)
        no_merged_sets = len(data.loaded_from)
        no_merged_sets = "_merged_" + str(no_merged_sets).zfill(3)
        filename = data.loaded_from[0]
    else:
        filename = data.loaded_from
        no_merged_sets = ""

    firstname, extension = os.path.splitext(filename)
    firstname += no_merged_sets
    if datadir:
        firstname = os.path.join(datadir, os.path.basename(firstname))

    if raw:
        outname_normal = firstname + "_normal.csv"
        cell._export_normal(data, outname=outname_normal, sep=sep)
        if data.has_steps is True:
            outname_steps = firstname + "_steps.csv"
            cell._export_steptable(data, outname=outname_steps, sep=sep)
        else:
            logging.debug("steps_made is not True")

    if summary:
        outname_stats = firstname + "_stats.csv"
        cell._export_stats(data, outname=outname_stats, sep=sep)

    if cycles:
        outname_cycles = firstname + "_cycles.csv"
        cell._export_cycles(
            outname=outname_cycles,
            sep=sep,
            shifted=shifted,
            method=method,
            shift=shift,
            last_cycle=last_cycle,
        )


# TODO (#520): near-dead, test-pinned only - decide removal in the DI pass
def cap_mod_summary(cell: "CellpyCell", summary, capacity_modifier="reset"):
    """Modify the summary capacities in place (legacy helper)."""
    # Why did I make this method?
    # OBS! modifies the summary table
    time_00 = time.time()
    # operates on the summary frame, so use the summary headers (native summary
    # discharge/charge differ from the raw names under the flip).
    discharge_title = cell.headers_summary.discharge_capacity
    charge_title = cell.headers_summary.charge_capacity
    chargecap = 0.0
    dischargecap = 0.0

    # TODO: @jepe - use externals.pandas.loc[row,column]

    if capacity_modifier == "reset":
        for index, row in summary.iterrows():
            dischargecap_2 = row[discharge_title]
            summary.loc[index, discharge_title] = dischargecap_2 - dischargecap
            dischargecap = dischargecap_2
            chargecap_2 = row[charge_title]
            summary.loc[index, charge_title] = chargecap_2 - chargecap
            chargecap = chargecap_2
    else:
        raise NotImplementedError

    logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
    return summary


# TODO (#520): near-dead, test-pinned only - decide removal in the DI pass
def cap_mod_normal(cell: "CellpyCell", capacity_modifier="reset", allctypes=True):
    """Modify the raw capacities in place (legacy helper)."""
    # Why did I make this method?
    # OBS! modifies the normal table
    time_00 = time.time()
    logging.debug("Not properly checked yet! Use with caution!")

    cycle_index_header = cell.headers_normal.cycle_index_txt
    step_index_header = cell.headers_normal.step_index_txt
    discharge_index_header = cell.headers_normal.discharge_capacity_txt
    discharge_energy_index_header = cell.headers_normal.discharge_energy_txt
    charge_index_header = cell.headers_normal.charge_capacity_txt
    charge_energy_index_header = cell.headers_normal.charge_energy_txt

    raw = cell.data.raw

    if capacity_modifier == "reset":
        # discharge cycles
        no_cycles = externals.numpy.amax(raw[cycle_index_header])
        for j in range(1, no_cycles + 1):
            cap_type = "discharge"
            e_header = discharge_energy_index_header
            cap_header = discharge_index_header
            discharge_cycles = cell.get_step_numbers(
                steptype=cap_type, allctypes=allctypes, cycle_number=j
            )

            steps = discharge_cycles[j]
            txt = "Cycle  %i (discharge):  " % j
            logging.debug(txt)
            # TODO: @jepe - use externals.pandas.loc[row,column] e.g. externals.pandas.loc[:,"charge_cap"]
            # for col or externals.pandas.loc[(externals.pandas.["step"]==1),"x"]
            selection = (raw[cycle_index_header] == j) & (
                raw[step_index_header].isin(steps)
            )
            c0 = raw[selection].iloc[0][cap_header]
            e0 = raw[selection].iloc[0][e_header]
            raw.loc[selection, cap_header] = raw.loc[selection, cap_header] - c0
            raw.loc[selection, e_header] = raw.loc[selection, e_header] - e0

            cap_type = "charge"
            e_header = charge_energy_index_header
            cap_header = charge_index_header
            charge_cycles = cell.get_step_numbers(
                steptype=cap_type, allctypes=allctypes, cycle_number=j
            )
            steps = charge_cycles[j]
            txt = "Cycle  %i (charge):  " % j
            logging.debug(txt)

            selection = (raw[cycle_index_header] == j) & (
                raw[step_index_header].isin(steps)
            )

            if any(selection):
                c0 = raw[selection].iloc[0][cap_header]
                e0 = raw[selection].iloc[0][e_header]
                raw.loc[selection, cap_header] = raw.loc[selection, cap_header] - c0
                raw.loc[selection, e_header] = raw.loc[selection, e_header] - e0
    logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
