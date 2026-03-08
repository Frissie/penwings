from pathlib import Path
from typing import Optional


class ProjectPaths:
    """
    Manage standardized directory structures for data science projects.

    `ProjectPaths` provides a convenient interface for working with common
    project directories such as data, models, reports, and notebooks. Each
    directory is exposed as a `pathlib.Path` attribute and can optionally be
    created on the filesystem during initialization.

    The class supports:

    • automatic project root detection
    • creation of predefined folder groups
    • optional creation of only selected groups
    • user-defined custom directories
    • dictionary-style access to paths

    Root detection searches the current working directory and its parents
    for common project markers such as ``data/``, ``models/``, ``notebooks/``,
    ``configs/``, ``README.md`` or ``pyproject.toml``.

    Parameters
    ----------
    root : str or pathlib.Path, optional
        Project root directory. If not provided, the root is automatically
        detected by scanning the current working directory and its parents
        for common project markers.

    create : bool, default True
        If True, directories are created on the filesystem.

    folders : None, str, or list[str], optional
        Specifies which predefined folder groups to create.

        - None : create all folder groups
        - str  : create a single folder group
        - list : create multiple folder groups

        Available folder groups:

        - ``data``      → data/, data/raw/, data/processed/, data/external/
        - ``models``    → models/
        - ``features``  → features/
        - ``reports``   → reports/, reports/figures/, reports/tables/
        - ``sql``       → sql/
        - ``notebooks`` → notebooks/
        - ``configs``   → configs/
        - ``logs``      → logs/

    custom_dirs : dict[str, str], optional
        Additional directories defined relative to the project root.
        Each key becomes an attribute on the class and the value specifies
        the relative path.

        Example
        -------
        ``{'modules': 'modules', 'view': 'modules/view'}``

        creates:

        ``paths.modules → root/modules``
        ``paths.view    → root/modules/view``

        Custom directories are grouped under the ``"custom"`` folder group
        and included in the output of :meth:`show`.

    Attributes
    ----------
    root : pathlib.Path
        The detected or user-defined project root.

    data : pathlib.Path
        Base data directory.

    data_raw : pathlib.Path
        Raw input data directory.

    data_processed : pathlib.Path
        Processed data directory.

    data_external : pathlib.Path
        External or third-party data.

    features : pathlib.Path
        Feature engineering directory.

    models : pathlib.Path
        Directory for trained models.

    reports : pathlib.Path
        Reports output directory.

    figures : pathlib.Path
        Report figures directory.

    tables : pathlib.Path
        Report tables directory.

    sql : pathlib.Path
        SQL query directory.

    notebooks : pathlib.Path
        Jupyter notebooks directory.

    configs : pathlib.Path
        Configuration files directory.

    logs : pathlib.Path
        Logs and pipeline outputs.

    Methods
    -------
    show()
        Display the directory groups that were requested or created.

    keys()
        Return the available path attribute names.

    as_dict()
        Return a dictionary mapping path names to ``Path`` objects.

    Examples
    --------
    Create a full project structure with automatic root detection:

    >>> paths = ProjectPaths()
    >>> paths.data_raw
    PosixPath('.../data/raw')

    Create only specific folder groups:

    >>> paths = ProjectPaths(folders=['data', 'reports'])
    >>> paths.show()

    Use a specific project root:

    >>> paths = ProjectPaths(root='/home/user/projects/fraud_detection')
    >>> paths.models
    PosixPath('/home/user/projects/fraud_detection/models')

    Define additional custom directories:

    >>> paths = ProjectPaths(
    ...     custom_dirs={'modules': 'modules', 'view': 'modules/view'}
    ... )
    >>> paths.modules
    PosixPath('.../modules')

    Dictionary-style access:

    >>> paths['data_raw']
    PosixPath('.../data/raw')
    """

    def __init__(
        self, root: Optional[Path | str] = None, create: bool = True, folders: Optional[str | list] = None, custom_dirs: Optional[dict] = None
    ):
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

        self._folders = folders
        self._created_groups = []
        self._path_map = {
            "data": [self.data, self.data_raw, self.data_processed, self.data_external],
            "models": [self.models],
            "features": [self.features],
            "reports": [self.reports, self.figures, self.tables],
            "sql": [self.sql],
            "notebooks": [self.notebooks],
            "configs": [self.configs],
            "logs": [self.logs],
        }

        if custom_dirs is not None:
            self._create_custom_dirs(custom_dirs)

        self._create_dirs(create, self._folders)

    def _create_custom_dirs(self, custom_dirs: dict[str, str]):
        paths = []

        for name, rel_path in custom_dirs.items():
            path = self.root / rel_path
            setattr(self, name, path)
            paths.append(path)

        self._path_map["custom"] = paths

        if self._folders is None:
            self._folders = "custom"
        elif isinstance(self._folders, str):
            self._folders = [self._folders, "custom"]
        else:
            self._folders.append("custom")

    def _detect_root(self):
        cwd = Path.cwd()
        markers = ["data", "models", "notebooks", "configs", "README.md", "pyproject.toml"]
        for parent in [cwd] + list(cwd.parents):
            if any((parent / m).exists() for m in markers):
                return parent
        return cwd

    def _create_dirs(self, create, folders=None):

        # Determine which paths to create
        if folders is None:
            folders_to_create = list(self._path_map.keys())
        elif folders == "custom":
            folders_to_create = list(self._path_map.keys())
        elif isinstance(folders, str):
            folders_to_create = [folders]
        elif isinstance(folders, list):
            folders_to_create = folders
        else:
            folders_to_create = []

        invalid = [f for f in folders_to_create if f not in self._path_map]

        if invalid:
            raise ValueError(f"Invalid folder groups: {invalid}")

        self._created_groups = folders_to_create  # store for show()

        # Flatten paths
        if create:
            paths_to_create = [p for key in folders_to_create for p in self._path_map.get(key, [])]

            for path in paths_to_create:
                path.mkdir(parents=True, exist_ok=True)

    def show(self):
        for key in self._created_groups:
            print(key)
            for path in self._path_map.get(key, []):
                print(f"  {path}")

    def __getitem__(self, key: str):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"{key} is not a valid project path. Available keys: {self.keys()}")

    def keys(self):
        return [k for k in self.__dict__ if isinstance(getattr(self, k), Path) and k != "root"]

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if isinstance(v, Path) and k != "root"}

    def __repr__(self):
        return f"ProjectPaths(root={self.root})"


if __name__ == "__main__":
    print("___Test_1___")
    test = ProjectPaths(create=False, folders=["data", "reports"], custom_dirs={"modules": "modules", "view": "modules/view"})
    print(test.view)
    test.show()
    print("___Test_2___")
    test2 = ProjectPaths(create=False)
    test2.show()
    for name in ["sql", "data", "models"]:
        print(test2[name])
    print("___Test_3___")
    test3 = ProjectPaths(create=False, custom_dirs={"modules": "modules", "view": "modules/view"})
    test3.show()
    print("___Test_4___")
    test4 = ProjectPaths(create=False, folders="data")
    test4.show()
    print("___Test_5___")
    test5 = ProjectPaths(create=False, folders="data")
    print(test5)
    print("___Test_6___")
    test6 = ProjectPaths(create=True, folders="data", custom_dirs={"modules": "modules", "data": "something"})
    print(test6.keys())
    print("___Test_7___")
    print(test6.as_dict())
