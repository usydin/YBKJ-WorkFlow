import sys
import os
from pathlib import Path


def is_frozen() -> bool:
    """Check if the application is running in a frozen state (e.g., PyInstaller)."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_app_root() -> Path:
    """
    Get the application root directory.
    - If frozen: The directory where the executable is located.
    - If not frozen: The project root directory (parent of 'app' folder).
    """
    if is_frozen():
        # sys.executable is the path to the .exe file
        return Path(sys.executable).parent.resolve()
    else:
        # Path of this file is project_root/app/path_utils.py
        return Path(__file__).resolve().parent.parent


def get_resource_path(relative_path: str | Path) -> Path:
    """
    Get the absolute path to a resource.
    - If frozen: Resources are extracted to sys._MEIPASS.
    - If not frozen: Resources are relative to the project root.
    """
    if is_frozen():
        # PyInstaller extracts bundled files to sys._MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        base_path = get_app_root()

    return (base_path / relative_path).resolve()


def get_data_dir(dir_name: str = "datapool") -> Path:
    """
    Get the directory for application data (logs, database, etc.).
    For a 'green version' (portable), this is typically a subfolder next to the executable.
    """
    return get_app_root() / dir_name


def get_log_dir() -> Path:
    """Get the directory for log files."""
    return get_app_root() / "logs"


def get_temp_dir() -> Path:
    """Get a directory for temporary files."""
    temp_dir = get_app_root() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir
