"""
This module provides a base class for processing GPX files with logging and configuration.
"""

import logging
from pathlib import Path

# It's good practice to have a constant for the application name
# if it's used in multiple places (e.g., for logging).
NAME = "config_cli_gui"


class BaseGPXProcessor:
    """
    A base class for processing GPX files, demonstrating how to integrate
    with the centralized logging and configuration system.
    """

    def __init__(
        self,
        input_files: str | Path | list[str | Path],
        output: Path,
        min_dist: int = 10,
        date_format: str = "%Y-%m-%d",
        elevation: bool = True,
        logger: logging.Logger = None,
    ):
        """
        Initializes the GPX processor.

        Args:
            input_files: A single file path or a list of file paths (as strings or Path objects).
            output: The path to the output file.
            min_dist: The minimum distance for processing.
            date_format: The date format string.
            elevation: A flag to include elevation data.
            logger: An optional logger instance. If not provided, a default logger is created.
        """
        self.input_paths: list[Path] = self._resolve_input_paths(input_files)
        self.output_path: Path = Path(output)
        self.min_dist: int = min_dist
        self.date_format: str = date_format
        self.include_elevation: bool = elevation
        self.logger: logging.Logger = logger or logging.getLogger(NAME)

        self.log_initialization()

    def _resolve_input_paths(self, input_files: str | Path | list[str | Path]) -> list[Path]:
        """
        Resolves the input to a list of Path objects.

        Args:
            input_files: The input file(s) to resolve.

        Returns:
            A list of Path objects.

        Raises:
            ValueError: If the input type is invalid.
        """
        if isinstance(input_files, (str, Path)):
            return [Path(input_files)]
        if isinstance(input_files, list):
            return [Path(p) for p in input_files]
        raise ValueError("Input must be a string, Path, or list of strings/Paths.")

    def log_initialization(self) -> None:
        """Logs the initial configuration of the processor."""
        self.logger.info("GPX Processor initialized with the following settings:")
        self.logger.info(f"  Input files: {[str(p) for p in self.input_paths]}")
        self.logger.info(f"  Output file: {self.output_path}")
        self.logger.info(f"  Minimum distance: {self.min_dist}")
        self.logger.info(f"  Date format: {self.date_format}")
        self.logger.info(f"  Include elevation: {self.include_elevation}")

    def compress_files(self) -> list[str]:
        """
        Shrinks the size of all given GPX/KML files.

        This is a placeholder implementation.

        Returns:
            A list of paths to the compressed files.
        """
        self.logger.info("Compressing files...")
        # In a real implementation, you would process the files here.
        self.logger.info(f"Compressed {len(self.input_paths)} files.")
        return [str(path) for path in self.input_paths]

    def merge_files(self) -> str:
        """
        Merges all input files into a single GPX file with reduced resolution.

        This is a placeholder implementation.

        Returns:
            The path to the merged file.
        """
        self.logger.info("Merging files...")
        # In a real implementation, you would merge the files here.
        self.logger.info(f"Merged {len(self.input_paths)} files into {self.output_path}.")
        return str(self.output_path)

    def extract_pois(self) -> str:
        """
        Extracts all points of interest (POIs) from the input files.

        This is a placeholder implementation.

        Returns:
            The path to the GPX file containing the POIs.
        """
        self.logger.info("Extracting POIs...")
        # In a real implementation, you would extract POIs here.
        self.logger.info(f"Extracted POIs from {len(self.input_paths)} files.")
        return str(self.output_path)
