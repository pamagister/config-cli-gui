"""Unified configuration, CLI and GUI settings management.

The most common classes are re-exported here::

    from config_cli_gui import ConfigCategory, ConfigManager, ConfigParameter

The GUI classes (``SettingsDialogGenerator``, ``GenericSettingsDialog``) are
imported lazily so that CLI-only applications do not load tkinter.
"""

from typing import Any

from config_cli_gui.cli import CliGenerator
from config_cli_gui.config import (
    AppConfig,
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
    ConfigSerializer,
)
from config_cli_gui.configtypes.color import Color
from config_cli_gui.configtypes.font import Font
from config_cli_gui.configtypes.vector import Vector
from config_cli_gui.docs import DocumentationGenerator

try:
    from config_cli_gui._version import version as __version__
except ImportError:  # pragma: no cover - only without setuptools_scm build step
    try:
        from importlib.metadata import version as _metadata_version

        __version__ = _metadata_version("config-cli-gui")
    except Exception:
        __version__ = "0.0.0"

_LAZY_GUI_EXPORTS = ("SettingsDialogGenerator", "GenericSettingsDialog")

__all__ = [
    "AppConfig",
    "CliGenerator",
    "Color",
    "ConfigCategory",
    "ConfigManager",
    "ConfigParameter",
    "ConfigSerializer",
    "DocumentationGenerator",
    "Font",
    "Vector",
    "__version__",
    *_LAZY_GUI_EXPORTS,
]


def __getattr__(name: str) -> Any:
    if name in _LAZY_GUI_EXPORTS:
        from config_cli_gui import gui

        return getattr(gui, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
