"""CLI interface for config-cli-gui using the generic config framework.

This file uses the CliGenerator from the generic config framework.
"""

from config_cli_gui.cli import CliGenerator
from tests.example_project.config.config_example import ProjectConfigManager
from tests.example_project.core.base import BaseGPXProcessor
from tests.example_project.core.logging import initialize_logging


def run_main_processing(_config: ProjectConfigManager) -> int:
    """Main processing function that gets called by the CLI generator.

    Args:
        _config: Configuration manager with all settings

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Initialize logging system
    logger_manager = initialize_logging(_config)
    logger = logger_manager.get_logger("config_cli_gui.cli")

    try:
        # Log startup information
        logger.info("Starting config_cli_gui CLI")
        logger_manager.log_config_summary()

        logger.info("Processing input")

        # Create and run BaseGPXProcessor
        processor = BaseGPXProcessor(
            _config.cli.input.value,
            _config.cli.output.value,
            _config.cli.min_dist.value,
            _config.app.date_format.value,
            _config.cli.elevation.value,
            _config.cli.extract_waypoints.value,
            logger=logger,
        )

        logger.info("Starting conversion process")

        # Run the processing (adjust method name based on your actual implementation)
        result_files = processor.compress_files()
        logger.info(f"Successfully processed {result_files}")
        return 0

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


def main():
    """Main entry point for the CLI application."""
    # Create the base configuration manager
    config_manager = ProjectConfigManager()

    cli_generator = CliGenerator(
        config_manager=config_manager,
        app_name="config_cli_gui",
    )

    return cli_generator.run_cli(
        main_function=run_main_processing,
        description="Example CLI for config-cli-gui using the generic config framework.",
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
