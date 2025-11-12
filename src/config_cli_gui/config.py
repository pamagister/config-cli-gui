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
    value: Any
    choices: list | tuple | None = None
    help: str = ""
    cli_arg: str = None
    required: bool = False
    is_cli: bool = False
    category: str = "general"

    def __post_init__(self):
        if self.is_cli and self.cli_arg is None and not self.required:
            self.cli_arg = f"--{self.name}"
        if isinstance(self.value, bool) and self.choices is None:
            self.choices = [True, False]

    @property
    def type_(self) -> type:
        """Get the type from the value."""
        return type(self.value)


class ConfigCategory(BaseModel, ABC):
    """Base class for configuration categories."""

    @abstractmethod
    def get_category_name(self) -> str:
        pass

    def get_parameters(self) -> list[ConfigParameter]:
        """Get all ConfigParameter objects from this category."""
        parameters = []
        for field_name in self.__class__.model_fields:
            param = self.model_fields[field_name].default
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

        # Register categories and make accessible as attributes
        for category in categories:
            if not isinstance(category, ConfigCategory):
                raise TypeError(
                    f"Category must be an instance of ConfigCategory, got {type(category)}"
                )
            name = category.get_category_name()
            self.add_category(name, category)

        if config_file:
            self.load_from_file(config_file)

        self._apply_kwargs(kwargs)

    def add_category(self, name: str, category: ConfigCategory):
        """Add a configuration category.

        Args:
            name: Name of the category (e.g., 'app', 'database', 'gui')
            category: Configuration category instance
        """
        self._categories[name] = category
        setattr(self, name, category)

    def get_category(self, name: str) -> ConfigCategory:
        return self._categories.get(name)

    def _apply_kwargs(self, kwargs: dict[str, Any]):
        """Apply keyword overrides: category__param=value"""
        for key, value in kwargs.items():
            if "__" in key:
                category_name, param_name = key.split("__", 1)
                if category_name in self._categories:
                    category = self._categories[category_name]
                    if hasattr(category, param_name):
                        setattr(category, param_name, value)

    def load_from_file(self, config_file: str):
        path = Path(config_file)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) if path.suffix in [".yml", ".yaml"] else json.load(f)
        self._apply_config_data(data)

    def _apply_config_data(self, data: dict):
        for category_name, category_data in data.items():
            category = self._categories.get(category_name)
            if not category:
                continue
            for param_name, param_value in category_data.items():
                if hasattr(category, param_name):
                    param = category.model_fields.get(param_name).default
                    if isinstance(param, ConfigParameter):
                        default_value = getattr(category, param_name)
                        if isinstance(default_value, Color) and isinstance(param_value, list):
                            param_value = Color.from_list(param_value)
                        elif isinstance(default_value, Path):
                            param_value = Path(param_value)
                        elif isinstance(default_value, datetime):
                            param_value = datetime.fromisoformat(param_value)
                        setattr(getattr(self, category_name), param_name, param_value)

    def save_to_file(self, config_file: str, format_: str = "auto"):
        """Save current configuration to file with enhanced YAML formatting and comments.

        Args:
            config_file (str): The path to the configuration file.
            format_ (str): The format to save the file in ('auto', 'json', 'yaml').
        """
        path = Path(config_file)
        data = self.to_dict()

        if format_ == "auto":
            format_ = "yaml" if path.suffix in [".yml", ".yaml"] else "json"

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            if format_ == "yaml":
                yaml.dump(data, f, indent=2)
            else:
                json.dump(data, f, indent=2)

        if format_ == "yaml":
            self._append_comments_to_yaml(path)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for name, category in self._categories.items():
            category_dict = {}
            for param in category.get_parameters():
                value = getattr(category, param.name).value
                if isinstance(value, Color):
                    value = value.to_list()
                elif isinstance(value, Path):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                category_dict[param.name] = value
            result[name] = category_dict
        return result

    def get_all_parameters(self) -> list[ConfigParameter]:
        return [p for c in self._categories.values() for p in c.get_parameters()]

    def get_cli_parameters(self) -> list[ConfigParameter]:
        return [p for p in self.get_all_parameters() if p.is_cli]

    def _append_comments_to_yaml(self, path: Path):
        """Appends comments to a YAML file based on ConfigParameter metadata.

        Args:
            config_path (Path): The path to the YAML configuration file.
        """

        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        all_parameters = {param.name: param for param in self.get_all_parameters()}
        current_category = None

        for line in lines:
            stripped = line.strip()
            if (
                stripped.endswith(":")
                and not stripped.startswith("#")
                and line.startswith(stripped)
            ):
                current_category = stripped[:-1]
                new_lines.append(line)
            else:
                parts = stripped.split(":", 1)
                if len(parts) > 1:
                    param_name = parts[0].strip()
                    if param_name in all_parameters:
                        param = all_parameters[param_name]
                        if current_category and param.category == current_category:
                            indent = " " * (len(line) - len(stripped))
                            comment = (
                                f"{indent}# {param.help} | "
                                f"type={type(param.value).__name__}, default value={param.value}"
                                f"{' [CLI]' if param.is_cli else ''}"
                            )
                            new_lines.append(comment)
                new_lines.append(line)
        path.write_text("\n".join(new_lines), encoding="utf-8")
