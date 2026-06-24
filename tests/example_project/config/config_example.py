"""Central configuration management for config-cli-gui project.

This module provides a single source of truth for all configuration parameters
organized in categories (CLI, App, GUI). It can generate config files, CLI modules,
and documentation from the parameter definitions.
"""

from datetime import datetime
from pathlib import Path

# import ttkbootstrap
from config_cli_gui.config import (
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
)
from config_cli_gui.configtypes.color import Color
from config_cli_gui.configtypes.font import Font
from config_cli_gui.configtypes.vector import Vector
from config_cli_gui.docs import DocumentationGenerator


class CliConfig(ConfigCategory):
    """CLI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "cli"

    # Positional argument
    input: ConfigParameter = ConfigParameter(
        name="input",
        value="",
        help="Path to input (file or folder)",
        required=True,
        is_cli=True,
    )

    # Optional CLI arguments
    output: ConfigParameter = ConfigParameter(
        name="output",
        value="",
        help="Path to output destination",
        is_cli=True,
    )

    min_dist: ConfigParameter = ConfigParameter(
        name="min_dist",
        value=20,
        help="Maximum distance between two waypoints",
        is_cli=True,
    )

    extract_waypoints: ConfigParameter = ConfigParameter(
        name="extract_waypoints",
        value=True,
        help="Extract starting points of each track as waypoint",
        is_cli=True,
    )

    elevation: ConfigParameter = ConfigParameter(
        name="elevation",
        value=False,
        help="Include elevation data in waypoints",
        is_cli=True,
    )


# AppConfig is provided by the core library (centralized). See src/config_cli_gui/config.py


class GuiConfig(ConfigCategory):
    """GUI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "gui"

    window_width: ConfigParameter = ConfigParameter(
        name="window_width",
        value=800,
        help="Default window width",
    )

    window_height: ConfigParameter = ConfigParameter(
        name="window_height",
        value=600,
        help="Default window height",
    )

    log_window_height: ConfigParameter = ConfigParameter(
        name="log_window_height",
        value=200,
        help="Height of the log window in pixels",
    )

    auto_scroll_log: ConfigParameter = ConfigParameter(
        name="auto_scroll_log",
        value=True,
        help="Automatically scroll to the newest log entries",
    )

    max_log_lines: ConfigParameter = ConfigParameter(
        name="max_log_lines",
        value=1000,
        help="Maximum number of log lines to keep in GUI",
    )

    point2D: ConfigParameter = ConfigParameter(
        name="point2D",
        value=Vector(7, 11),
        help="Point in 2D space",
    )

    point3D: ConfigParameter = ConfigParameter(
        name="point3D",
        value=Vector(1.2, 3.4, 5.6),
        help="Point in 3D space",
    )


class MiscConfig(ConfigCategory):
    def get_category_name(self) -> str:
        return "misc"

    some_numeric: ConfigParameter = ConfigParameter(
        name="some_numeric",
        value=42,
        help="Example integer",
    )

    some_vector2d: ConfigParameter = ConfigParameter(
        name="some_vector2d",
        value=Vector(1, 2),
        help="Example vector 2D",
    )

    some_vector3d: ConfigParameter = ConfigParameter(
        name="some_vector3d",
        value=Vector(1.1, 2.2, 3.3),
        help="Example vector 3D",
    )

    some_file: ConfigParameter = ConfigParameter(
        name="some_file",
        value=Path("some_file.txt"),
        help="Path to the file to use",
    )

    some_color: ConfigParameter = ConfigParameter(
        name="some_color",
        value=Color(255, 0, 0),
        help="Color setting for the application",
    )

    some_date: ConfigParameter = ConfigParameter(
        name="some_date",
        value=datetime.fromisoformat("2025-12-31 10:30:45"),
        help="Date setting for the application",
    )

    some_font: ConfigParameter = ConfigParameter(
        name="some_font",
        value=Font("DejaVuSans.ttf", size=12, color=Color(0, 0, 255)),
        help="Font setting for the application",
    )


class ConfigParameterManager(ConfigManager):  # Inherit from ConfigManager
    """Main configuration manager that handles all parameter categories."""

    cli: CliConfig
    gui: GuiConfig
    misc: MiscConfig

    def __init__(self, config_file: str | None = None, **kwargs):
        """Initialize the configuration manager with all parameter categories."""
        categories = (CliConfig(), GuiConfig(), MiscConfig())
        super().__init__(categories, config_file, **kwargs)

    def get_app_name(self) -> str:
        """Return the application identifier for this example project.

        This overrides the library default so that example files use
        "example-app" as their persistence directory/name.
        """
        return "example-app"


def main():
    """Main function to generate config file and documentation."""
    default_config: str = "config.yaml"
    default_cli_doc: str = "docs/usage/cli.md"
    default_config_doc: str = "docs/usage/config.md"
    _config = ConfigParameterManager()
    doc_gen = DocumentationGenerator(_config)
    doc_gen.generate_default_config_file(output_file=default_config)
    print(f"Generated: {default_config}")

    doc_gen.generate_config_markdown_doc(output_file=default_config_doc)
    print(f"Generated: {default_config_doc}")

    doc_gen.generate_cli_markdown_doc(output_file=default_cli_doc)
    print(f"Generated: {default_cli_doc}")


if __name__ == "__main__":
    main()
