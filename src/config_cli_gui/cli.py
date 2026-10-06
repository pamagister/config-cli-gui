"""Generic CLI generator for configuration framework."""

import argparse
import traceback
from collections.abc import Callable
from logging import Logger, getLogger
from typing import Any

from config_cli_gui import logging as cli_logging
from config_cli_gui.config import ConfigManager, ConfigParameter, ConfigSerializer


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


def _make_type_converter(param: ConfigParameter) -> Callable[[str], Any]:
    """Return an argparse ``type`` callable that converts a string to the parameter's type."""
    serializer = ConfigSerializer()
    target_type = param.type_

    def convert(value: str) -> Any:
        try:
            return serializer.convert(value, target_type)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e)) from e

    # argparse uses __name__ in its error messages ("invalid int value: ...")
    convert.__name__ = param.type_name
    return convert


class CliGenerator:
    """Generates a CLI automatically from a ConfigManager."""

    def __init__(self, config_manager: ConfigManager, app_name: str = "app"):
        self.config_manager = config_manager
        self.app_name = app_name

    # ----------------------------------------------------------------------
    # Argument parser builder
    # ----------------------------------------------------------------------
    def create_argument_parser(self, description: str | None = None) -> argparse.ArgumentParser:
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
            if p.required:  # POSITIONAL ARGUMENT
                kwargs: dict[str, Any] = {"help": p.help}
                if p.choices:
                    kwargs["choices"] = p.choices
                if not isinstance(p.value, (str, bool)):
                    kwargs["type"] = _make_type_converter(p)
                parser.add_argument(p.name, **kwargs)
                continue

            # OPTIONAL FLAG
            flag = p.cli_arg or f"--{p.name}"
            default_hint = f" (default: {p.value})" if p.value not in (None, "") else ""
            kwargs = {
                "help": f"{p.help}{default_hint}",
                "default": argparse.SUPPRESS,
                # dest = parameter name, so that custom flags still map back to the parameter
                "dest": p.name,
            }
            if not p.choices:
                kwargs["metavar"] = flag.lstrip("-").upper().replace("-", "_")

            # Handle different parameter types
            if isinstance(p.value, bool):
                kwargs["nargs"] = "?"  # allow optional argument
                kwargs["default"] = p.value  # default remains as defined
                kwargs["const"] = None  # triggers toggle mode
                kwargs["action"] = ToggleOrBool
            else:
                kwargs["type"] = _make_type_converter(p)
                if p.choices:
                    kwargs["choices"] = p.choices

            parser.add_argument(flag, **kwargs)

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
        main_function: Callable[[ConfigManager, Logger], int],
        description: str | None = None,
        validator: Callable[[ConfigManager, Logger], bool] | None = None,
        logger: Logger | None = None,
        argv: list[str] | None = None,
    ) -> int:
        """Parse the command line, build the effective configuration and run ``main_function``.

        Precedence (lowest to highest): values of the passed config manager,
        the ``--config`` file, command line arguments.

        The passed config manager is left untouched; ``main_function`` and
        ``validator`` receive a copy of the same (sub)class.
        """
        parser = self.create_argument_parser(description)
        args = parser.parse_args(argv)

        if logger is None:
            logger = getLogger(self.app_name)

        config = self.config_manager.copy()

        config_file = getattr(args, "config", None)
        if config_file:
            try:
                config.load_from_file(config_file)
            except (OSError, ValueError) as e:
                logger.error(f"Could not load configuration: {e}")
                return 1

        config.apply_overrides(self.create_config_overrides(args))
        if config.app.log_level.value != self.config_manager.app.log_level.value:
            self._sync_log_level(config)

        # Optional validation
        if validator and not validator(config, logger):
            logger.error("Configuration validation failed.")
            return 1

        # Execute main
        try:
            return main_function(config, logger)
        except KeyboardInterrupt:
            logger.info("Interrupted.")
            return 130
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.debug(traceback.format_exc())
            return 1

    @staticmethod
    def _sync_log_level(config: ConfigManager) -> None:
        """Apply a log level changed by --config/-v/-q to already initialized logging."""
        manager = cli_logging._logger_manager
        if manager is not None:
            manager.set_log_level(str(config.app.log_level.value))
