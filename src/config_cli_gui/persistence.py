"""Simple platform-aware persistence helpers for remembering the last-used
configuration file.

This module avoids adding an extra dependency by using common platform
conventions (XDG on Linux, APPDATA on Windows, ~/Library on macOS).
The value is stored in a small INI file under an application-specific
configuration directory.
"""

from __future__ import annotations

import configparser
import os
import platform
from pathlib import Path


def get_store_dir(app_name: str = "config-cli-gui") -> Path:
    """Return a platform-appropriate directory for storing small app data.

    The directory is created if it does not exist.
    """
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        base = os.environ.get("APPDATA", home / "AppData" / "Roaming")
        store = Path(base) / app_name
    elif system == "Darwin":
        store = home / "Library" / "Application Support" / app_name
    else:
        # Linux and other Unix-like platforms - follow XDG spec when possible
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            store = Path(xdg) / app_name
        else:
            store = home / ".config" / app_name

    store.mkdir(parents=True, exist_ok=True)
    return store


def _get_store_file(app_name: str = "config-cli-gui") -> Path:
    return get_store_dir(app_name) / "last_used.ini"


def read_last_used_config(app_name: str = "config-cli-gui") -> str | None:
    """Read the last used config file path from the store.

    Returns the recorded path as string or None if not found.
    """
    path = _get_store_file(app_name)
    if not path.exists():
        return None

    cfg = configparser.ConfigParser()
    try:
        cfg.read(path)
        if "last" in cfg and "config" in cfg["last"]:
            return cfg["last"]["config"]
    except Exception:
        return None
    return None


def write_last_used_config(app_name: str, config_path: str) -> None:
    """Write the last used config file path to the store.

    Overwrites previous entry.
    """
    path = _get_store_file(app_name)
    cfg = configparser.ConfigParser()
    cfg["last"] = {"config": str(config_path)}
    with open(path, "w", encoding="utf-8") as f:
        cfg.write(f)
