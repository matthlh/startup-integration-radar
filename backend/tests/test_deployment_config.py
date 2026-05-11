"""Tests for the deployment-prep settings: DATA_DIR, ALLOWED_ORIGINS, /api/health."""

import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def _reload_app_with_env(monkeypatch, **env):
    """Re-import the app modules so settings/Settings pick up the new env."""
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    # The settings cache is module-level; clear it so the new env wins.
    import app.config

    app.config.get_settings.cache_clear()
    # main + routes pull settings at import time, so reload them too.
    import app.api.routes
    import app.main

    importlib.reload(app.api.routes)
    importlib.reload(app.main)
    return app.main.app


# ─── DATA_DIR ────────────────────────────────────────────────────────────────


def test_data_dir_env_var_routes_storage(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import app.config

    app.config.get_settings.cache_clear()
    settings = app.config.get_settings()
    assert settings.data_dir == str(tmp_path)
    assert settings.companies_store_path == tmp_path / "companies.json"
    assert settings.seed_csv_path == tmp_path / "seed_companies.csv"


def test_default_data_dir_falls_back_to_backend_data(monkeypatch):
    """Default with no env override and no .env file should be backend/data.

    Uses settings_ignoring_dotenv() instead of get_settings() so the developer's
    local .env (which may legitimately set DATA_DIR=data for convenience) does
    not leak into the test.
    """
    monkeypatch.delenv("DATA_DIR", raising=False)
    from app.config import settings_ignoring_dotenv

    settings = settings_ignoring_dotenv()
    assert settings.data_dir.endswith("backend/data")


def test_empty_data_dir_env_falls_back_to_default():
    """A blank DATA_DIR= in .env or the process env should still resolve safely."""
    from app.config import Settings, _DEFAULT_DATA_DIR

    settings = Settings(data_dir="", _env_file=None)
    assert settings.data_dir == _DEFAULT_DATA_DIR


def test_whitespace_data_dir_env_falls_back_to_default():
    from app.config import Settings, _DEFAULT_DATA_DIR

    settings = Settings(data_dir="   ", _env_file=None)
    assert settings.data_dir == _DEFAULT_DATA_DIR


def test_json_store_writes_to_data_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import app.config

    app.config.get_settings.cache_clear()
    # Reload so the store sees the new default.
    import app.storage.json_store as json_store

    importlib.reload(json_store)
    store = json_store.CompanyStore()
    assert store.path == tmp_path / "companies.json"
    assert store.path.exists()  # initialized empty


def test_seed_manager_writes_to_data_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import app.config

    app.config.get_settings.cache_clear()
    import app.services.seed_manager as seed_manager

    importlib.reload(seed_manager)
    row, added = seed_manager.add_seed(domain="example.com")
    assert added is True
    assert row.domain == "example.com"
    expected = tmp_path / "seed_companies.csv"
    assert expected.exists()


# ─── ALLOWED_ORIGINS / CORS ──────────────────────────────────────────────────


def test_allowed_origins_default_includes_localhost(monkeypatch):
    """Same isolation reason as the DATA_DIR default test."""
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    from app.config import settings_ignoring_dotenv

    origins = settings_ignoring_dotenv().cors_origins
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins


def test_allowed_origins_parses_comma_separated_env(monkeypatch):
    monkeypatch.setenv(
        "ALLOWED_ORIGINS", "https://app.vercel.app, http://localhost:3000 ,  "
    )
    import app.config

    app.config.get_settings.cache_clear()
    origins = app.config.get_settings().cors_origins
    assert origins == ["https://app.vercel.app", "http://localhost:3000"]


def test_cors_header_returned_for_allowed_vercel_origin(monkeypatch, tmp_path: Path):
    app_module = _reload_app_with_env(
        monkeypatch,
        DATA_DIR=str(tmp_path),
        ALLOWED_ORIGINS="https://my-scout.vercel.app",
    )
    client = TestClient(app_module)
    response = client.get(
        "/api/health", headers={"Origin": "https://my-scout.vercel.app"}
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://my-scout.vercel.app"
    )


# ─── /api/health ─────────────────────────────────────────────────────────────


def test_health_returns_expected_shape(monkeypatch, tmp_path: Path):
    app_module = _reload_app_with_env(monkeypatch, DATA_DIR=str(tmp_path))
    client = TestClient(app_module)
    payload = client.get("/api/health").json()
    assert payload["ok"] is True
    assert payload["service"] == "integration-scout"
    assert payload["storage"] == str(tmp_path)
    assert payload["version"].count(".") == 2  # x.y.z
    assert payload["external_calls_enabled"] is False
