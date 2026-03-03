import pathlib

home_dir = pathlib.Path.cwd()
proj_dir = pathlib.Path.cwd().parent

input_dir = home_dir / "input"
sql_dir = input_dir / "sql"
parquet_dir = input_dir / "parquet"
output_dir = home_dir / "output"

if __name__ == "__main__":
    i = 1
    for name, value in dict(locals()).items():
        if isinstance(value, pathlib.Path):
            print(f"{i} - {name}: {value}")
            i += 1
