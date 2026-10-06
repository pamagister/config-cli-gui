import pytest

from config_cli_gui import persistence


@pytest.fixture(autouse=True)
def isolated_persistence(tmp_path, monkeypatch):
    """Keep "last used config" entries out of the real user profile during tests."""
    store = tmp_path / "persistence"

    def get_store_dir(app_name: str = "config-cli-gui"):
        path = store / app_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    monkeypatch.setattr(persistence, "get_store_dir", get_store_dir)
    return store
