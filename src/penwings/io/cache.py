import pandas as pd

from sqlalchemy import Engine
from pathlib import Path
from datetime import datetime, timedelta
from typing import Unpack, Union, Optional
from .._utils._typing import SQLParquetKwargs
from .._utils._decorators import timing_sql


class SQLParquetCache:
    def __init__(
        self,
        parquet_dir: Union[Path, str],
        conn: Engine,
        sql_dir: Optional[Union[Path, str]] = None,
        refresh_days: int = 0,  # zero disables refresh when force == false
        verbose: bool = True,
        **kwargs: Unpack[SQLParquetKwargs],
    ):

        if sql_dir is not None:
            self.sql_dir: Path = Path(sql_dir)
        self.parquet_dir: Path = Path(parquet_dir)
        self.refresh_days = refresh_days
        self.conn = conn
        self.global_kwargs = kwargs

        self.verbose = verbose
        self.source = "SQL"

    def set_params(self, **params):
        for key, value in params.items():
            if not hasattr(self, key):
                raise ValueError(f"Invalid parameter: {key}")
            setattr(self, key, value)
        return self

    def _sql_path(self, sql_file: str) -> Path:
        return self.sql_dir / sql_file

    def _parquet_path(self, sql_file: str, parquet_name: str | None = None) -> Path:
        name = parquet_name or Path(sql_file).stem
        return self.parquet_dir / f"{name}.parquet"

    def _is_new(self, path: Path, refresh_window: int) -> bool:
        if not path.exists():
            return False
        if self.refresh_days == 0:
            return True
        last_modified = datetime.fromtimestamp(path.stat().st_mtime)
        return datetime.now() - last_modified < timedelta(days=refresh_window)

    def _read_sql(self, sql_file: str):
        return self._sql_path(sql_file).read_text()

    def _return_sql(self, query: str, conn, **kwargs: Unpack[SQLParquetKwargs]) -> pd.DataFrame:
        return pd.read_sql(query, conn, **kwargs)

    @timing_sql
    def get(
        self,
        sql: str,
        parquet_name: Union[str, None] = None,
        conn: Engine | None = None,
        refresh_days: int | None = None,
        force: bool = False,
        **kwargs: Unpack[SQLParquetKwargs],
    ) -> tuple[pd.DataFrame, str]:
        if isinstance(sql, str) and Path(sql).suffix == ".sql":
            query = self._read_sql(sql)
        elif isinstance(sql, str):
            if parquet_name is None:
                raise ValueError("parquet_name must be provided if query is passed directly")
            query = sql
        else:
            raise ValueError("sql must be a SQL string or a path to a .sql file")

        connection = conn or self.conn
        refresh_window = refresh_days or self.refresh_days
        parquet_path = self._parquet_path(query)
        sql_kwargs = self.global_kwargs | kwargs

        if not force and self._is_new(parquet_path, refresh_window):
            source = "Parquet"
            return pd.read_parquet(parquet_path), source

        source = "SQL"
        df = self._return_sql(query, connection, **sql_kwargs)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(parquet_path, index=False)

        return df, source
