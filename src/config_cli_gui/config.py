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
    choices: list[Any] | None = None
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
    def type_(self) -> type[Any]:
        """Return the Python type of this parameter’s value."""
        return type(self.value)


class ConfigCategory(BaseModel, ABC):
    """Base class for configuration categories."""

    @abstractmethod
    def get_category_name(self) -> str:
        """Return the unique name for this configuration category."""
        pass

    def get_parameters(self) -> list[ConfigParameter]:
        """Return all `ConfigParameter` instances from this category."""
        params = []
        for value in vars(self).values():  # faster, only instance attrs
            if isinstance(value, ConfigParameter):
                value.category = self.get_category_name()
                params.append(value)
        return params


class ConfigSerializer:
    """Handles serialization and deserialization of custom config types."""

    TYPE_MAPPING = {
        Font: {
            "to_serializable": lambda v: v.to_str(),
            "from_serializable": lambda v: Font.from_list(v)
            if isinstance(v, list)
            else Font.from_str(v),
        },
        Color: {
            "to_serializable": lambda v: v.to_hex(),
            "from_serializable": lambda v: Color.from_list(v)
            if isinstance(v, list)
            else (Color.from_hex(v) if isinstance(v, str) else v),
        },
        Vector: {
            "to_serializable": lambda v: v.to_str(),
            "from_serializable": lambda v: Vector.from_list(v)
            if isinstance(v, list)
            else (Vector.from_str(v) if isinstance(v, str) else v),
        },
        Path: {
            "to_serializable": lambda v: str(v.as_posix()),
            "from_serializable": lambda v: Path(v) if isinstance(v, str) else v,
        },
        datetime: {
            "to_serializable": lambda v: v.isoformat(),
            "from_serializable": lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
        },
    }

    def to_serializable(self, value: Any) -> Any:
        """Convert a value to a serializable format."""
        for type_class, methods in self.TYPE_MAPPING.items():
            if isinstance(value, type_class):
                return methods["to_serializable"](value)
        return value

    def from_serializable(self, value: Any, target_type: type[Any]) -> Any:
        """Convert a value from a serializable format to its original type."""
        for type_class, methods in self.TYPE_MAPPING.items():
            if target_type == type_class:
                return methods["from_serializable"](value)
        return value


class ConfigManager:
    """Manages loading, saving, and accessing configuration categories."""

    def __init__(
        self,
        categories: tuple[ConfigCategory, ...],
        config_file: str | None = None,
        **overrides: Any,
    ):
        self._categories: dict[str, ConfigCategory] = {}
        self._serializer = ConfigSerializer()

        for category in categories:
            if not isinstance(category, ConfigCategory):
                raise TypeError(f"Expected ConfigCategory instance, got {type(category)}")
            self.add_category(category.get_category_name(), category)

        if config_file:
            self.load_from_file(config_file)

        self.apply_overrides(overrides)

    def add_category(self, name: str, category: ConfigCategory) -> None:
        """Register a new configuration category."""
        self._categories[name] = category
        setattr(self, name, category)

    def get_category(self, name: str) -> ConfigCategory | None:
        """Retrieve a category by name."""
        return self._categories.get(name)

    def apply_overrides(self, overrides: dict[str, Any]) -> None:
        """Apply keyword overrides in the format `category__param=value`."""
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

    def load_from_file(self, config_file: str) -> None:
        """Load configuration from a YAML or JSON file."""
        path = Path(config_file)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) if path.suffix.lower() in [".yml", ".yaml"] else json.load(f)

        self._apply_config_data(data)

    def _apply_config_data(self, data: dict[str, Any]) -> None:
        """Apply loaded data to the configuration parameters."""
        for category_name, category_data in data.items():
            category = self._categories.get(category_name)
            if not category:
                continue
            for param_name, param_value in category_data.items():
                if hasattr(category, param_name):
                    param: ConfigParameter = getattr(category, param_name)
                    if isinstance(param, ConfigParameter):
                        target_type = param.type_
                        if isinstance(param.value, Path):
                            target_type = Path
                        deserialized_value = self._serializer.from_serializable(
                            param_value, target_type
                        )
                        param.value = deserialized_value

    def save_to_file(self, config_file: str, format_: str = "auto") -> None:
        """Save the current configuration to a file."""
        path = Path(config_file)
        data = self.to_dict()

        file_format = format_
        if file_format == "auto":
            file_format = "yaml" if path.suffix.lower() in [".yml", ".yaml"] else "json"

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            if file_format == "yaml":
                yaml.dump(data, f, indent=2, sort_keys=False)
            else:
                json.dump(data, f, indent=2)

        if file_format == "yaml":
            self._append_comments_to_yaml(path)

    def to_dict(self) -> dict[str, Any]:
        """Convert all configuration categories to a dictionary."""
        result: dict[str, dict[str, Any]] = {}
        for category_name, category in self._categories.items():
            result[category_name] = {}
            for param in category.get_parameters():
                value = self._serializer.to_serializable(param.value)
                result[category_name][param.name] = value
        return result

    def get_all_parameters(self) -> list[ConfigParameter]:
        """Return a flat list of all parameters from all categories."""
        return [p for c in self._categories.values() for p in c.get_parameters()]

    def get_cli_parameters(self) -> list[ConfigParameter]:
        """Return a list of all parameters that are exposed to the CLI."""
        return [p for p in self.get_all_parameters() if p.is_cli]

    def _append_comments_to_yaml(self, path: Path) -> None:
        """Append helpful metadata comments to the YAML file."""
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        all_params = {p.name: p for p in self.get_all_parameters()}
        current_category = ""

        for line in lines:
            stripped = line.strip()
            if (
                stripped.endswith(":")
                and not stripped.startswith("#")
                and line.lstrip() == stripped
            ):
                current_category = stripped[:-1]
                new_lines.append(line)
                continue

            param_name = stripped.split(":")[0].strip()
            if param_name in all_params:
                param = all_params[param_name]
                if param.category == current_category:
                    indent = " " * (line.find(param_name))
                    comment_parts = [param.help, f"type={param.type_.__name__}"]
                    if param.is_cli:
                        comment_parts.append("[CLI]")
                    if param.choices:
                        comment_parts.append(f"choices={param.choices}")

                    comment = f"{indent}# " + " | ".join(filter(None, comment_parts))
                    new_lines.append(comment)

            new_lines.append(line)

        path.write_text("\n".join(new_lines), encoding="utf-8")
