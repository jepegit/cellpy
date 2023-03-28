import cellpy
import multiprocessing
import concurrent.futures
import time
import pandas as pd

ASYNC_MODE = "threading"

if ASYNC_MODE == "threading":
    PoolExecutor = concurrent.futures.ThreadPoolExecutor
else:
    PoolExecutor = concurrent.futures.ProcessPoolExecutor


def func(a=None, b=None, c=None):
    time.sleep(1)
    s = f"{a=} {b=} {c=}"
    return s


def main():
    print(" starting ".center(80, "-"))
    max_number_processes = multiprocessing.cpu_count()
    print(f"{max_number_processes=}")
    p1 = dict(a=1, b=1, c=2)
    p2 = dict(a=2, b=2, c=4)
    p3 = dict(a=3, b=3, c=6)
    p4 = dict(a=3, b=4, c=6)
    p5 = dict(a=3, b=5, c=6)
    p6 = dict(a=3, b=6, c=6)
    params = [p1, p2, p3, p4, p5, p6]
    t0 = time.time()
    with PoolExecutor(max_number_processes) as executor:
        pool = [executor.submit(func, **param) for param in params]

        for i in concurrent.futures.as_completed(pool):
            print(i.result())
    print(f"Took {time.time() - t0} seconds")


if __name__ == '__main__':
    main()
