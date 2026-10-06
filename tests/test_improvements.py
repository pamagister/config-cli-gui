"""Tests for parameter derivation, type conversion, CLI execution, copies and docs."""

import logging
from datetime import datetime
from pathlib import Path

import pytest

import config_cli_gui
from config_cli_gui import (
    CliGenerator,
    Color,
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
    DocumentationGenerator,
    Font,
    Vector,
)


class MiscCategory(ConfigCategory):
    def get_category_name(self) -> str:
        return "misc"

    color: ConfigParameter = ConfigParameter(value=Color(1, 2, 3), help="Color", is_cli=True)
    out: ConfigParameter = ConfigParameter(
        value=Path("a/b"), help="Output | with pipe", is_cli=True, cli_arg="--target"
    )
    when: ConfigParameter = ConfigParameter(
        value=datetime(2025, 1, 2, 3, 4, 5), help="Time", is_cli=True
    )
    ratio: ConfigParameter = ConfigParameter(value=1.5, help="Ratio")
    count: ConfigParameter = ConfigParameter(value=3, help="Count in misc")
    label: ConfigParameter = ConfigParameter(value="", help="Optional label", is_cli=True)
    nested: ConfigParameter = ConfigParameter(value={"count": 1}, help="Nested dict")


class OtherCategory(ConfigCategory):
    def get_category_name(self) -> str:
        return "other"

    count: ConfigParameter = ConfigParameter(name="count", value=7, help="Count in other")


class MyManager(ConfigManager):
    misc: MiscCategory
    other: OtherCategory

    def __init__(self, config_file: str | None = None, **kwargs):
        super().__init__((MiscCategory(), OtherCategory()), config_file, **kwargs)

    @staticmethod
    def get_app_name() -> str:
        return "my-app"


# ----------------------------------------------------------------------
# ConfigParameter / ConfigCategory
# ----------------------------------------------------------------------
def test_name_and_cli_arg_derived_from_attribute():
    mgr = MyManager()
    assert mgr.misc.color.name == "color"
    assert mgr.misc.color.cli_arg == "--color"
    assert mgr.misc.out.cli_arg == "--target"
    assert mgr.misc.color.category == "misc"


def test_type_name_is_platform_independent():
    assert MyManager().misc.out.type_name == "Path"


def test_reset_to_defaults():
    mgr = MyManager()
    mgr.misc.color.value = Color(9, 9, 9)
    mgr.other.count.value = 99
    mgr.reset_to_defaults()
    assert mgr.misc.color.value == Color(1, 2, 3)
    assert mgr.other.count.value == 7


def test_default_value_is_not_shared_with_value():
    param = MyManager().misc.nested
    param.value["count"] = 5
    assert param.default_value == {"count": 1}


def test_copy_is_independent_and_keeps_subclass():
    mgr = MyManager()
    clone = mgr.copy()
    clone.misc.count.value = 42
    assert isinstance(clone, MyManager)
    assert clone.get_category("misc") is clone.misc
    assert mgr.misc.count.value == 3


# ----------------------------------------------------------------------
# Loading / saving
# ----------------------------------------------------------------------
def test_yaml_round_trip_with_duplicate_parameter_names(tmp_path):
    mgr = MyManager()
    path = tmp_path / "config.yaml"
    mgr.save_to_file(str(path))
    text = path.read_text(encoding="utf-8")

    assert "# Count in misc | type=int" in text
    assert "# Count in other | type=int" in text
    assert "type=Path" in text
    # the nested dict key "count" must not get a parameter comment
    assert text.count("# Count in misc") == 1
    assert text.endswith("\n")

    loaded = MyManager(config_file=str(path))
    assert loaded.to_dict() == mgr.to_dict()


def test_load_coerces_plain_types(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("misc:\n  count: '12'\n  ratio: 2\nother:\n  count: 8\n", encoding="utf-8")
    mgr = MyManager(config_file=str(path))
    assert mgr.misc.count.value == 12
    assert isinstance(mgr.misc.ratio.value, float)
    assert mgr.other.count.value == 8


def test_load_keeps_raw_value_and_warns_on_invalid_entry(tmp_path, caplog):
    path = tmp_path / "config.yaml"
    path.write_text("misc:\n  count: abc\n  ratio: 3.5\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="config_cli_gui"):
        mgr = MyManager(config_file=str(path))
    assert mgr.misc.count.value == "abc"
    assert mgr.misc.ratio.value == 3.5
    assert "misc.count" in caplog.text


def test_load_empty_file(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("", encoding="utf-8")
    assert MyManager(config_file=str(path)).misc.count.value == 3


def test_last_used_config_uses_app_name(tmp_path, isolated_persistence):
    path = tmp_path / "config.yaml"
    mgr = MyManager()
    mgr.save_to_file(str(path))
    assert (isolated_persistence / "my-app" / "last_used.ini").exists()
    assert mgr.get_last_used_config() == str(path)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def test_cli_converts_custom_types_and_custom_flag():
    parser = CliGenerator(MyManager()).create_argument_parser()
    args = parser.parse_args(
        ["--color", "#00ff00", "--target", "x/y", "--when", "2026-01-01 12:00:00"]
    )
    assert args.color == Color(0, 255, 0)
    assert args.out == Path("x/y")
    assert args.when == datetime(2026, 1, 1, 12)


def test_cli_rejects_invalid_value(capsys):
    parser = CliGenerator(MyManager()).create_argument_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--when", "not-a-date"])
    assert "argument --when: Cannot convert 'not-a-date' to datetime" in capsys.readouterr().err


def test_run_cli_passes_subclass_copy_and_applies_precedence(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("misc:\n  count: 5\n  color: '#0000ff'\n", encoding="utf-8")
    mgr = MyManager()
    seen = {}

    def main(conf, _logger):
        seen["type"] = type(conf)
        seen["count"] = conf.misc.count.value
        seen["color"] = conf.misc.color.value
        seen["level"] = conf.app.log_level.value
        return 0

    rc = CliGenerator(mgr).run_cli(main, argv=["--config", str(path), "--color", "#ff0000", "-q"])

    assert rc == 0
    assert seen == {
        "type": MyManager,
        "count": 5,
        "color": Color(255, 0, 0),
        "level": "WARNING",
    }
    # the original manager is not modified
    assert mgr.misc.color.value == Color(1, 2, 3)
    assert mgr.app.log_level.value == "INFO"


def test_run_cli_missing_config_file_returns_error(tmp_path):
    rc = CliGenerator(MyManager()).run_cli(
        lambda conf, log: 0, argv=["--config", str(tmp_path / "missing.yaml")]
    )
    assert rc == 1


# ----------------------------------------------------------------------
# Config types
# ----------------------------------------------------------------------
def test_config_types_equality_and_parsing():
    assert Color.from_hex("#f00") == Color(255, 0, 0)
    assert Color.from_hex("nonsense") == Color(0, 0, 0)
    assert not Color.is_valid_hex("#12345")
    assert Vector(1, 2) == Vector(1, 2) != Vector(1, 2, 3)
    assert Vector.from_list([]) == Vector(0, 0)
    assert Vector.from_str("[1, 2, 3]") == Vector(1.0, 2.0, 3.0)
    assert Font("a.ttf", 12, Color()) == Font("a.ttf", 12.0, Color())
    assert len({Color(1, 2, 3), Color(1, 2, 3)}) == 1


def test_font_list_is_available_lazily():
    assert isinstance(Font.font_names, list)
    assert len(Font.font_names) == len(Font.font_files_sorted)


# ----------------------------------------------------------------------
# Docs / package
# ----------------------------------------------------------------------
def test_docs_escape_pipes_and_use_app_name(tmp_path):
    gen = DocumentationGenerator(MyManager())
    cli_doc = tmp_path / "cli.md"
    config_doc = tmp_path / "config.md"
    gen.generate_cli_markdown_doc(str(cli_doc))
    gen.generate_config_markdown_doc(str(config_doc), link_strategy="none")

    cli_text = cli_doc.read_text(encoding="utf-8")
    assert "my-app [OPTIONS]" in cli_text
    assert "Output \\| with pipe" in cli_text
    assert "`--target`" in cli_text
    assert "*required*" not in cli_text  # nothing is required here, "" is just empty

    config_text = config_doc.read_text(encoding="utf-8")
    assert "Configuration File Reference" not in config_text
    assert '## Category "other"' in config_text
    assert "| Path " in config_text


def test_package_exports():
    assert config_cli_gui.__version__
    assert config_cli_gui.ConfigManager is ConfigManager
    with pytest.raises(AttributeError):
        _ = config_cli_gui.DoesNotExist
