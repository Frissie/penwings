# Penwings

**Penwings** is a lightweight Python library for building **reproducible data workflows**.

It provides simple, composable tools to:
- manage project structure
- standardize data access
- cache SQL queries efficiently

The goal is to reduce boilerplate and make data pipelines **faster, cleaner, and reproducible by default**.

---

## ✨ Features

### 🗂️ Project Structure Management
- Standardized folder setup for data science projects
- Automatic project root detection
- Flexible, extensible path system

### 🧠 SQL → Parquet Caching
- Execute SQL queries via SQLAlchemy
- Automatically cache results as Parquet
- Reuse cached data to avoid unnecessary database hits
- Configurable refresh logic

### ⚡ Lightweight & Modular
- Minimal core dependencies (`pandas`, `numpy`)
- Optional SQL support
- Designed to scale into larger workflows

---

## 📦 Installation

```bash
pip install penwings
````

### Optional SQL support

```bash
pip install penwings[sql]
```

> Requires Python **3.11+**

---

## 🚀 Quick Start

### 1. Project structure

```python
from penwings import ProjectPaths

paths = ProjectPaths()

print(paths.data)
print(paths.models)
```

Creates a standardized structure like:

```
configs/
data/
  raw/
  processed/
  external/
features/
logs/
models/
notebooks/
reports/
  figures/
  tables/
sql/
```

---

### 2. SQL caching

```python
from sqlalchemy import create_engine
from penwings import SQLParquetCache

engine = create_engine("sqlite:///example.db")

cache = SQLParquetCache(
    sql_dir="sql",
    parquet_dir="cache",
    conn=engine,
    refresh_days=1
)
```

---

## 📊 Usage

### Using SQL files

```python
df = cache.get("sales.sql")
```

* Loads from **Parquet** if cached
* Otherwise executes SQL and caches result

---

### Using raw SQL

```python
query = "SELECT * FROM sales WHERE month = '2026-02'"

df = cache.get(
    sql=query,
    parquet_name="sales_feb"
)
```

---

### Cache behavior

```python
df = cache.get("sales.sql", force=True)
```

* `force=True` → always re-run SQL
* `refresh_days=N` → cache expires after N days
* returns:

  * `DataFrame`


---

## 🧩 ProjectPaths

Create only specific parts of a project:

```python
paths = ProjectPaths(folders=["data", "ml"])
```

Custom directories:

```python
paths = ProjectPaths(
    custom_dirs={
        "modules": "src/modules",
        "views": "src/views"
    }
)
```

Access paths:

```python
paths.data
paths["models"]
paths.as_dict()
```

---

## 🧠 Design Philosophy

Penwings is built around a few core ideas:

* **Reproducibility first** → deterministic data access via caching
* **Convention over configuration** → sensible defaults for structure
* **Composable building blocks** → small tools that work well together
* **Lightweight core** → no heavy framework overhead

---

## 🛣️ Roadmap

* Pipeline abstraction (data workflows as steps)
* Improved SQL utilities and query management
* Integration with feature engineering workflows
* Better caching strategies and metadata tracking

---

## 🔢 Versioning

Penwings follows **semantic versioning**:

* **MAJOR** → breaking changes
* **MINOR** → new features
* **PATCH** → bug fixes

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a branch (`feature/my-feature`)
3. Commit your changes
4. Open a pull request

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 💡 Example Workflow

```python
from sqlalchemy import create_engine
from penwings import ProjectPaths, SQLParquetCache

# Setup project structure
paths = ProjectPaths()

# Setup SQL cache
engine = create_engine("sqlite:///example.db")

cache = SQLParquetCache(
    sql_dir=paths.sql,
    parquet_dir=paths.data,
    conn=engine
)

# Load data
df_sales = cache.get("sales.sql")

```

---

## ⭐ Why Penwings?

Penwings sits between:

* ad-hoc scripts ❌
* heavy frameworks ❌

It gives you just enough structure to:

* stay organized
* move fast
* keep workflows reproducible

without getting in your way.