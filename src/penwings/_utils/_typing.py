from typing import TypedDict, List, Union


class SQLParquetKwargs(TypedDict, total=False):
    index_col: Union[str, List[str], None]
    parse_dates: Union[List[str], None]
    dtype: Union[dict, None]
