"""
Collecting all nda-extractor functions to locate errors and create a more
sensible structure
"""

import pathlib
import csv
import binascii


def process_subheader(subheader_bytes):
    raise NotImplementedError


def dict_to_csv_line(indict, lorder):
    csv_line = []
    for a in lorder:
        if a == "Elapsed_time":
            seconds = indict.get(a) / 1000
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            #            csv_line.append('record_ID')
            csv_line.append("%d:%02d:%02d" % (h, m, s))
        #            csv_line.append(f'{h}:{m}:{s}')
        # FIXME: do a proper handling of these lines, I think they are special
        # in some way, so will need special handling.  until then, ignore them
        #        elif a == "step_ID" and indict.get(a) == 0:
        #            return None
        else:
            csv_line.append(str(indict.get(a)))
    return csv_line


def get_step_name(s):
    if s == 1:
        return "CC_Chg"

    elif s == 2:
        return "CC_Dchg"

    # TODO: 3

    elif s == 4:
        return "Rest"
    # TODO: 5, 6

    elif s == 7:
        return "CCCV_Chg"
    # TODO: The rest
    else:
        return str(s)


def process_header(header_bytes):
    magic_number = header_bytes[0:6].decode("utf-8")
    if magic_number != "NEWARE":
        raise RuntimeError("Magic number wrong. Not valid .nda file")
    # Possibly ASCI coding but whatever.  This works.
    year = header_bytes[6:10].decode("utf-8")
    month = header_bytes[10:12].decode("utf-8")
    day = header_bytes[12:14].decode("utf-8")

    hour = header_bytes[2137:2139].decode("utf-8")
    minute = header_bytes[2140:2142].decode("utf-8")
    second = header_bytes[2143:2145].decode("utf-8")

    version = header_bytes[112:142].decode("utf-16").strip()
    name = header_bytes[2166:2178].decode("utf-8").strip("\00")
    # Comments is odd. Creation date?
    comments = header_bytes[2181:2300].decode("utf-8").strip("\00")

    # Not sure if this is really channel stuff...
    machine = int.from_bytes(header_bytes[2091:2092], byteorder="little")
    channel = int.from_bytes(header_bytes[2092:2093], byteorder="little")

    # ret = {}
    ret = {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "second": second,
        "version": version,
        "comments": comments,
        "machine": machine,
        "channel": channel,
        "name": name,
    }
    # TODO: find mass or something
    return ret


# Return a dict containing the relevant data.  all nice and pretty like.
def old_byte_stream(byte_stream):
    curr_dict = {}

    # Line ID
    line_idb = int.from_bytes(byte_stream[0:4], byteorder="little")
    curr_dict["record_ID"] = line_idb
    # End line ID

    # Jumpto
    col2 = int.from_bytes(byte_stream[4:8], byteorder="little")
    curr_dict["jumpto"] = col2
    # end jumpto

    # Step ID
    sid = int.from_bytes(byte_stream[8:9], byteorder="little")
    # If step id is zero, there is funny behavior.
    curr_dict["step_ID"] = sid
    # End Step ID

    # Step name? Might be with step ID too.  In any case, probably an
    # identifier for charge, rest, discharge, etc.
    # 4=REST. 1=CC_Chg. 7=CCCV_Chg. 2=CC_DChg.
    sjob = int.from_bytes(byte_stream[9:10], byteorder="little")
    sjob_name = get_step_name(sjob)
    curr_dict["step_name"] = sjob_name
    # End step name

    # Time in step
    tis = int.from_bytes(byte_stream[10:14], byteorder="little")
    curr_dict["time_in_step"] = tis
    # print(tic)
    # end time in step

    # Voltage
    volts = int.from_bytes(byte_stream[14:18], byteorder="little")
    if volts > 0x7FFFFFFFFF:
        volts -= 0x100000000000000
    curr_dict["voltage"] = volts / 10000
    # End voltage

    # Current
    current = int.from_bytes(byte_stream[18:22], byteorder="little")
    if current > 0x7FFFFFFF:
        current -= 0x100000000
    curr_dict["current"] = current / 10000
    # End Current

    # blank? This section seems to be blank, but it might not be?
    # By process of elimination, it might be tempurature.
    blank = int.from_bytes(byte_stream[22:30], byteorder="little")
    curr_dict["blank"] = blank
    # end blank?

    # Charge and Energy
    comp1 = int.from_bytes(byte_stream[30:38], byteorder="little")
    if comp1 > 0x7FFFFFFF:
        comp1 -= 0x100000000

    comp2 = int.from_bytes(byte_stream[38:46], byteorder="little")
    if comp2 > 0x7FFFFFFF:
        comp2 -= 0x100000000

    comp1 = comp1 / 3600000
    comp2 = comp2 / 3600000

    curr_dict["charge_mAh"] = comp1
    curr_dict["energy_mWh"] = comp2
    # End charge and energy

    # Time and date
    #    timestamp = int.from_bytes(byte_stream[46:54], byteorder='little')
    # timestamp = int.from_bytes(byte_stream[3280:3289], byteorder='little')
    #    newt = datetime.datetime.fromtimestamp(timestamp)
    #    curr_dict['timestamp'] = newt.strftime('%m-%d-%Y %H:%M:%S')
    # end time and date

    # last 5?  silly number.  The last one might be an indicator, and the other
    # 4 might be a number.  Possibly a checksum
    last = int.from_bytes(byte_stream[54:59], byteorder="little")
    curr_dict["last"] = last
    # end

    # stuff = []
    # for a in byte_stream:
    #    stuff.append(a)

    # print(curr_dict)
    # Raw binary available for bugfixing purposes only
    raw_bin = str(binascii.hexlify(bytearray(byte_stream)))
    curr_dict["RAW_BIN"] = raw_bin
    # time.sleep(.1)

    return curr_dict


def old_nda(inpath, outpath=":auto:", csv_line_order=None):
    print("old_nda")

    if csv_line_order is None:
        csv_line_order = [
            "record_ID",
            "jumpto",
            "step_ID",
            "step_name",
            "time_in_step",
            "voltage",
            "current",
            "blank",
            "charge_mAh",
            "energy_mWh",
        ]

    inpath = pathlib.Path(inpath)

    header_size = 2304

    byte_line = []
    line_size = 59
    line_number = 0
    main_data = False

    if outpath == ":auto:":
        outpath = inpath.with_suffix(".csv")
        print(inpath)
        print(outpath)

    if outpath != ":mem:":
        outfile = open(outpath, "w")

    else:
        import io

        outfile = io.StringIO()
    csv_out = csv.writer(outfile, delimiter=",", quotechar='"')
    csv_out.writerow(csv_line_order)

    header_data = {}
    with open(inpath, "rb") as f:
        header_bytes = f.read(header_size)
        # TODO: header decoding, including finding a mass
        header_data = process_header(header_bytes)

        byte = f.read(1)
        pos = 0
        subheader = b""
        while byte:
            if not main_data:
                local = int.from_bytes(byte, byteorder="little")
                if local == 255:
                    main_data = True
                    # TODO: Secondary header decoding
                    # header_data['subheader'] = process_subheader(subheader)
                    continue
                else:
                    subheader += byte
                    byte = f.read(1)
                    continue
            line = f.read(line_size)
            if line == b"":
                break

            dict_line = old_byte_stream(line)
            csv_line = dict_to_csv_line(dict_line, csv_line_order)
            # print(csv_line)
            if csv_line:
                csv_out.writerow(csv_line)

    if outpath == ":mem:":
        return outfile, header_data, csv_line

    outfile.close()

    return outpath, header_data, csv_line
    # print(subheader)


# Return a dict containing the relevant data.  all nice and pretty like.
def new_byte_stream(byte_stream):
    curr_dict = {}

    # Seems to be record ID * 256
    column_1 = int.from_bytes(
        byte_stream[0:1], byteorder="little", signed=True
    )  # ?? indicator of subheader?
    curr_dict["column_1"] = column_1

    # Record ID
    record_ID = int.from_bytes(
        byte_stream[1:5], byteorder="little", signed=True
    )  # 1 record id
    curr_dict["record_ID"] = record_ID

    # Not sure
    column_2 = int.from_bytes(byte_stream[5:9], byteorder="little", signed=True)  # 0 ?
    curr_dict["column_2"] = column_2

    # Step number?
    step_ID = int.from_bytes(
        byte_stream[9:11], byteorder="little", signed=True
    )  # 1 step number
    curr_dict["step_jump"] = step_ID

    # Step name
    step_name = int.from_bytes(
        byte_stream[11:12], byteorder="little", signed=True
    )  # 2 CC_DChg
    curr_dict["step_name"] = get_step_name(step_name)

    # Not sure - jumpto?
    step_jump_two = int.from_bytes(
        byte_stream[12:13], byteorder="little", signed=True
    )  # 2 step number again?
    curr_dict["step_ID"] = step_jump_two

    # Elapsed time in seconds
    tot_seconds = int.from_bytes(
        byte_stream[13:21], byteorder="little", signed=True
    )  # 0 elapsed time
    curr_dict["Elapsed_time"] = tot_seconds

    # Voltage V
    vol = int.from_bytes(
        byte_stream[21:25], byteorder="little", signed=True
    )  # 22126   voltage
    curr_dict["Voltage_V"] = vol / 10000

    # Current mA
    cur = int.from_bytes(
        byte_stream[25:29], byteorder="little", signed=True
    )  # 7  current
    curr_dict["Current_mA"] = cur / 10000

    # Capacity Charge mAh
    chg_cap = int.from_bytes(byte_stream[37:45], byteorder="little", signed=True)  # ?
    curr_dict["Chg_Capacity_mAh"] = chg_cap / 36000000

    # Capacity Discharge mAh
    dchg_cap = int.from_bytes(byte_stream[45:53], byteorder="little", signed=True)  # ?
    curr_dict["Dchg_Capacity_mAh"] = dchg_cap / 36000000

    # Energy Charge mWh
    chg_eng = int.from_bytes(byte_stream[53:59], byteorder="little", signed=True)  # ?
    curr_dict["Chg_Energy_mWh"] = chg_eng / 360000000

    # Energy Discharge mWh
    dchg_eng = int.from_bytes(byte_stream[61:67], byteorder="little", signed=True)  # ?
    curr_dict["Dchg_Energy_mWh"] = dchg_eng / 360000000

    # 29-45 and 65-69 Other stuff? eg capacity and energy of CCCV and CV curves
    # Print it anyway
    column_3 = int.from_bytes(byte_stream[41:45], byteorder="little", signed=True)
    curr_dict["column_3"] = column_3

    column_4 = int.from_bytes(byte_stream[65:69], byteorder="little", signed=True)
    curr_dict["column_4"] = column_4

    # Date and time
    year = int.from_bytes(byte_stream[69:71], byteorder="little", signed=True)  # 8 year
    month = int.from_bytes(
        byte_stream[71:72], byteorder="little", signed=True
    )  # 8 year
    day = int.from_bytes(byte_stream[72:73], byteorder="little", signed=True)  # 9 month
    hour = int.from_bytes(byte_stream[73:74], byteorder="little", signed=True)  # 10 day
    minute = int.from_bytes(
        byte_stream[74:75], byteorder="little", signed=True
    )  # 10 hour
    second = int.from_bytes(
        byte_stream[75:76], byteorder="little", signed=True
    )  # 11 minute
    #    second = int.from_bytes(byte_stream[76:78], byteorder='little', signed=True)   # 11 second
    curr_dict["Timestamp"] = f"{year}-{month}-{day} {hour}:{minute}:{second}"

    # 78-86 Not sure. Extra space?
    column_5 = int.from_bytes(byte_stream[78:84], byteorder="little", signed=True)  # 11
    curr_dict["column_5"] = column_5

    # print(curr_dict)
    # Raw binary available for bugfixing purposes only
    raw_bin = str(binascii.hexlify(bytearray(byte_stream)))
    curr_dict["RAW_BIN"] = raw_bin
    # time.sleep(.1)

    return curr_dict


def new_nda(inpath, outpath=":auto:", csv_line_order=None, testcols=False):
    print("new_nda")

    if csv_line_order is None:
        csv_line_order = []

    inpath = pathlib.Path(inpath)

    header_size = 217548
    byte_line = []
    line_size = 86
    line_number = 0
    main_data = False

    if testcols is False:

        csv_line_order = [
            "record_ID",
            "step_jump",
            "step_name",
            "step_ID",
            "Elapsed_time",
            "Voltage_V",
            "Current_mA",
            "Chg_Capacity_mAh",
            "Dchg_Capacity_mAh",
            "Chg_Energy_mWh",
            "Dchg_Energy_mWh",
            "Timestamp",
        ]
    elif testcols is True:
        csv_line_order = [
            "column_1",
            "record_ID",
            "column_2",
            "step_jump",
            "step_name",
            "step_ID",
            "Elapsed_time",
            "Voltage_V",
            "Current_mA",
            "Chg_Capacity_mAh",
            "Dchg_Capacity_mAh",
            "Chg_Energy_mWh",
            "Dchg_Energy_mWh",
            "column_3",
            "column_4",
            "Timestamp",
            "column_5",
        ]

    if outpath == ":auto:":
        outpath = inpath.with_suffix(".csv")
        print(inpath)
        print(outpath)

    if outpath != ":mem:":
        outfile = open(outpath, "w")

    else:
        import io

        outfile = io.StringIO()
    csv_out = csv.writer(outfile, delimiter=",", quotechar='"')
    csv_out.writerow(csv_line_order)

    header_data = {}
    with open(inpath, "rb") as f:
        header_bytes = f.read(header_size)
        # TODO: header decoding, including finding a mass
        header_data = process_header(header_bytes)

        byte = f.read(1)
        pos = 0
        subheader = b""
        while byte:
            if not main_data:
                local = int.from_bytes(byte, byteorder="little", signed=True)
                if local == 85:
                    main_data = True
                    # TODO: Secondary header decoding
                    # if local == 170 then subheader is True. Maybe...
                    # header_data['subheader'] = process_subheader(subheader)
                    continue
                #                if local == 170:
                #                    continue
                else:
                    subheader += byte
                    byte = f.read(1)
                    continue
            line = f.read(line_size)
            if line == b"":
                break

            dict_line = new_byte_stream(line)
            csv_line = dict_to_csv_line(dict_line, csv_line_order)
            # print(csv_line)
            if csv_line:
                csv_out.writerow(csv_line)

    if outpath == ":mem:":
        return outfile, header_data, csv_line

    outfile.close()

    return outpath, header_data, csv_line
    # print(subheader)


def process_nda(inpath, outpath=None):
    print("process_nda")

    inpath = pathlib.Path(inpath)

    # Not used?
    csv_report = None
    m = None
    lline = None

    if outpath == ":auto:":
        outpath = inpath.with_suffix(".csv")
        print(inpath)
        print(outpath)

    with open(inpath, "rb") as f:
        data = f.read()

    if data[112:115] == b"BTS":
        old_nda(inpath, outpath=":auto:")
    else:
        new_nda(inpath, outpath=":auto:")

    return csv_report, m, lline


def report_generator(filepath):
    print("generating report")
    print(" - not inserted yet - redirects to direct_report")
    direct_report(filepath)


def direct_report(filepath):
    print("direct_report")
    print(" - not inserted yet - redirects to process_nda")
    print(f"Input from: {filepath.resolve()}")
    print(f"File exists? {filepath.is_file()}")
    nda_path = filepath
    csv_report, m, lline = process_nda(nda_path, outpath=":mem:")


if __name__ == "__main__":
    filepath = pathlib.Path("test.nda")
    report_generator(filepath)
