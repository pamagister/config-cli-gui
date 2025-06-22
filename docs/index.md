# config-cli-gui: Unified Configuration and Interface Management

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
````

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
# my_project/config.py
from config_cli_gui.config import ConfigParameter, GenericConfigManager, BaseConfigCategory
from pydantic import Field # Make sure pydantic is installed

class MyCliConfig(BaseConfigCategory):
    """CLI-specific parameters for MyProject."""
    input_path: ConfigParameter = ConfigParameter(
        name="input_path",
        default="",
        type_=str,
        help="Path to the input file or directory",
        required=True,
        cli_arg=None # Positional argument
    )
    output_dir: ConfigParameter = ConfigParameter(
        name="output_dir",
        default="./output",
        type_=str,
        help="Directory for output files",
        cli_arg="--output"
    )
    dry_run: ConfigParameter = ConfigParameter(
        name="dry_run",
        default=False,
        type_=bool,
        help="Perform a dry run without making actual changes",
        cli_arg="--dry-run"
    )

class MyAppConfig(BaseConfigCategory):
    """Application-wide settings."""
    log_level: ConfigParameter = ConfigParameter(
        name="log_level",
        default="INFO",
        type_=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level"
    )
    max_threads: ConfigParameter = ConfigParameter(
        name="max_threads",
        default=4,
        type_=int,
        help="Maximum number of processing threads"
    )

class MyGuiConfig(BaseConfigCategory):
    """GUI-specific settings."""
    theme: ConfigParameter = ConfigParameter(
        name="theme",
        default="dark",
        type_=str,
        choices=["light", "dark", "system"],
        help="GUI theme"
    )
    window_size: ConfigParameter = ConfigParameter(
        name="window_size",
        default="800x600",
        type_=str,
        help="Initial GUI window size"
    )

class ProjectConfigManager(GenericConfigManager):
    """Main configuration manager for MyProject."""
    cli: MyCliConfig = Field(default_factory=MyCliConfig)
    app: MyAppConfig = Field(default_factory=MyAppConfig)
    gui: MyGuiConfig = Field(default_factory=MyGuiConfig)

    def __init__(self, config_file: str | None = None, **kwargs):
        # Dynamically register categories for the generic manager
        self.__class__.add_config_category("cli", MyCliConfig)
        self.__class__.add_config_category("app", MyAppConfig)
        self.__class__.add_config_category("gui", MyGuiConfig)
        super().__init__(config_file, **kwargs)

```

### 2\. Generate CLI

Use the generic CLI functions to parse command-line arguments based on your defined `CliConfig`.

```python
# my_project/cli.py
import argparse
from my_project.config import ProjectConfigManager
from config_cli_gui.cli import create_argument_parser, create_config_overrides_from_args

def parse_my_args():
    # Define any project-specific hardcoded CLI args (e.g., --version)
    extra_cli_args = {
        "--version": {"action": "version", "version": "MyProject 1.0.0", "help": "Show program's version number and exit."}
    }

    parser = create_argument_parser(
        config_manager_class=ProjectConfigManager,
        description="MyProject CLI application",
        epilog="""
Examples:
  python -m my_project.cli my_input.txt --output ./results
  python -m my_project.cli --config custom.yaml another_input.csv
        """,
        cli_category_name="cli", # The name of your CLI config category
        extra_arguments=extra_cli_args
    )
    return parser.parse_args()

def main_cli():
    args = parse_my_args()

    # Map generic flags like verbose/quiet to specific log levels if desired
    log_level_map = {
        "verbose": "DEBUG", # Assuming you added a --verbose flag in extra_cli_args
        "quiet": "WARNING"  # Assuming you added a --quiet flag
    }

    cli_overrides = create_config_overrides_from_args(
        args,
        config_manager_class=ProjectConfigManager,
        cli_category_name="cli",
        log_level_map=log_level_map
    )

    # Initialize your project's configuration
    config = ProjectConfigManager(
        config_file=args.config if hasattr(args, "config") and args.config else None,
        **cli_overrides
    )

    print(f"Input Path: {config.cli.input_path.default}")
    print(f"Output Directory: {config.cli.output_dir.default}")
    print(f"Dry Run: {config.cli.dry_run.default}")
    print(f"Log Level: {config.app.log_level.default}")
    # ... your application logic using 'config'

if __name__ == "__main__":
    main_cli()
```

### 3\. Integrate GUI Settings Dialog

The `SettingsDialog` from `config-cli-gui` (or your project's adapted version) can be used to easily create a settings window.

```python
# my_project/gui.py (Simplified example)
import tkinter as tk
from my_project.config import ProjectConfigManager
from config_cli_gui.gui_settings import SettingsDialog # Assuming gui_settings is part of the generic lib or adapted

def open_settings_window(parent_root, config_manager: ProjectConfigManager):
    dialog = SettingsDialog(parent_root, config_manager)
    parent_root.wait_window(dialog.dialog)
    # After dialog closes, config_manager will have updated values if 'OK' was clicked
    print("Settings updated or cancelled.")
    print(f"New GUI Theme: {config_manager.gui.theme.default}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Hide main window for this example
    
    # Initialize your project's config manager
    project_config = ProjectConfigManager() 
    
    open_settings_window(root, project_config)
    
    root.destroy()
```

### 4\. Generate Documentation and Default Config

Use the static methods on your `ProjectConfigManager` to generate `config.yaml`, `cli.md`, and `config.md` files.

```python
# scripts/generate_docs.py (or similar script in your project)
from my_project.config import ProjectConfigManager
import os

# Define output paths
output_dir = "docs/generated"
os.makedirs(output_dir, exist_ok=True)

config_file_path = "config.yaml" # At the project root or similar
cli_doc_path = os.path.join(output_dir, "cli.md")
config_doc_path = os.path.join(output_dir, "config.md")

print(f"Generating default config to: {config_file_path}")
ProjectConfigManager.generate_default_config_file(config_file_path)

print(f"Generating general config documentation to: {config_doc_path}")
ProjectConfigManager.generate_config_markdown_doc(config_doc_path)

print(f"Generating CLI documentation to: {cli_doc_path}")
ProjectConfigManager.generate_cli_markdown_doc(
    output_file=cli_doc_path,
    cli_category_name="cli", # Ensure this matches your CLI config category
    cli_entry_point="python -m my_project.cli" # Your project's actual CLI entry point
)

print("Documentation and default config generation complete.")
```

By following this structure, `config-cli-gui` provides a robust and maintainable foundation for your application's configuration needs.
