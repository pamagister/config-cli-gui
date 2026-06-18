"""Centralized logging configuration for config_cli_gui.

This module provides a unified logging setup that supports:
- File logging with rotation
- GUI integration via a custom handler
- Configurable log levels
- Structured logging with consistent formatting
"""

import logging
import logging.handlers
import sys
from collections.abc import Callable
from pathlib import Path


class GuiLogHandler(logging.Handler):
    """Custom logging handler that can write to a GUI text widget."""

    def __init__(self, writer: Callable[[str], None] | None = None):
        """
        Initialize the handler.
        Args:
            writer: A callable that takes a string and writes it to the GUI.
        """
        super().__init__()
        self.writer = writer
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the GUI if a writer is available.
        Args:
            record: The log record to emit.
        """
        if self.writer:
            try:
                msg = self.format(record) + "\n"
                self.writer(msg)
            except Exception:
                # Fail silently to avoid recursive logging errors
                pass


class LoggerManager:
    """Manages all logging configuration and handlers.

    Accepts explicit parameters for integration with the project's
    configuration system. All file-size related checks are performed once
    during initialization and clamped to the allowed range.
    """

    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: Path = Path("logs"),
        log_file_name: str = "config_cli_gui.log",
        log_file_max_size: int | None = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
    ):
        """
        Initialize the logger manager.
        Args:
            log_level: The initial log level (e.g., "DEBUG", "INFO").
            log_dir: The directory to store log files.
            log_file_name: The name of the log file.
            log_file_max_size: Maximum log file size in MB (clamped to 0..100).
            enable_file_logging: Whether to enable file logging.
            enable_console_logging: Whether to enable console logging.
        """
        self.log_level = log_level.upper()
        self.log_dir = log_dir
        self.log_file_name = log_file_name

        # Validate and clamp file size (MB). Must be >= 0 and <= 100.
        if log_file_max_size is None:
            # keep the previous hard-coded default of 10 MB when not provided
            self.log_file_max_size_mb = 10
        else:
            try:
                size_mb = int(log_file_max_size)
            except Exception:
                size_mb = 10
            # clamp to allowed range
            if size_mb < 0:
                size_mb = 0
            if size_mb > 100:
                size_mb = 100
            self.log_file_max_size_mb = size_mb

        # Enable/disable handlers
        self.enable_file_logging = bool(enable_file_logging)
        self.enable_console_logging = bool(enable_console_logging)

        self.logger = logging.getLogger("config_cli_gui")
        self.gui_handler: GuiLogHandler | None = None
        self.file_handler: logging.handlers.RotatingFileHandler | None = None
        self.console_handler: logging.StreamHandler | None = None

        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure all logging handlers and formatters."""
        self.logger.handlers.clear()
        self.logger.setLevel(self.log_level)

        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        self._setup_file_handler(detailed_formatter)
        self._setup_console_handler(simple_formatter)
        self._setup_gui_handler()

    def _setup_file_handler(self, formatter: logging.Formatter) -> None:
        """Set up a rotating file handler."""
        # Only create file handler when enabled
        if not self.enable_file_logging:
            self.file_handler = None
            return

        self.log_dir.mkdir(exist_ok=True)
        log_file = self.log_dir / self.log_file_name

        max_bytes = int(self.log_file_max_size_mb) * 1024 * 1024

        # If max_bytes is 0, RotatingFileHandler will effectively never rotate.
        self.file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=5,
            encoding="utf-8",
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def _setup_console_handler(self, formatter: logging.Formatter) -> None:
        """Set up a console handler."""
        if not self.enable_console_logging:
            self.console_handler = None
            return

        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.console_handler)

    def _setup_gui_handler(self) -> None:
        """Set up the GUI handler (initially without a writer)."""
        self.gui_handler = GuiLogHandler()

    def connect_gui_writer(self, writer: Callable[[str], None]) -> None:
        """
        Connect a GUI writer to the logging system.
        Args:
            writer: A callable that takes a string and writes it to the GUI.
        """
        if self.gui_handler:
            self.logger.removeHandler(self.gui_handler)

        self.gui_handler = GuiLogHandler(writer)
        self.logger.addHandler(self.gui_handler)

    def disconnect_gui_writer(self) -> None:
        """Disconnect the GUI writer."""
        if self.gui_handler:
            self.logger.removeHandler(self.gui_handler)
            self.gui_handler = GuiLogHandler()  # Re-create a handler without a writer

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """
        Get a logger instance.
        Args:
            name: The name of the logger (defaults to the main project logger).
        Returns:
            A logger instance.
        """
        if name:
            return logging.getLogger(f"config_cli_gui.{name}")
        return self.logger

    def set_log_level(self, level: str) -> None:
        """
        Change the log level dynamically.
        Args:
            level: The new log level (e.g., "DEBUG", "INFO").
        """
        self.log_level = level.upper()
        self.logger.setLevel(self.log_level)

    def log_config_summary(self) -> None:
        """Log a summary of the current configuration."""
        self.logger.info("=== Configuration Summary ===")
        self.logger.info(f"Log level: {self.log_level}")
        self.logger.info("==============================")


_logger_manager: LoggerManager | None = None


def initialize_logging(
    log_level: str = "INFO",
    log_file_max_size: int | None = None,
    enable_file_logging: bool | None = None,
    enable_console_logging: bool | None = None,
    log_dir: Path | None = None,
    log_file_name: str | None = None,
) -> LoggerManager:
    """
    Initialize the global logging system.

    Accepts individual configuration values (no dependency on AppConfig).
    Args:
        log_level: The initial log level.
        log_file_max_size: Maximum log file size in MB (clamped to 0..100).
        enable_file_logging: Enable or disable file logging. When None, defaults to True.
        enable_console_logging: Enable or disable console logging. When None, defaults to True.
        log_dir: Directory for log files. When None, defaults to Path('logs').
        log_file_name: Log filename. When None, defaults to 'config_cli_gui.log'.
    Returns:
        The initialized LoggerManager instance.
    """
    global _logger_manager
    if _logger_manager is None:
        # Defaults: file and console logging enabled unless explicitly disabled
        if enable_file_logging is None:
            enable_file_logging = True
        if enable_console_logging is None:
            enable_console_logging = True
        if log_dir is None:
            log_dir = Path("logs")
        if log_file_name is None:
            log_file_name = "config_cli_gui.log"

        _logger_manager = LoggerManager(
            log_level=log_level,
            log_dir=log_dir,
            log_file_name=log_file_name,
            log_file_max_size=log_file_max_size,
            enable_file_logging=enable_file_logging,
            enable_console_logging=enable_console_logging,
        )
    return _logger_manager


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance from the global logger manager.
    Args:
        name: The name of the logger (optional).
    Returns:
        A logger instance.
    Raises:
        RuntimeError: If logging has not been initialized.
    """
    if _logger_manager is None:
        raise RuntimeError("Logging not initialized. Call initialize_logging() first.")
    return _logger_manager.get_logger(name)


def get_logger_manager() -> LoggerManager:
    """
    Get the global logger manager instance.
    Returns:
        The LoggerManager instance.
    Raises:
        RuntimeError: If logging has not been initialized.
    """
    if _logger_manager is None:
        raise RuntimeError("Logging not initialized. Call initialize_logging() first.")
    return _logger_manager


def connect_gui_logging(writer: Callable[[str], None]) -> None:
    """
    Connect a GUI writer to the logging system.
    Args:
        writer: A GUI writer object with a write() method.
    """
    manager = get_logger_manager()
    manager.connect_gui_writer(writer)


def disconnect_gui_logging() -> None:
    """Disconnect the GUI from the logging system."""
    manager = get_logger_manager()
    manager.disconnect_gui_writer()
