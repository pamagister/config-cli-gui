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
    """Manages all logging configuration and handlers."""

    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: Path = Path("logs"),
        log_file_name: str = "config_cli_gui.log",
    ):
        """
        Initialize the logger manager.
        Args:
            log_level: The initial log level (e.g., "DEBUG", "INFO").
            log_dir: The directory to store log files.
            log_file_name: The name of the log file.
        """
        self.log_level = log_level.upper()
        self.log_dir = log_dir
        self.log_file_name = log_file_name

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
        self.log_dir.mkdir(exist_ok=True)
        log_file = self.log_dir / self.log_file_name

        self.file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def _setup_console_handler(self, formatter: logging.Formatter) -> None:
        """Set up a console handler."""
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


def initialize_logging(log_level: str = "INFO") -> LoggerManager:
    """
    Initialize the global logging system.
    Args:
        log_level: The initial log level.
    Returns:
        The initialized LoggerManager instance.
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager(log_level)
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
