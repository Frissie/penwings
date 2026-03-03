# Penwings

**Penwings** is a lightweight Python library designed to simplify SQL data workflows by automatically importing data from SQL and caching it as Parquet files. This ensures faster subsequent access and reproducible pipelines, while reducing database get.

---

## Table of Contents

1. [Features](#features)  
2. [Installation](#installation)  
3. [Getting Started](#getting-started)  
4. [Usage](#usage)  
5. [Versioning](#versioning)  
6. [Contributing](#contributing)  
7. [License](#license)  

---

## Features

- get data from SQL queries or SQL files  
- Automatically save query results as Parquet files  
- Reuse Parquet files to avoid redundant queries  
- Simple, stable API for reproducible workflows  
- Optimized for performance and ease of integration  

---

## Installation

Install via pip:

pip install penwings

> Make sure you have Python 3.11+ installed.

---

## Getting Started

### Importing the Library

from penwings import SQLParquetCache

### Initialize the Cache

You can initialize the cache by providing either a SQL directory or a query string, along with a Parquet directory:

```
from sqlalchemy import create_engine
```

# SQL connection
```
engine = create_engine("postgresql://user:password@localhost/dbname")

# Initialize the cache
loader = SQLParquetCache(
    sql_dir="sql_files",        # Optional if using query string
    parquet_dir="parquet_cache",
    conn=engine
)
```
---

## Usage

### 1. Using SQL Files

If you have SQL files stored in a directory:

```
# Run a SQL file and cache the result
df = loader.get("monthly_sales.sql")
```

- `penwings` will automatically check if a Parquet version exists.
- If it exists, the cached Parquet is loaded.
- If not, the SQL query runs and the result is saved as a Parquet file.

### 2. Using SQL Query Strings

You can also pass queries directly:

```
query = "SELECT * FROM sales WHERE month='2026-02'"
df = loader.get(sql=query, parquet_name="sales_feb2026")
```

- `parquet_name` determines the Parquet file name.
- Works similarly to SQL file mode for caching.

### 3. Automatic Parquet Management

- All results are cached in the specified `parquet_dir`.
- This reduces repeated database queries and ensures reproducibility.
- Cached files can be reloaded for faster access.

---

## Versioning

Penwings follows **semantic versioning**:

- **MAJOR**: Breaking changes to API  
- **MINOR**: New features, backward-compatible  
- **PATCH**: Bug fixes  

---

## Contributing

We welcome contributions!  

1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/my-feature`)  
3. Commit your changes (`git commit -m 'Add new feature'`)  
4. Push to branch (`git push origin feature/my-feature`)  
5. Open a pull request  

Please ensure your code follows PEP8 standards.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Example Workflow

```
from sqlalchemy import create_engine
from penwings import SQLParquetCache

engine = create_engine("sqlite:///example.db")

loader = SQLParquetCache(
    sql_dir="sql_queries",
    parquet_dir="parquet_cache",
    conn=engine
)

# get data
df_jan = loader.get("sales_january.sql")
df_feb = loader.get(sql="SELECT * FROM sales WHERE month='2026-02'", parquet_name="sales_feb")
```

- SQL files are automatically cached as Parquet  
- Subsequent loads are fast and do not hit the database  
