import copy
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from config_cli_gui import persistence
from config_cli_gui.configtypes.color import Color
from config_cli_gui.configtypes.font import Font
from config_cli_gui.configtypes.vector import Vector

logger = logging.getLogger("config_cli_gui")


@dataclass
class ConfigParameter:
    """Represents a single configuration parameter with metadata.

    ``name`` may be omitted when the parameter is declared as an attribute of a
    ``ConfigCategory``; it is then derived from the attribute name.
    """

    name: str = ""
    value: Any = None
    choices: list[Any] | None = None
    help: str = ""
    cli_arg: str | None = None
    required: bool = False
    is_cli: bool = False
    category: str = "general"
    _default: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        self._default = copy.deepcopy(self.value)
        if isinstance(self.value, bool) and self.choices is None:
            self.choices = [True, False]
        self._derive_cli_arg()

    def _derive_cli_arg(self) -> None:
        if self.name and self.is_cli and self.cli_arg is None and not self.required:
            self.cli_arg = f"--{self.name}"

    @property
    def type_(self) -> type[Any]:
        """Return the Python type of this parameter’s value."""
        return type(self.value)

    @property
    def type_name(self) -> str:
        """Return a platform-independent type name (e.g. ``Path`` instead of ``WindowsPath``)."""
        if isinstance(self.value, Path):
            return "Path"
        return self.type_.__name__

    @property
    def default_value(self) -> Any:
        """Return (a copy of) the value the parameter was declared with."""
        return copy.deepcopy(self._default)

    def reset(self) -> None:
        """Restore the value the parameter was declared with."""
        self.value = copy.deepcopy(self._default)


class ConfigCategory(BaseModel, ABC):
    """Base class for configuration categories."""

    def model_post_init(self, __context: Any) -> None:
        category_name = self.get_category_name()
        for attr_name, value in vars(self).items():
            if isinstance(value, ConfigParameter):
                if not value.name:
                    value.name = attr_name
                    value._derive_cli_arg()
                value.category = category_name

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

    def reset_to_defaults(self) -> None:
        """Restore all parameters of this category to their declared values."""
        for param in self.get_parameters():
            param.reset()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("yes", "true", "t", "y", "1", "on"):
            return True
        if lowered in ("no", "false", "f", "n", "0", "off"):
            return False
    raise ValueError(f"Boolean value expected, got {value!r}")


def _to_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Integer value expected, got {value!r}")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"Integer value expected, got {value!r}")
        return int(value)
    return int(value)


def _to_str(value: Any) -> str:
    if isinstance(value, (str, int, float)):
        return str(value)
    raise ValueError(f"String value expected, got {value!r}")


class ConfigSerializer:
    """Handles serialization and deserialization of custom config types."""

    TYPE_MAPPING = {
        Font: {
            "to_serializable": lambda v: v.to_str(),
            "from_serializable": lambda v: (
                v
                if isinstance(v, Font)
                else (Font.from_list(v) if isinstance(v, list) else Font.from_str(v))
            ),
        },
        Color: {
            "to_serializable": lambda v: v.to_hex(),
            "from_serializable": lambda v: (
                Color.from_list(v)
                if isinstance(v, list)
                else (Color.from_hex(v) if isinstance(v, str) else v)
            ),
        },
        Vector: {
            "to_serializable": lambda v: v.to_str(),
            "from_serializable": lambda v: (
                Vector.from_list(v)
                if isinstance(v, list)
                else (Vector.from_str(v) if isinstance(v, str) else v)
            ),
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

    # Lenient conversions for plain types (e.g. "42" -> 42 for an int parameter).
    BUILTIN_CONVERTERS = {
        bool: _to_bool,
        int: _to_int,
        float: float,
        str: _to_str,
    }

    def to_serializable(self, value: Any) -> Any:
        """Convert a value to a serializable format."""
        for type_class, methods in self.TYPE_MAPPING.items():
            if isinstance(value, type_class):
                return methods["to_serializable"](value)
        return value

    def from_serializable(self, value: Any, target_type: type[Any]) -> Any:
        """Convert a value from a serializable format to its original type."""
        if not isinstance(target_type, type):
            return value
        for type_class, methods in self.TYPE_MAPPING.items():
            if issubclass(target_type, type_class):
                return methods["from_serializable"](value)
        return value

    def convert(self, value: Any, target_type: type[Any]) -> Any:
        """Convert ``value`` to ``target_type``, raising ``ValueError`` if impossible.

        Unlike ``from_serializable``, this also coerces the plain types
        ``bool``, ``int``, ``float`` and ``str``.
        """
        if value is None or not isinstance(target_type, type) or target_type is type(None):
            return value
        converter = self.BUILTIN_CONVERTERS.get(target_type)
        if converter is not None:
            if type(value) is target_type:
                return value
            try:
                return converter(value)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Cannot convert {value!r} to {target_type.__name__}: {e}") from e
        try:
            return self.from_serializable(value, target_type)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot convert {value!r} to {target_type.__name__}: {e}") from e


class AppConfig(ConfigCategory):
    """Application-specific configuration parameters (centralized).

    This category was moved from example project to the core library so that
    every project uses a consistent, non-editable application configuration
    section. It contains general application settings such as logging and
    theme preferences.
    """

    def get_category_name(self) -> str:
        return "app"

    date_format: ConfigParameter = ConfigParameter(
        name="date_format",
        value="%Y-%m-%d",
        help="Date format to use",
    )

    log_level: ConfigParameter = ConfigParameter(
        name="log_level",
        value="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the application",
    )

    log_file_max_size: ConfigParameter = ConfigParameter(
        name="log_file_max_size",
        value=2,
        help="Maximum log file size in MB before rotation",
    )

    enable_file_logging: ConfigParameter = ConfigParameter(
        name="enable_file_logging",
        value=True,
        help="Enable logging to file",
    )

    enable_console_logging: ConfigParameter = ConfigParameter(
        name="enable_console_logging",
        value=True,
        help="Enable logging to console",
    )

    # ttkbootstrap.Style().theme_names()
    theme: ConfigParameter = ConfigParameter(
        name="theme",
        value="darkly",
        choices=[
            "cosmo",
            "flatly",
            "litera",
            "minty",
            "lumen",
            "sandstone",
            "yeti",
            "pulse",
            "united",
            "darkly",
            "superhero",
            "solar",
            "cyborg",
            "vapor",
            "simplex",
        ],
        help="GUI theme setting supported by ttkbootstrap",
    )


class ConfigManager:
    """Manages loading, saving, and accessing configuration categories."""

    def __init__(
        self,
        categories: tuple[ConfigCategory, ...],
        config_file: str | None = None,
        persist_last_used: bool = True,
        **overrides: Any,
    ):
        self._categories: dict[str, ConfigCategory] = {}
        self._serializer = ConfigSerializer()
        self.app: AppConfig = AppConfig()

        categories = (self.app, *categories)
        for category in categories:
            if not isinstance(category, ConfigCategory):
                raise TypeError(f"Expected ConfigCategory instance, got {type(category)}")
            self.add_category(category.get_category_name(), category)

        if config_file:
            # Allow callers to opt-out of writing the "last used" persistence
            # entry when loading a configuration during initialization. This
            # is useful for GUIs or libraries that want to load a default
            # config without marking it as the user's last-used file.
            self.load_from_file(config_file, persist_last_used=persist_last_used)

        self.apply_overrides(overrides)

    @staticmethod
    def get_app_name() -> str:
        """Return the application identifier used by persistence helpers.

        Projects can override this method in their concrete ConfigManager to
        provide a different name "my-app-name"
        """
        return "config-cli-gui"

    def add_category(self, name: str, category: ConfigCategory) -> None:
        """Register a new configuration category."""
        self._categories[name] = category
        setattr(self, name, category)

    def get_category(self, name: str) -> ConfigCategory | None:
        """Retrieve a category by name."""
        return self._categories.get(name)

    def get_categories(self) -> tuple[ConfigCategory, ...]:
        values: Iterable[ConfigCategory] = self._categories.values()
        return tuple(values)

    def iter_categories(self) -> Iterator[tuple[str, ConfigCategory]]:
        """Iterate over ``(name, category)`` pairs in registration order."""
        return iter(list(self._categories.items()))

    def get_parameter(self, category_name: str, param_name: str) -> ConfigParameter | None:
        """Return a single parameter or ``None`` if it does not exist."""
        category = self._categories.get(category_name)
        param = getattr(category, param_name, None) if category else None
        return param if isinstance(param, ConfigParameter) else None

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

    def copy(self) -> "ConfigManager":
        """Return an independent copy of the same (sub)class.

        Categories and their parameters are deep-copied; any other attributes
        of a subclass are shared (shallow copy), so they need not be copyable.
        """
        clone = copy.copy(self)
        clone._categories = {}
        for name, category in self._categories.items():
            clone.add_category(name, copy.deepcopy(category))
        return clone

    def reset_to_defaults(self) -> None:
        """Restore every parameter of every category to its declared value."""
        for category in self._categories.values():
            category.reset_to_defaults()

    def load_from_file(self, config_file: str, persist_last_used: bool = True) -> None:
        """Load configuration from a YAML or JSON file."""
        path = Path(config_file)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) if path.suffix.lower() in [".yml", ".yaml"] else json.load(f)

        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValueError(f"Invalid configuration file (expected a mapping): {config_file}")

        self._apply_config_data(data)
        # Persist the information about the last used configuration file so the
        # application can restore the same config on next start. This can be
        # disabled by callers (e.g. GUI startup loading a default file) by
        # passing `persist_last_used=False`.
        if persist_last_used:
            self._write_last_used(path)
        logger.info(f"Loaded configuration from: {path}")

    def _apply_config_data(self, data: dict[str, Any]) -> None:
        """Apply loaded data to the configuration parameters."""
        for category_name, category_data in data.items():
            category = self._categories.get(category_name)
            if not category or not isinstance(category_data, dict):
                continue
            for param_name, param_value in category_data.items():
                param = getattr(category, param_name, None)
                if not isinstance(param, ConfigParameter):
                    continue
                try:
                    param.value = self._serializer.convert(param_value, param.type_)
                except ValueError as e:
                    # Keep the raw value so that a single bad entry does not
                    # prevent the remaining configuration from loading.
                    logger.warning(f"{category_name}.{param_name}: {e}")
                    param.value = param_value

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
                yaml.dump(data, f, indent=2, sort_keys=False, allow_unicode=True)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)

        if file_format == "yaml":
            self._append_comments_to_yaml(path)

        # Record the saved config as the last-used config as well.
        self._write_last_used(path)
        logger.info(f"Saved configuration to: {path}")

    def _write_last_used(self, path: Path) -> None:
        try:
            persistence.write_last_used_config(self.get_app_name(), str(path))
        except Exception as e:
            # Persistence must never break loading or saving a configuration.
            logger.debug(f"Could not record last used config: {e}")

    def get_last_used_config(self) -> str | None:
        """Return the last used config file path recorded by the persistence layer.

        This is a convenience wrapper around persistence.read_last_used_config.
        """
        try:
            return persistence.read_last_used_config(self.get_app_name())
        except Exception:
            return None

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
        """Insert a metadata comment above every parameter in the YAML file."""
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        params = {
            (name, p.name): p for name, c in self._categories.items() for p in c.get_parameters()
        }
        current_category = ""
        param_indent: int | None = None

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue

            indent = len(line) - len(line.lstrip())
            key = stripped.split(":", 1)[0].strip()
            if indent == 0:
                current_category = key
                param_indent = None
            else:
                if param_indent is None:
                    param_indent = indent
                # Deeper lines belong to nested values (dicts/lists), not parameters.
                param = params.get((current_category, key)) if indent == param_indent else None
                if param is not None and stripped.startswith(f"{key}:"):
                    comment_parts = [param.help, f"type={param.type_name}"]
                    if param.is_cli:
                        comment_parts.append("[CLI]")
                    if param.choices:
                        comment_parts.append(f"choices={param.choices}")
                    new_lines.append(" " * indent + "# " + " | ".join(filter(None, comment_parts)))

            new_lines.append(line)

        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
