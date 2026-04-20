from __future__ import annotations

import pandas as pd

from pathlib import Path
from datetime import datetime, timedelta
from typing import Unpack, Optional, TYPE_CHECKING
from ..utils._typing import SQLParquetKwargs
from ..utils._decorators import timing_sql

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class SQLParquetCache:
    """
    Cache SQL query results locally as Parquet files.

    This class executes SQL queries using a SQLAlchemy engine and caches
    the results as Parquet files in a specified directory. On subsequent
    calls, the cached Parquet file is returned if it is considered "fresh"
    according to a configurable refresh window.

    The query can either be provided directly as a SQL string or as a path
    to a ``.sql`` file. If a Parquet file already exists and is within the
    refresh window, it will be loaded instead of re-executing the query,
    unless ``force=True`` is specified.

    Parameters
    ----------
    parquet_dir : str or pathlib.Path
        Directory where Parquet cache files will be stored.
    conn : sqlalchemy.engine.Engine
        SQLAlchemy engine used to execute SQL queries.
    sql_dir : str or pathlib.Path, optional
        Directory containing ``.sql`` files. Required when passing a
        filename instead of a raw SQL string.
    refresh_days : int, default 0
        Number of days for which a cached Parquet file is considered fresh.
        If 0, refresh checking is disabled and existing Parquet files are
        always used unless ``force=True``.
    verbose : bool, default True
        Whether to enable verbose output (if used by decorators or
        extended implementations).
    **kwargs : dict
        Additional keyword arguments passed to ``pandas.read_sql``.
        These are stored globally and merged with per-call arguments
        in :meth:`get`.

    Notes
    -----
    - Cached Parquet filenames are derived from the SQL filename stem
      or from the provided ``parquet_name``.
    - If a raw SQL string is provided, ``parquet_name`` must be specified.
    - The cache directory is created automatically if it does not exist.
    - The method :meth:`get` returns both the DataFrame and the source
      ("SQL" or "Parquet") used to obtain the data.
    """

    def __init__(
        self,
        parquet_dir: Path | str,
        conn: Engine,
        sql_dir: Optional[Path | str] = None,
        refresh_days: int = 0,  # zero disables refresh when force == false
        verbose: bool = True,
        **kwargs: Unpack[SQLParquetKwargs],
    ):
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            raise ImportError("SQLParquetCache requires 'sqlalchemy'. Install it with: pip install penwings[sql]")

        if sql_dir is not None:
            self.sql_dir: Path = Path(sql_dir)
        self.parquet_dir: Path = Path(parquet_dir)
        self.refresh_days = refresh_days
        self.conn = conn
        self.global_kwargs = kwargs

        self.verbose = verbose

    def set_params(self, **params):
        for key, value in params.items():
            if not hasattr(self, key):
                raise ValueError(f"Invalid parameter: {key}")
            setattr(self, key, value)
        return self

    def _sql_path(self, sql_file: str) -> Path:
        if not hasattr(self, "sql_dir"):
            raise ValueError("sql_dir must be set when passing a .sql filename.")
        return self.sql_dir / sql_file

    def _parquet_path(self, parquet_name: str) -> Path:
        return self.parquet_dir / f"{parquet_name}.parquet"

    def _is_fresh(self, path: Path, refresh_window: int) -> bool:
        """
        Determine whether a cached Parquet file is fresh enough to use.

        Parameters
        ----------
        path : Path
            Path to the Parquet file.
        refresh_window : int
            Number of days the file is considered valid.
            If 0, the file is always considered fresh (if it exists).

        Returns
        -------
        bool
            True if the file exists and is within the refresh window.
        """
        if not path.exists():
            return False

        # 0 means: never refresh (always use cache if it exists)
        if refresh_window == 0:
            return True

        last_modified = datetime.fromtimestamp(path.stat().st_mtime)
        age = datetime.now() - last_modified
        return age < timedelta(days=refresh_window)

    def _read_sql(self, sql_file: str):
        return self._sql_path(sql_file).read_text()

    def _return_sql(self, query: str, conn, **kwargs: Unpack[SQLParquetKwargs]) -> pd.DataFrame:
        return pd.read_sql(query, conn, **kwargs)

    @timing_sql
    def get(
        self,
        sql: str,
        parquet_name: str | None = None,
        conn: Engine | None = None,
        refresh_days: int | None = None,
        force: bool = False,
        **kwargs: Unpack[SQLParquetKwargs],
    ) -> tuple[pd.DataFrame, str]:
        """
        Retrieve a DataFrame from cache or execute the SQL query.

        Parameters
        ----------
        sql : str
            Either a raw SQL query string or the filename of a ``.sql`` file.
        parquet_name : str, optional
            Name of the Parquet file (without extension) when passing a raw
            SQL string. Ignored if a ``.sql`` filename is provided.
        conn : sqlalchemy.engine.Engine, optional
            Alternative SQLAlchemy engine to use instead of the default.
        refresh_days : int, optional
            Override the instance-level refresh window (in days).
        force : bool, default False
            If True, bypass the cache and force re-execution of the query.
        **kwargs : dict
            Additional keyword arguments passed to ``pandas.read_sql``.
            These override any global keyword arguments defined at
            initialization.

        Returns
        -------
        DataFrame
            The resulting query output.
        str
            The data source used: either ``"SQL"`` or ``"Parquet"``.

        Raises
        ------
        ValueError
            If ``sql`` is a raw SQL string and ``parquet_name`` is not provided.
            If ``sql`` is neither a SQL string nor a ``.sql`` file path.

        Notes
        -----
        If the Parquet file exists and is within the refresh window,
        it is loaded directly using ``pandas.read_parquet``. Otherwise,
        the SQL query is executed and the result is written to Parquet.
        """
        if isinstance(sql, str) and Path(sql).suffix == ".sql":
            parquet_name = parquet_name or Path(sql).stem
            query = self._read_sql(sql)
        elif isinstance(sql, str):
            if parquet_name is None:
                raise ValueError("parquet_name must be provided if query is passed directly")
            query = sql
        else:
            raise ValueError("sql must be a SQL string or a path to a .sql file")

        connection = self.conn if conn is None else conn
        refresh_window = self.refresh_days if refresh_days is None else refresh_days
        parquet_path = self._parquet_path(parquet_name)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        sql_kwargs = self.global_kwargs | kwargs

        if not force and self._is_fresh(parquet_path, refresh_window):
            source = "Parquet"
            return pd.read_parquet(parquet_path), source

        source = "SQL"
        df = self._return_sql(query, connection, **sql_kwargs)
        df.to_parquet(parquet_path, index=False)

        return df, source
