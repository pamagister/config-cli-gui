"""Settings dialog tests; skipped automatically when no display is available."""

import tkinter as tk
from unittest.mock import patch

import pytest

from config_cli_gui.configtypes.color import Color
from config_cli_gui.configtypes.vector import Vector
from tests.example_project.config.config_example import ConfigParameterManager


@pytest.fixture(scope="module")
def root():
    # One Tk root per module: creating several roots in a row is unreliable on Windows.
    ttkbootstrap = pytest.importorskip("ttkbootstrap")
    try:
        window = ttkbootstrap.Window(themename="darkly")
    except tk.TclError as e:
        pytest.skip(f"no display available: {e}")
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture
def dialog(root, tmp_path):
    from config_cli_gui.gui import SettingsDialogGenerator

    manager = ConfigParameterManager()
    dlg = SettingsDialogGenerator(manager).create_settings_dialog(
        root, config_file=str(tmp_path / "config.yaml")
    )
    yield dlg
    dlg.dialog.destroy()


def test_widgets_round_trip_unchanged_values(dialog):
    values, errors = dialog._collect_values()
    assert errors == []
    expected = {
        f"{p.category}__{p.name}": p.value for p in dialog.config_manager.get_all_parameters()
    }
    assert values == expected


def test_invalid_value_is_reported_and_not_saved(dialog, tmp_path):
    dialog.widgets["misc__some_color"].var.set("#nothex")
    with patch("config_cli_gui.gui.messagebox.showerror") as showerror:
        assert dialog._persist_settings() is False
    assert "misc.some_color" in showerror.call_args.args[1]
    assert not (tmp_path / "config.yaml").exists()


def test_persist_applies_and_saves(dialog, tmp_path):
    dialog.widgets["misc__some_numeric"].set_value(7)
    dialog.widgets["gui__point2D"].set_value(Vector(3, 4))
    assert dialog._persist_settings() is True
    manager = dialog.config_manager
    assert manager.misc.some_numeric.value == 7
    assert manager.gui.point2D.value == Vector(3, 4)
    assert (tmp_path / "config.yaml").exists()


def test_reset_tab_restores_defaults(dialog):
    dialog.config_manager.misc.some_color.value = Color(1, 1, 1)
    dialog.widgets["misc__some_color"].set_value(Color(1, 1, 1))
    misc_index = [name for name, _ in dialog._tabs].index("misc")
    dialog.notebook.select(misc_index)
    with patch("config_cli_gui.gui.messagebox.askyesno", return_value=True):
        dialog._on_reset_tab()
    assert dialog.widgets["misc__some_color"].get_value() == Color(255, 0, 0)
