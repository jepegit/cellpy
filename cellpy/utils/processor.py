import cellpy
import multiprocessing
import concurrent.futures
import time
import pathlib
import pandas as pd

ASYNC_MODE = "threading"

if ASYNC_MODE == "threading":
    PoolExecutor = concurrent.futures.ThreadPoolExecutor
else:
    # cellpy.CellpyCell object is not serializable so returning it
    # within a process-pool will crash.
    # TODO: make it serializable
    PoolExecutor = concurrent.futures.ProcessPoolExecutor


def func(filename):
    # time.sleep(1)
    print(f"{filename}: {pathlib.Path(filename).is_file()}")
    c = cellpy.get(filename)
    return c


def main():
    print(" starting ".center(80, "-"))
    max_number_processes = multiprocessing.cpu_count()
    print(f"{max_number_processes=}")
    f1 = r"C:\scripting\cellpy\testdata\batch_project\data\raw\20230221_CLP001_1_02_cc_01.res"
    f2 = r"C:\scripting\cellpy\testdata\batch_project\data\raw\20230221_CLP001_1_03_cc_01.res"
    f3 = r"C:\scripting\cellpy\testdata\batch_project\data\raw\20230221_CLP001_2_01_cc_01.res"
    f4 = r"C:\scripting\cellpy\testdata\batch_project\data\raw\20230221_CLP001_2_04_cc_01.res"
    params = [
        dict(filename=f1),
        dict(filename=f2),
        dict(filename=f3),
        dict(filename=f4),
    ]
    t0 = time.time()
    with PoolExecutor() as executor:
        pool = [executor.submit(func, **param) for param in params]

        for i in concurrent.futures.as_completed(pool):
            c = i.result(timeout=2000)
    dt_p = time.time() - t0

    t0 = time.time()
    for param in params:
        c = func(**param)
    dt_s = time.time() - t0
    print(f"Parallel processing took {dt_p} seconds")
    print(f"Sequential processing took {dt_s} seconds")


if __name__ == "__main__":
    main()
