# Welcome to config-cli-gui

**Unified Configuration and Interface Management**

Provides a generic configuration framework that automatically generates both command-line interfaces and GUI settings dialogs from configuration parameters. 

[![Github CI Status](https://github.com/pamagister/config-cli-gui/actions/workflows/main.yml/badge.svg)](https://github.com/pamagister/config-cli-gui/actions)
[![GitHub release](https://img.shields.io/github/v/release/pamagister/config-cli-gui)](https://github.com/pamagister/config-cli-gui/releases)
[![Read the Docs](https://readthedocs.org/projects/config-cli-gui/badge/?version=stable)](https://config-cli-gui.readthedocs.io/en/stable/)
[![License](https://img.shields.io/github/license/pamagister/config-cli-gui)](https://github.com/pamagister/config-cli-gui/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/pamagister/config-cli-gui)](https://github.com/pamagister/config-cli-gui/issues)
[![PyPI](https://img.shields.io/pypi/v/config-cli-gui)](https://pypi.org/project/config-cli-gui/)
[![Downloads](https://pepy.tech/badge/config-cli-gui)](https://pepy.tech/project/config-cli-gui/)


`config-cli-gui` is a Python library designed to streamline the management of application configurations, 
generating command-line interfaces (CLIs), and dynamically creating graphical user interface (GUI) settings dialogs 
from a single source of truth. It leverages Pydantic for robust parameter definition and offers 
powerful features for consistent configuration across different application entry points.

---

## 🚀 Installation

You can install `config-cli-gui` using pip:

```bash
pip install config-cli-gui
```

---

## ✨ Features

  * **Single Source of Truth**: Define all your application parameters in one place using simple, dataclass-like structures based on Pydantic's `BaseModel`. This ensures consistency and reduces errors across your application.
  * **Categorized Configuration**: Organize your parameters into logical categories (e.g., `cli`, `app`, `gui`) for better structure and maintainability.
  * **Dynamic CLI Generation**: Automatically generate `argparse`-compatible command-line arguments directly from your defined configuration parameters, including help texts, types, and choices.
  * **Config File Management**: Easily load and save configurations from/to YAML or JSON files, allowing users to customize default settings.
  * **GUI Settings Dialogs**: Dynamically create Tkinter-based settings dialogs for your application, allowing users to intuitively modify configuration parameters via a graphical interface.
  * **Documentation Generation**: Generate detailed Markdown documentation for both your CLI options and all configuration parameters, keeping your user guides always up-to-date with your codebase.
  * **Override System**: Supports robust overriding of configuration values via configuration files and command-line arguments, with clear precedence.

---

## 📚 Usage

### 1\. Define Your Configuration

Start by defining your application's configuration parameters in a central `config.py` file within your project. You will inherit from `config-cli-gui`'s `GenericConfigManager` and `BaseConfigCategory`.

```python
# my_project/config_example.py

from config_cli_gui.config import (
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
)


class CliConfig(ConfigCategory):
    """CLI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "cli"

    # Positional argument
    input: ConfigParameter = ConfigParameter(
        name="input",
        default="",
        help="Path to input (file or folder)",
        required=True,
        is_cli=True,
    )

    min_dist: ConfigParameter = ConfigParameter(
        name="min_dist",
        default=20,
        help="Maximum distance between two waypoints",
        is_cli=True,
    )

    extract_waypoints: ConfigParameter = ConfigParameter(
        name="extract_waypoints",
        default=True,
        help="Extract starting points of each track as waypoint",
        is_cli=True,
    )


class AppConfig(ConfigCategory):
    """Application-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "app"

    log_level: ConfigParameter = ConfigParameter(
        name="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the application",
    )

    log_file_max_size: ConfigParameter = ConfigParameter(
        name="log_file_max_size",
        default=10,
        help="Maximum log file size in MB before rotation",
    )


class ProjectConfigManager(ConfigManager):  # Inherit from ConfigManager
    """Main configuration manager that handles all parameter categories."""

    categories = (CliConfig(), AppConfig())

    def __init__(self, config_file: str | None = None, **kwargs):
        """Initialize the configuration manager with all parameter categories."""
        super().__init__(self.categories, config_file, **kwargs)


```

### 2\. Generate CLI

Use the generic CLI functions to parse command-line arguments based on your defined `CliConfig`.

```python
# my_project/cli_example.py
from config_cli_gui.cli import CliGenerator
from config_cli_gui.config import ConfigManager
from tests.example_project.config.config_example import ProjectConfigManager
from tests.example_project.core.base import BaseGPXProcessor
from tests.example_project.core.logging import initialize_logging


def run_main_processing(_config: ConfigManager) -> int:
    """Main processing function that gets called by the CLI generator.

    Args:
        _config: Configuration manager with all settings

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Initialize logging system
    logger_manager = initialize_logging(_config)
    logger = logger_manager.get_logger("config_cli_gui.cli")

    try:
        # Log startup information
        logger.info("Starting config_cli_gui CLI")
        logger_manager.log_config_summary()

        logger.info(f"Processing input")

        # Create and run BaseGPXProcessor
        processor = BaseGPXProcessor(
            _config.get_category("cli").input.default,
            _config.get_category("cli").output.default,
            _config.get_category("cli").min_dist.default,
            _config.get_category("app").date_format.default,
            _config.get_category("cli").elevation.default,
            logger=logger,
        )

        logger.info("Starting conversion process")

        # Run the processing (adjust method name based on your actual implementation)
        result_files = processor.compress_files()
        logger.info(f"Successfully processed {result_files}")
        return 0

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


def main():
    """Main entry point for the CLI application."""
    # Create the base configuration manager
    config_manager = ProjectConfigManager()

    # Create CLI generator
    cli_generator = CliGenerator(config_manager=config_manager, app_name="config_cli_gui")

    # Run the CLI with our main processing function
    return cli_generator.run_cli(
        main_function=run_main_processing,
        description="Example CLI for config-cli-gui using the generic config framework.",
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
```

### 3\. Integrate GUI Settings Dialog

The `SettingsDialog` from `config-cli-gui` (or your project's adapted version) can be used to easily create a settings window.

```python
# my_project/gui_example.py (Simplified example)
import tkinter as tk
from tests.example_project.config.config_example import ProjectConfigManager
from config_cli_gui.gui import GenericSettingsDialog  # Assuming gui_settings is part of the generic lib or adapted


def open_settings_window(parent_root, config_manager: ProjectConfigManager):
    dialog = GenericSettingsDialog(parent_root, config_manager)
    parent_root.wait_window(dialog.dialog)
    # After dialog closes, config_manager will have updated values if 'OK' was clicked
    print("Settings updated or cancelled.")
    print(f"New GUI Theme: {config_manager.get_category('gui').theme.default}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window for this example

    # Initialize your project's config manager
    project_config = ProjectConfigManager()

    open_settings_window(root, project_config)

    root.destroy()
```

### 4\. Generate Documentation and Default Config

Use the static methods on your `ProjectConfigManager` to generate `config.yaml`, `cli.md`, and `config.md` files.

```python
# scripts/generate_docs.py (or similar script in your project)
from tests.example_project.config.config_example import ProjectConfigManager
from config_cli_gui.docs import DocumentationGenerator
import os

# Define output paths
output_dir = "docs/generated"
os.makedirs(output_dir, exist_ok=True)

default_config = "config.yaml"  # At the project root or similar
default_cli_doc = os.path.join(output_dir, "cli.md")
default_config_doc = os.path.join(output_dir, "config.md")
_config = ProjectConfigManager()
doc_gen = DocumentationGenerator(_config)
doc_gen.generate_default_config_file(output_file=default_config)
print(f"Generated: {default_config}")

doc_gen.generate_config_markdown_doc(output_file=default_config_doc)
print(f"Generated: {default_config_doc}")

doc_gen.generate_cli_markdown_doc(output_file=default_cli_doc)
print(f"Generated: {default_cli_doc}")

print("Documentation and default config generation complete.")
```

By following this structure, `config-cli-gui` provides a robust and maintainable foundation for your application's configuration needs.
