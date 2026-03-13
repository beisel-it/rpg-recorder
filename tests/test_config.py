"""
test_config.py — Smoke tests for bot.config module.

Acceptance criteria:
  - Config loads DISCORD_TOKEN from environment
  - Config exposes SESSIONS_DIR (Path) and LOG_LEVEL (str)
  - Missing DISCORD_TOKEN raises an error at import/reload time
"""

import importlib
import os
import sys
from pathlib import Path

import pytest


def _reload_config(monkeypatch, token="test-token-123", sessions_dir=None, log_level=None):
    """Helper: set env vars and reload bot.config, returning the module."""
    if token is None:
        monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    else:
        monkeypatch.setenv("DISCORD_TOKEN", token)

    if sessions_dir is not None:
        monkeypatch.setenv("SESSIONS_DIR", sessions_dir)

    if log_level is not None:
        monkeypatch.setenv("LOG_LEVEL", log_level)

    # Remove cached module so module-level code re-runs
    sys.modules.pop("bot.config", None)

    import bot.config as cfg
    return cfg


class TestConfigLoading:
    def test_loads_discord_token(self, monkeypatch):
        cfg = _reload_config(monkeypatch, token="my-secret-token")
        assert cfg.DISCORD_TOKEN == "my-secret-token"

    def test_sessions_dir_default(self, monkeypatch):
        monkeypatch.delenv("SESSIONS_DIR", raising=False)
        cfg = _reload_config(monkeypatch)
        assert isinstance(cfg.SESSIONS_DIR, Path)
        assert cfg.SESSIONS_DIR == Path("sessions")

    def test_sessions_dir_custom(self, monkeypatch, tmp_path):
        cfg = _reload_config(monkeypatch, sessions_dir=str(tmp_path / "my-sessions"))
        assert cfg.SESSIONS_DIR == Path(str(tmp_path / "my-sessions"))

    def test_log_level_default(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        cfg = _reload_config(monkeypatch)
        assert cfg.LOG_LEVEL == "INFO"

    def test_log_level_custom(self, monkeypatch):
        cfg = _reload_config(monkeypatch, log_level="debug")
        assert cfg.LOG_LEVEL == "DEBUG"   # normalized to uppercase


class TestConfigMissingRequired:
    def test_missing_discord_token_raises(self, monkeypatch):
        """DISCORD_TOKEN is required — missing → KeyError at import time."""
        monkeypatch.delenv("DISCORD_TOKEN", raising=False)
        sys.modules.pop("bot.config", None)

        with pytest.raises(KeyError):
            import bot.config  # noqa: F401
