import sys
from unittest.mock import mock_open, patch

import pytest

from config_cli_gui.cli import CliGenerator
from tests.example_project.config.config_example import ProjectConfigManager

# ----------------------------------------------------------------------
# Mock config.yaml content
# ----------------------------------------------------------------------
MOCK_YAML = """\
app:
  date_format: '%Y-%m-%d'
  enable_console_logging: true
  enable_file_logging: true

cli:
  elevation: true
  extract_waypoints: true
  input: ''
  min_dist: 20
  output: ''
"""


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def config_manager():
    return ProjectConfigManager()


@pytest.fixture
def cli_gen(config_manager):
    return CliGenerator(config_manager)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_positional_argument_parsing(cli_gen):
    argv = [
        "prog",
        "--min_dist",
        "77",
        "tests/example_project/example.gpx",
    ]

    with patch.object(sys, "argv", argv):
        parser = cli_gen.create_argument_parser()
        args = parser.parse_args()

    assert args.input == "tests/example_project/example.gpx"
    assert args.min_dist == "77" or args.min_dist == 77


def test_boolean_explicit_true(cli_gen):
    argv = [
        "prog",
        "--elevation",
        "true",
        "tests/file.gpx",
    ]

    with patch.object(sys, "argv", argv):
        parser = cli_gen.create_argument_parser()
        args = parser.parse_args()

    assert args.elevation is True


def test_boolean_explicit_false(cli_gen):
    argv = [
        "prog",
        "--elevation",
        "false",
        "tests/file.gpx",
    ]

    with patch.object(sys, "argv", argv):
        parser = cli_gen.create_argument_parser()
        args = parser.parse_args()

    assert args.elevation is False


def test_boolean_toggle(cli_gen):
    # default elevation=False in CliConfig → toggle makes it True
    argv = [
        "prog",
        "--elevation",
        "--min_dist",
        "42",
        "tests/file.gpx",
    ]

    with patch.object(sys, "argv", argv):
        parser = cli_gen.create_argument_parser()
        args = parser.parse_args()

    assert args.elevation is True


def test_load_config_file_and_override(cli_gen):
    argv = [
        "prog",
        "--config",
        "config.yaml",
        "--min_dist",
        "42",
        "--elevation",
        "false",
        "tests/example_project/file.gpx",
    ]

    with patch.object(sys, "argv", argv):
        with patch("builtins.open", mock_open(read_data=MOCK_YAML)):
            with patch("pathlib.Path.exists", return_value=True):
                params = {}

                def fake_main(conf):
                    nonlocal params
                    params["input"] = conf.cli.input.value
                    params["min_dist"] = conf.cli.min_dist.value
                    params["elevation"] = conf.cli.elevation.value
                    params["extract_waypoints"] = conf.cli.extract_waypoints.value
                    return 0

                exit_code = cli_gen.run_cli(main_function=fake_main)

    assert exit_code == 0
    assert params["input"] == "tests/example_project/file.gpx"
    assert params["min_dist"] == "42" or params["min_dist"] == 42
    assert params["elevation"] is False  # override
    assert params["extract_waypoints"] is True  # from config file


def test_cli_overrides_applied_correctly(cli_gen):
    argv = [
        "prog",
        "--min_dist",
        "55",
        "--output",
        "out.gpx",
        "tests/input.gpx",
    ]

    with patch.object(sys, "argv", argv):
        parser = cli_gen.create_argument_parser()
        args = parser.parse_args()
        overrides = cli_gen.create_config_overrides(args)

    assert overrides["cli__min_dist"] == "55" or overrides["cli__min_dist"] == 55
    assert overrides["cli__output"] == "out.gpx"
    assert overrides["cli__input"] == "tests/input.gpx"
