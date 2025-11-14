# config_cli_gui/cli_example.py
"""Generic CLI generator for configuration framework."""

import argparse
import traceback
from collections.abc import Callable
from typing import Any

from config_cli_gui.config import ConfigManager


def str2bool(v: str):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    if v.lower() in ("no", "false", "f", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


class ToggleOrBool(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            # toggle mode
            current = getattr(namespace, self.dest, None)
            default = self.default
            setattr(namespace, self.dest, not default if current is None else not current)
        else:
            # explicit boolean mode
            setattr(namespace, self.dest, str2bool(values))


class CliGenerator:
    """Generates a CLI automatically from a ConfigManager."""

    def __init__(self, config_manager: ConfigManager, app_name: str = "app"):
        self.config_manager = config_manager
        self.app_name = app_name

    # ----------------------------------------------------------------------
    # Argument parser builder
    # ----------------------------------------------------------------------
    def create_argument_parser(self, description: str = None) -> argparse.ArgumentParser:
        if description is None:
            description = f"Command line interface for {self.app_name}"

        parser = argparse.ArgumentParser(description=description)

        # Config file argument
        parser.add_argument("--config", help="Path to configuration file")

        # verbosity
        parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
        parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

        # CLI parameters
        for p in self.config_manager.get_cli_parameters():
            if p.required:  # POSITONAL ARGUMENT
                parser.add_argument(p.name, help=p.help)
                continue

            # OPTIONAL FLAG
            kwargs = {
                "help": f"{p.help} (default: {p.value})",
                "default": argparse.SUPPRESS,
            }

            # Handle different parameter types
            if isinstance(p.value, bool):
                kwargs["nargs"] = "?"  # allow optional argument
                kwargs["default"] = p.value  # default remains as defined
                kwargs["const"] = None  # triggers toggle mode
                kwargs["action"] = ToggleOrBool
            else:
                kwargs["type"] = type(p.value)
                if p.choices:
                    kwargs["choices"] = p.choices

            parser.add_argument(p.cli_arg, **kwargs)

        return parser

    # ----------------------------------------------------------------------
    # convert args → config overrides
    # ----------------------------------------------------------------------
    def create_config_overrides(self, args: argparse.Namespace) -> dict[str, Any]:
        overrides = {}

        for p in self.config_manager.get_cli_parameters():
            if hasattr(args, p.name):
                overrides[f"{p.category}__{p.name}"] = getattr(args, p.name)

        if getattr(args, "verbose", False):
            overrides["app__log_level"] = "DEBUG"
        elif getattr(args, "quiet", False):
            overrides["app__log_level"] = "WARNING"

        return overrides

    # ----------------------------------------------------------------------
    # Main CLI runner
    # ----------------------------------------------------------------------
    def run_cli(
        self,
        main_function: Callable[[ConfigManager], int],
        description: str = None,
        validator: Callable[[ConfigManager], bool] = None,
    ) -> int:
        parser = self.create_argument_parser(description)
        args = parser.parse_args()

        # Load config_file only ONCE
        config = ConfigManager(
            categories=tuple(self.config_manager._categories.values()),
            config_file=getattr(args, "config", None),
        )

        # Apply CLI overrides
        overrides = self.create_config_overrides(args)
        config.apply_overrides(overrides)

        # Optional validation
        if validator and not validator(config):
            print("Configuration validation failed.")
            return 1

        # Execute main
        try:
            return main_function(config)
        except KeyboardInterrupt:
            print("Interrupted.")
            return 130
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            return 1
