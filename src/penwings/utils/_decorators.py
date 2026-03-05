import time as t

from functools import wraps
from pathlib import Path


def timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = t.perf_counter()
        result = func(*args, **kwargs)
        end = t.perf_counter()
        print(f"{func.__name__} took {end - start: .2f}")
        return result

    return wrapper


def timing_sql(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        sql_file = kwargs.get("sql_file", None)
        verbose = getattr(args[0], "verbose", True)

        if sql_file is None and len(args) > 1:
            sql_file = args[1]

        sql_file = Path(sql_file)

        start = t.perf_counter()
        result, source = func(*args, **kwargs)
        end = t.perf_counter()

        if verbose:
            print(f"{sql_file.stem} -> {source} took {end - start: .2f} seconds to load")
        return result

    return wrapper
