import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from config_cli_gui.configtypes.color import Color
from config_cli_gui.configtypes.font import Font
from config_cli_gui.configtypes.vector import Vector


@dataclass
class ConfigParameter:
    """Represents a single configuration parameter with metadata."""

    name: str
    value: Any
    choices: list | tuple | None = None
    help: str = ""
    cli_arg: str | None = None
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
        """Return the Python type of this parameter’s value."""
        return type(self.value)


class ConfigCategory(BaseModel, ABC):
    """Base class for configuration categories."""

    @abstractmethod
    def get_category_name(self) -> str:
        pass

    def get_parameters(self) -> list[ConfigParameter]:
        """Return ConfigParameter instances that are actual instance attributes."""
        params = []

        for value in vars(self).values():  # faster, only instance attrs
            if isinstance(value, ConfigParameter):
                value.category = self.get_category_name()
                params.append(value)

        return params


class ConfigManager:
    """Generic configuration manager handling multiple configuration categories."""

    def __init__(
        self,
        categories: tuple[ConfigCategory, ...] = None,
        config_file: str | None = None,
        **overrides: Any,
    ):
        self._categories: dict[str, ConfigCategory] = {}

        # Register categories and expose them as attributes
        for category in categories:
            if not isinstance(category, ConfigCategory):
                raise TypeError(f"Expected ConfigCategory instance, got {type(category)}")
            self.add_category(category.get_category_name(), category)

        # Load configuration from file if provided
        if config_file:
            self.load_from_file(config_file)

        # Apply overrides (category__param=value)
        self.apply_overrides(overrides)

    def add_category(self, name: str, category: ConfigCategory):
        self._categories[name] = category
        setattr(self, name, category)

    def get_category(self, name: str) -> ConfigCategory | None:
        return self._categories.get(name)

    def apply_overrides(self, overrides: dict[str, Any]):
        """Apply keyword overrides in format category__param=value."""
        for key, value in overrides.items():
            if "__" not in key:
                continue
            category_name, param_name = key.split("__", 1)
            category = self._categories.get(category_name)
            if category and hasattr(category, param_name):
                param = getattr(category, param_name)
                if isinstance(param, ConfigParameter):
                    param.value = value
                else:
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
                param: ConfigParameter = getattr(category, param_name, None)
                if not isinstance(param, ConfigParameter):
                    continue

                # Type conversions
                if isinstance(param.value, Font) and isinstance(param_value, list):
                    param_value = Font.from_list(param_value)
                if isinstance(param.value, Color) and isinstance(param_value, list):
                    param_value = Color.from_list(param_value)
                if isinstance(param.value, Color) and isinstance(param_value, str):
                    param_value = Color.from_hex(param_value)
                if isinstance(param.value, Vector) and isinstance(param_value, list):
                    param_value = Vector.from_list(param_value)
                if isinstance(param.value, Vector) and isinstance(param_value, str):
                    param_value = Vector.from_str(param_value)
                elif isinstance(param.value, Path):
                    param_value = Path(param_value)
                elif isinstance(param.value, datetime):
                    param_value = datetime.fromisoformat(param_value)

                param.value = param_value

    def save_to_file(self, config_file: str, format_: str = "auto"):
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
        """Convert all configuration categories to a dictionary of plain values."""
        result: dict[str, dict[str, Any]] = {}
        for category in self._categories.values():
            category_name = category.get_category_name()
            result[category_name] = {}
            for param in category.get_parameters():
                val = getattr(category, param.name).value
                if isinstance(val, Font):
                    val = val.to_list()
                elif isinstance(val, Color):
                    val = val.to_hex()
                elif isinstance(val, Vector):
                    val = str(val.to_str())
                elif isinstance(val, Path):
                    val = str(val.as_posix())
                elif isinstance(val, datetime):
                    val = val.isoformat()
                result[category_name][param.name] = val
        return result

    def get_all_parameters(self) -> list[ConfigParameter]:
        return [p for c in self._categories.values() for p in c.get_parameters()]

    def get_cli_parameters(self) -> list[ConfigParameter]:
        return [p for p in self.get_all_parameters() if p.is_cli]

    def _append_comments_to_yaml(self, path: Path):
        """Append helpful metadata comments to the YAML file."""
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        all_params = {p.name: p for p in self.get_all_parameters()}
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
                continue

            parts = stripped.split(":", 1)
            if len(parts) > 1:
                param_name = parts[0].strip()
                if param_name in all_params:
                    param = all_params[param_name]
                    if current_category and param.category == current_category:
                        indent = " " * (len(line) - len(stripped))
                        comment = (
                            f"{indent}# {param.help} | "
                            f"type={param.type_.__name__}"
                            f"{' [CLI]' if param.is_cli else ''}"
                        )
                        if param.choices:
                            comment = comment + f" | choices={param.choices}"
                        new_lines.append(comment)

            new_lines.append(line)

        path.write_text("\n".join(new_lines), encoding="utf-8")
