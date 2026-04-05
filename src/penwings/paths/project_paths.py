from pathlib import Path
from typing import Optional


class PathBase:
    """
    Core base class for managing project-related filesystem paths.

    `PathBase` provides a minimal, extensible foundation for defining and
    accessing paths within a project. It centralizes all paths in an internal
    registry and exposes them through both attribute-style (dot notation)
    and dictionary-style access.

    The class is designed to be subclassed by concrete path managers that
    define specific directory structures (e.g. data, models, reports).

    Key features
    ------------
    • Automatic project root detection based on filesystem markers
    • Centralized path registry (`_paths`) as a single source of truth
    • Safe path registration with duplicate protection
    • Attribute-style access: ``paths.data``
    • Dictionary-style access: ``paths['data']``
    • Clean and extensible base for mixins and derived classes

    Root Detection
    --------------
    If no root is provided, the class attempts to detect the project root by
    traversing the current working directory and its parents, looking for
    known marker files.

    By default, the following marker is used:

    - ``pyproject.toml``

    The first directory containing any marker is considered the project root.
    If no markers are found, the current working directory is used.

    Parameters
    ----------
    root : str or pathlib.Path, optional
        The project root directory. If provided, it overrides automatic
        root detection.

    Attributes
    ----------
    root : pathlib.Path
        The detected or user-defined project root directory.

    _paths : dict[str, pathlib.Path | Any]
        Internal registry storing all paths and path-like objects.
        This acts as the single source of truth for all path access.

    Methods
    -------
    _detect_root()
        Detect the project root by scanning parent directories for markers.

    _add_path(name, path)
        Register a new path in the internal registry.

    __getitem__(key)
        Access a registered path using dictionary-style access.

    __getattr__(name)
        Access a registered path using attribute-style access.

    __repr__()
        Return a string representation of the instance.

    Notes
    -----
    - All paths should be registered via :meth:`_add_path` to ensure
      consistency and avoid accidental overwrites.
    - Direct assignment of attributes (e.g. ``self.data = ...``) is discouraged,
      as it bypasses the internal registry.
    - This class does not enforce that all registered values are
      ``pathlib.Path`` instances, allowing flexibility for advanced use
      cases (e.g. nested path nodes).

    Examples
    --------
    Basic usage in a subclass:

    >>> class MyPaths(PathBase):
    ...     def __init__(self, root=None):
    ...         super().__init__(root)
    ...         self._add_path("data", self.root / "data")
    ...         self._add_path("models", self.root / "models")

    >>> paths = MyPaths()
    >>> paths.data
    PosixPath('.../data')

    >>> paths["models"]
    PosixPath('.../models')

    Attempting to access a non-existing path:

    >>> paths["unknown"]
    KeyError: "'unknown' not found. Available keys: [...]"
    """

    def __init__(self, root=None):
        self._paths = {}
        self._paths["root"] = Path(root) if root else self._detect_root()

    def __repr__(self):
        return f"{self.__class__.__name__}(root={self.root})"

    @property
    def root(self):
        return self._paths["root"]

    def _detect_root(self):
        cwd = Path.cwd()
        markers = ["pyproject.toml"]
        for parent in [cwd] + list(cwd.parents):
            if any((parent / m).exists() for m in markers):
                return parent
        return cwd

    def _add_path(self, name: str, path: Path):
        if name in self._paths:
            raise ValueError(f"Path '{name}' already exists")
        self._paths[name] = path

    def __getitem__(self, key: str):
        try:
            return self._paths[key]
        except KeyError:
            raise KeyError(f"{key!r} not found. Available keys: {list(self._paths.keys())}")

    def __getattr__(self, name):
        if name in self._paths:
            return self._paths[name]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class PathMixin:
    """
    Requires:
        self._paths: dict[str, Path]
    """

    def keys(self):
        return [k for k, v in self._paths.items() if isinstance(v, Path) and k != "root"]

    def as_dict(self):
        return {k: v for k, v in self._paths.items() if isinstance(v, Path) and k != "root"}


class ProjectPaths(PathBase, PathMixin):
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
        super().__init__(root)

        # data
        self._add_path("data", self.root / "data")
        self._add_path("raw", self.root / "data" / "raw")
        self._add_path("processed", self.root / "data" / "processed")
        self._add_path("external", self.root / "data" / "external")

        # ML / features
        self._add_path("feature", self.root / "feature")
        self._add_path("models", self.root / "models")

        # outputs
        self._add_path("reports", self.root / "reports")
        self._add_path("figures", self.root / "reports" / "figures")
        self._add_path("tables", self.root / "reports" / "tables")

        # other
        self._add_path("sql", self.root / "sql")
        self._add_path("notebooks", self.root / "notebooks")
        self._add_path("configs", self.root / "configs")
        self._add_path("logs", self.root / "logs")

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
