import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class Color:
    """Simple color class for RGB values."""

    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))

    def to_list(self) -> list[int]:
        return [self.r, self.g, self.b]

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_list(cls, rgb_list: list[int]) -> "Color":
        if len(rgb_list) >= 3:
            return cls(rgb_list[0], rgb_list[1], rgb_list[2])
        return cls()

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return cls(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
        return cls()

    def __str__(self):
        return self.to_hex()

    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b})"


@dataclass
class ConfigParameter:
    """Represents a single configuration parameter with all its metadata."""

    name: str
    default: Any
    choices: list | tuple | None = None
    help: str = ""
    cli_arg: str = None
    required: bool = False
    is_cli: bool = False
    category: str = "general"

    def __post_init__(self):
        if self.is_cli and self.cli_arg is None and not self.required:
            self.cli_arg = f"--{self.name}"
        if isinstance(self.default, bool) and self.choices is None:
            self.choices = [True, False]

    @property
    def type_(self) -> type:
        """Get the type from the default value."""
        return type(self.default)


class ConfigCategory(BaseModel, ABC):
    """Base class for configuration categories."""

    @abstractmethod
    def get_category_name(self) -> str:
        """Return the category name for this configuration group."""
        pass

    def get_parameters(self) -> list[ConfigParameter]:
        """Get all ConfigParameter objects from this category."""
        parameters = []
        for field_name in self.__class__.model_fields:
            param = getattr(self, field_name)
            if isinstance(param, ConfigParameter):
                param.category = self.get_category_name()
                parameters.append(param)
        return parameters


class ConfigManager:
    """Generic configuration manager that can handle multiple configuration categories."""

    def __init__(self, categories: tuple[ConfigCategory, ...], config_file: str = None, **kwargs):
        """Initialize configuration manager.

        Args:
            config_file: Path to configuration file (JSON or YAML)
            **kwargs: Override parameters in format category__parameter
        """
        self._categories: dict[str, ConfigCategory] = {}

        for category in categories:
            if isinstance(category, ConfigCategory):
                self.add_category(category.get_category_name(), category)
            else:
                raise TypeError(
                    f"Category must be an instance of BaseConfigCategory, got {type(category)}"
                )

        # Load from file if provided
        if config_file:
            self.load_from_file(config_file)

        # Override with provided kwargs
        self._apply_kwargs(kwargs)

    def add_category(self, name: str, category: ConfigCategory):
        """Add a configuration category.

        Args:
            name: Name of the category (e.g., 'app', 'database', 'gui')
            category: Configuration category instance
        """
        self._categories[name] = category

    def get_category(self, name: str) -> ConfigCategory:
        """Get a configuration category by name."""
        return self._categories.get(name)

    def _apply_kwargs(self, kwargs: dict[str, Any]):
        """Apply keyword arguments to override configuration values."""
        for key, value in kwargs.items():
            if "__" in key:
                category_name, param_name = key.split("__", 1)
                if category_name in self._categories:
                    category = self._categories[category_name]
                    if hasattr(category, param_name):
                        param = getattr(category, param_name)
                        if isinstance(param, ConfigParameter):
                            param.default = value

    def load_from_file(self, config_file: str):
        """Load configuration from JSON or YAML file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yml", ".yaml"]:
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)

        # Store loaded data for later application
        self._apply_config_data(config_data)

    def _apply_config_data(self, _loaded_config_data):
        """Apply configuration data to categories."""

        # Apply loaded configuration
        for category_name, category_data in _loaded_config_data.items():
            if category_name in self._categories:
                category = self._categories[category_name]
                for param_name, param_value in category_data.items():
                    if hasattr(category, param_name):
                        param = getattr(category, param_name)
                        if isinstance(param, ConfigParameter):
                            # Handle special types
                            if isinstance(param.default, Color) and isinstance(param_value, list):
                                param.default = Color.from_list(param_value)
                            elif isinstance(param.default, Path):
                                param.default = Path(param_value)
                            elif isinstance(param.default, datetime):
                                param.default = datetime.fromisoformat(param_value)
                            else:
                                param.default = param_value

    def save_to_file(self, config_file: str, format_: str = "auto"):
        """Save current configuration to file with enhanced YAML formatting and comments.

        Args:
            config_file (str): The path to the configuration file.
            format_ (str): The format to save the file in ('auto', 'json', 'yaml').
        """
        config_path = Path(config_file)
        config_data = self.to_dict()

        # Determine format
        if format_ == "auto":
            format_ = "yaml" if config_path.suffix.lower() in [".yml", ".yaml"] else "json"

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            if format_ == "yaml":
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_data, f, indent=2)

        # Append comments for YAML files
        if format_ == "yaml":
            self._append_comments_to_yaml(config_path)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for category_name, category in self._categories.items():
            category_dict = {}
            for param in category.get_parameters():
                value = param.default
                # Handle special types for serialization
                if isinstance(value, Color):
                    value = value.to_list()
                elif isinstance(value, Path):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                category_dict[param.name] = value
            result[category_name] = category_dict
        return result

    def get_all_parameters(self) -> list[ConfigParameter]:
        """Get all parameters from all categories."""
        parameters = []
        for category in self._categories.values():
            parameters.extend(category.get_parameters())
        return parameters

    def get_cli_parameters(self) -> list[ConfigParameter]:
        """Get parameters that are CLI-enabled."""
        cli_parameters = []
        for category in self._categories.values():
            for param in category.get_parameters():
                if param.is_cli:
                    cli_parameters.append(param)
        return cli_parameters

    def _append_comments_to_yaml(self, config_path: Path):
        """Appends comments to a YAML file based on ConfigParameter metadata.

        Args:
            config_path (Path): The path to the YAML configuration file.
        """
        lines = config_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        all_parameters = {param.name: param for param in self.get_all_parameters()}
        current_category = None

        for line in lines:
            stripped_line = line.strip()
            # Check for category (e.g., 'app:')
            # A category should end with ':', not start with '#', and not be indented.
            if (
                stripped_line.endswith(":")
                and not stripped_line.startswith("#")
                and line.startswith(stripped_line)
            ):
                current_category = stripped_line[:-1]
                new_lines.append(line)
            else:
                # Check for parameter (e.g., '  date_format: '%Y-%m-%d'')
                # This needs to handle cases where the value spans multiple lines
                parts = stripped_line.split(":", 1)
                if len(parts) > 1:  # This line might be a parameter definition
                    param_name = parts[0].strip()
                    if param_name in all_parameters:
                        param = all_parameters[param_name]
                        # Ensure the parameter belongs to the current category
                        # and is not a sub-item of a multi-line value
                        if current_category and param.category == current_category:
                            comment_indent = " " * (len(line) - len(stripped_line))
                            comment = (
                                f"{comment_indent}# {param.help} | "
                                f"type={type(param.default).__name__}, default={param.default}"
                                f"{' [CLI]' if param.is_cli else ''}"
                            )
                            new_lines.append(comment)
                new_lines.append(line)
        config_path.write_text("\n".join(new_lines), encoding="utf-8")
