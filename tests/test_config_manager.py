import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from config_cli_gui.config import (
    Color,
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
)


class ExampleCategory(ConfigCategory):
    bg_color: ConfigParameter = ConfigParameter(
        name="bg_color", value=Color(10, 20, 30), help="Background color"
    )
    output_path: ConfigParameter = ConfigParameter(
        name="output_path", value=Path("/default/path"), help="Output directory"
    )
    timestamp: ConfigParameter = ConfigParameter(
        name="timestamp", value=datetime(2023, 1, 1, 12, 0, 0), help="Start time"
    )
    count: ConfigParameter = ConfigParameter(name="count", value=5, help="Simple integer")

    def get_category_name(self) -> str:
        return "example"


def test_color_basic():
    c = Color(0, 51, 255)
    assert c.to_list() == [0, 51, 255]
    assert c.to_hex() == "#0033ff"
    assert c.to_rgb() == (0.0, 0.2, 1.0)
    assert str(c) == "#0033ff"


def test_color_clamping():
    c = Color(-5, 260, 500)
    assert c.to_list() == [0, 255, 255]


def test_color_from_list():
    c = Color.from_list([200, 100, 50])
    assert c.to_hex() == "#c86432"


def test_color_from_hex():
    c = Color.from_hex("#c86432")
    assert c.to_list() == [200, 100, 50]


def test_config_parameter_cli_auto_flag():
    p = ConfigParameter(name="debug", value=True, is_cli=True)
    assert p.cli_arg == "--debug"
    assert p.choices == [True, False]


def test_config_category_get_parameters():
    cat = ExampleCategory()
    params = cat.get_parameters()
    assert len(params) == 4
    names = {p.name for p in params}
    assert {"bg_color", "output_path", "timestamp", "count"} == names


def test_config_manager_initialization():
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))

    assert mgr.get_category("example") is cat
    assert hasattr(mgr, "example")


def test_config_manager_overrides():
    cat = ExampleCategory()

    ConfigManager((cat,), example__count=99, example__output_path="/new/path")

    assert cat.count.value == 99
    assert str(cat.output_path.value) == "/new/path"


def test_load_from_json(tmp_path):
    json_data = {
        "example": {
            "bg_color": "#c86432",
            "output_path": "/tmp/test",
            "timestamp": "2023-05-01T10:00:00",
            "count": 42,
        }
    }

    path = tmp_path / "config.json"
    path.write_text(json.dumps(json_data))

    cat = ExampleCategory()
    ConfigManager((cat,), config_file=str(path))

    assert cat.bg_color.value.to_list() == [200, 100, 50]
    assert str(cat.output_path.value.as_posix()) == "/tmp/test"
    assert cat.count.value == 42
    assert cat.timestamp.value == datetime(2023, 5, 1, 10, 0, 0)


def test_load_from_yaml(tmp_path):
    yaml_data = """
example:
  bg_color: [100, 150, 200]
  output_path: "/tmp/yamlpath"
  timestamp: "2024-02-20T12:00:00"
  count: 7
"""
    path = tmp_path / "config.yaml"
    path.write_text(yaml_data)

    cat = ExampleCategory()
    ConfigManager((cat,), config_file=str(path))

    assert cat.bg_color.value.to_list() == [100, 150, 200]
    assert str(cat.output_path.value.as_posix()) == "/tmp/yamlpath"
    assert cat.timestamp.value == datetime(2024, 2, 20, 12, 0, 0)
    assert cat.count.value == 7


def test_save_to_json(tmp_path):
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))

    out = tmp_path / "out.json"
    mgr.save_to_file(str(out), format_="json")

    written = json.loads(out.read_text())
    assert written["example"]["bg_color"] == "#0a141e"
    assert written["example"]["count"] == 5
    assert written["example"]["output_path"] == "/default/path"


def test_save_to_yaml_with_comments(tmp_path):
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))

    out = tmp_path / "out.yaml"

    # Patch the internal comment function to check it is called
    with patch.object(mgr, "_append_comments_to_yaml") as mock_comments:
        mgr.save_to_file(str(out), format_="yaml")
        mock_comments.assert_called_once()

    text = out.read_text()
    assert "example:" in text


def test_to_dict():
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))
    d = mgr.to_dict()

    assert d["example"]["bg_color"] == "#0a141e"
    assert isinstance(d["example"]["timestamp"], str)


def test_get_all_parameters():
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))
    params = mgr.get_all_parameters()
    assert len(params) == 4


def test_get_cli_parameters():
    cat = ExampleCategory()
    cat.count.is_cli = True
    mgr = ConfigManager((cat,))
    cli_params = mgr.get_cli_parameters()

    assert len(cli_params) == 1
    assert cli_params[0].name == "count"


def test_load_missing_file():
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))
    with pytest.raises(FileNotFoundError):
        mgr.load_from_file("no_such_file.json")


def test_invalid_category():
    with pytest.raises(TypeError):
        ConfigManager((123,))


def test_append_comments_to_yaml(tmp_path):
    cat = ExampleCategory()
    mgr = ConfigManager((cat,))

    path = tmp_path / "file.yaml"
    path.write_text("example:\n  count: 5\n")

    mgr._append_comments_to_yaml(path)

    updated = path.read_text()
    assert "# Simple integer" in updated
