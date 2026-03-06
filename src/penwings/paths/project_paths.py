from pathlib import Path


class ProjectPaths:
    """
    Manage and optionally create a standardized data science project folder structure.

    This class provides a convenient interface to access common project folders
    as `Path` objects, automatically detects the project root, and can create
    either all or a subset of folder groups. The `show()` method displays only
    the folders that were requested or created.

    Root detection is based on standard project markers:
    'data', 'models', 'notebooks', 'configs', 'README.md', or 'pyproject.toml'.

    Parameters
    ----------
    root : str or pathlib.Path, optional
        The root directory of the project. If `None`, the root is auto-detected
        by searching the current working directory and its parents for standard
        project markers.
    create : bool, default True
        If True, the requested folders are created on the filesystem.
    folders : None, str, or list of str, optional
        Specifies which folder groups to create:
            - None : create all folders
            - str  : name of a single folder group to create (e.g., 'data')
            - list : list of folder groups to create (e.g., ['data', 'models'])
        Valid folder groups include:
            - 'data'      : data/, data/raw/, data/processed/, data/external/
            - 'models'    : models/
            - 'features'  : features/
            - 'reports'   : reports/, reports/figures/, reports/tables/
            - 'sql'       : sql/
            - 'notebooks' : notebooks/
            - 'configs'   : configs/
            - 'logs'      : logs/

    Attributes
    ----------
    root : pathlib.Path
        The project root directory.
    data : pathlib.Path
        Top-level data directory.
    data_raw : pathlib.Path
        Raw input data directory.
    data_processed : pathlib.Path
        Final processed data directory.
    data_external : pathlib.Path
        External or third-party data directory.
    features : pathlib.Path
        Directory for feature engineering.
    models : pathlib.Path
        Directory to store trained models.
    reports : pathlib.Path
        Reports output directory.
    figures : pathlib.Path
        Subdirectory for report figures.
    tables : pathlib.Path
        Subdirectory for report tables.
    sql : pathlib.Path
        Directory for SQL queries.
    notebooks : pathlib.Path
        Notebooks directory for exploration and analysis.
    configs : pathlib.Path
        Configuration files directory.
    logs : pathlib.Path
        Logs directory for pipeline or experiment outputs.

    Methods
    -------
    show()
        Prints the paths of only the folder groups that were created or requested.

    Examples
    --------
    Create all folders with automatic root detection:

    >>> paths = ProjectPaths()
    >>> paths.show()
    data: /project/data
    data: /project/data/raw
    data: /project/data/processed
    data: /project/data/external
    models: /project/models
    features: /project/features
    reports: /project/reports
    reports: /project/reports/figures
    reports: /project/reports/tables
    sql: /project/sql
    notebooks: /project/notebooks
    configs: /project/configs
    logs: /project/logs

    Create only the data and reports folders:

    >>> paths = ProjectPaths(folders=['data', 'reports'])
    >>> paths.show()
    data: /project/data
    data: /project/data/raw
    data: /project/data/processed
    data: /project/data/external
    reports: /project/reports
    reports: /project/reports/figures
    reports: /project/reports/tables

    Use a specific root directory:

    >>> paths = ProjectPaths(root='/home/user/projects/fraud_detection')
    >>> paths.data_raw
    PosixPath('/home/user/projects/fraud_detection/data/raw')
    """

    def __init__(self, root: Path | str | None = None, create: bool = True, folders=None):
        self.root = Path(root) if root else self._detect_root()

        # data
        self.data = self.root / "data"
        self.data_raw = self.data / "raw"
        self.data_processed = self.data / "processed"
        self.data_external = self.data / "external"

        # ML / features
        self.features = self.root / "features"
        self.models = self.root / "models"

        # outputs
        self.reports = self.root / "reports"
        self.figures = self.reports / "figures"
        self.tables = self.reports / "tables"

        # other
        self.sql = self.root / "sql"
        self.notebooks = self.root / "notebooks"
        self.configs = self.root / "configs"
        self.logs = self.root / "logs"

        # Track which folder groups were created
        self._created_groups = []

        if create:
            self._create_dirs(folders)

    def _detect_root(self):
        cwd = Path.cwd()
        markers = ["data", "models", "notebooks", "configs", "README.md", "pyproject.toml"]
        for parent in [cwd] + list(cwd.parents):
            if any((parent / m).exists() for m in markers):
                return parent
        return cwd

    def _create_dirs(self, folders=None):
        # Define mapping
        path_map = {
            "data": [self.data, self.data_raw, self.data_processed, self.data_external],
            "models": [self.models],
            "features": [self.features],
            "reports": [self.reports, self.figures, self.tables],
            "sql": [self.sql],
            "notebooks": [self.notebooks],
            "configs": [self.configs],
            "logs": [self.logs],
        }

        # Determine which paths to create
        if folders is None:
            folders_to_create = list(path_map.keys())
        elif isinstance(folders, str):
            folders_to_create = [folders]
        elif isinstance(folders, list):
            folders_to_create = folders
        else:
            folders_to_create = []

        self._created_groups = folders_to_create  # store for show()

        # Flatten paths
        paths_to_create = [p for key in folders_to_create for p in path_map.get(key, [])]

        for path in paths_to_create:
            path.mkdir(parents=True, exist_ok=True)

    def show(self):
        # Only show created folder groups
        path_map = {
            "data": [self.data, self.data_raw, self.data_interim, self.data_processed, self.data_external],
            "models": [self.models],
            "features": [self.features],
            "reports": [self.reports, self.figures, self.tables],
            "sql": [self.sql],
            "notebooks": [self.notebooks],
            "configs": [self.configs],
            "logs": [self.logs],
        }

        for key in self._created_groups:
            for path in path_map.get(key, []):
                print(f"{key}: {path}")


if __name__ == "__main__":
    test = ProjectPaths(create=False, folders=["data", "reports"])
    test.show()
