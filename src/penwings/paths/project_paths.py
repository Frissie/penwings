import json

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

    def _create_dirs(self):
        for path in self._paths.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)

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

    def show(self):
        for k, v in self._paths.items():
            if isinstance(v, Path) and k != "root":
                print(f"{k:10}{v}")


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

        self._folders = folders
        self._setup_dirs(self._folders)

        if custom_dirs is not None:
            self._setup_custom_dirs(custom_dirs)

        if create:
            self._create_dirs()

    def _setup_custom_dirs(self, custom_dirs: dict[str, str]):
        for name, rel_path in custom_dirs.items():
            self._add_path(name, self.root / rel_path)

    def _setup_dirs(self, folders=None):
        selected_folders = ["data", "ml", "output", "sql", "notebooks", "config", "logs"] if folders is None else folders
        if isinstance(selected_folders, str):
            selected_folders = [selected_folders]

        def _create_data():
            self._add_path("data", self.root / "data")
            self._add_path("raw", self.root / "data" / "raw")
            self._add_path("processed", self.root / "data" / "processed")
            self._add_path("external", self.root / "data" / "external")

        def _create_ml():
            self._add_path("features", self.root / "features")
            self._add_path("models", self.root / "models")

        def _create_output():
            self._add_path("reports", self.root / "reports")
            self._add_path("figures", self.root / "reports" / "figures")
            self._add_path("tables", self.root / "reports" / "tables")

        def _create_sql():
            self._add_path("sql", self.root / "sql")

        def _create_notebooks():
            self._add_path("notebooks", self.root / "notebooks")

        def _create_config():
            self._add_path("configs", self.root / "configs")

        def _create_logs():
            self._add_path("logs", self.root / "logs")

        modules = {
            "data": _create_data,
            "ml": _create_ml,
            "output": _create_output,
            "sql": _create_sql,
            "notebooks": _create_notebooks,
            "notebook": _create_notebooks,
            "config": _create_config,
            "conf": _create_config,
            "logs": _create_logs,
        }

        for folder in selected_folders:
            func = modules.get(folder)
            if func:
                func()
            else:
                raise ValueError(f"Invalid folder groups: {folder}")


class ConfigPaths(PathBase, PathMixin):
    """
    Manage project folder structures from a JSON configuration file.

    `ConfigPaths` allows defining a project’s directory structure
    dynamically through a JSON file. Each path specified in the JSON
    is registered in the internal `_paths` registry and can be accessed
    via attribute-style (e.g., `paths.data`) or dictionary-style
    (e.g., `paths["data"]`) access.

    Unlike `ProjectPaths`, `ConfigPaths` does not have predefined
    folder groups — the folder structure is entirely determined by
    the JSON configuration.

    Parameters
    ----------
    config : str or pathlib.Path
        Path to the JSON configuration file. The JSON must contain
        a top-level `"paths"` key mapping attribute names to
        relative paths. Example:

        {
            "paths": {
                "data": "data",
                "raw": "data/raw",
                "processed": "data/processed",
                "configs": "configs"
            }
        }

    root : str or pathlib.Path, optional
        Project root directory. If not provided, the root is automatically
        detected using `PathBase` root detection (e.g., by looking for
        `pyproject.toml`).

    create : bool, default True
        If True, directories specified in the JSON configuration will
        be created on the filesystem.

    Attributes
    ----------
    root : pathlib.Path
        The detected or user-defined project root.

    Methods
    -------
    show()
        Display all registered paths, excluding the root.

    as_dict()
        Return a dictionary of all registered paths, excluding the root.

    keys()
        Return a list of registered path attribute names, excluding the root.

    Notes
    -----
    - The JSON configuration determines all paths; there are no
      hardcoded folder groups.
    - All paths are registered via `_add_path` to ensure consistency.
    - Direct assignment to `_paths` is discouraged.
    - Useful for projects where folder structures may change or be
      configurable per project/environment.
    """

    def __init__(
        self,
        config: str | Path,
        root: Optional[str | Path] = None,
        create: bool = True,
    ):
        super().__init__(root)

        config = self._load_config(config)
        self._build_from_config(config)

        if create:
            self._create_dirs()

    def _load_config(self, config):
        config_path = Path(config)
        if not config_path.exists():
            raise ValueError(f"Config file not found: {config_path}")
        if not config_path.suffix == ".json":
            raise ValueError("Config file needs to be a json file")
        return json.loads(config_path.read_text())

    def _build_from_config(self, config: dict):
        """
        Expected format:
        {
            "paths": {
                "data": "data",
                "raw": "data/raw",
                "processed": "data/processed"
                "configs": "configs"
            }
        }
        """
        paths = config.get("paths")
        if not paths:
            raise ValueError("Config must contain a 'paths' key")

        for name, rel_path in paths.items():
            self._add_path(name, self.root / rel_path)


if __name__ == "__main__":
    # print("___Test_1___")
    # test = ProjectPaths(create=False, folders=["data", "ml"], custom_dirs={"modules": "modules", "view": "modules/view"})
    # print(test.view)
    # test.show()
    # print("___Test_2___")
    # test2 = ProjectPaths(create=True)
    # test2.show()
    # for name in ["sql", "data", "models"]:
    #     print(test2[name])
    # print("___Test_3___")
    # test3 = ProjectPaths(create=False, custom_dirs={"modules": "modules", "view": "modules/view"})
    # test3.show()
    # print("___Test_4___")
    # test4 = ProjectPaths(create=False, folders="data")
    # test4.show()
    # print("___Test_5___")
    # test5 = ProjectPaths(create=False, folders="data")
    # print(test5)
    # print("___Test_6___")
    # test6 = ProjectPaths(create=True, folders="data", custom_dirs={"modules": "modules"})
    # print(test6.keys())
    # print("___Test_7___")
    # print(test6.as_dict())

    print("___Test_8___")
    test8 = ConfigPaths(config="src/penwings/paths/test.json", create=False)
    print(test8.root)
    print(test8.data)
    print(test8["config"])
    print(test8.show())
    print(test8._paths)
    print(test8.as_dict())
