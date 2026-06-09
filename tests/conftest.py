"""Shared fixtures for brain-cli tests."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Make sure the src package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a clean temporary directory."""
    return tmp_path


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    """Redirect config dir to a temp dir so tests don't touch real config."""
    import brain.config as config_mod
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path / "brain")
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "brain" / "config.toml")
    # Also patch profiles file path
    import brain.profiles as profiles_mod
    monkeypatch.setattr(profiles_mod, "PROFILES_FILE", tmp_path / "brain" / "profiles.toml")
    return tmp_path / "brain"


@pytest.fixture
def mock_env_files(tmp_path, monkeypatch):
    """Redirect key lookups to temp .env files."""
    import brain.keys as keys_mod
    profile_env = tmp_path / "profile_env"
    profile_env.mkdir(parents=True, exist_ok=True)
    env_file = profile_env / ".env"
    monkeypatch.setattr(keys_mod, "PROFILE_ENV", env_file)
    monkeypatch.setattr(keys_mod, "GLOBAL_ENV", tmp_path / "global_env" / ".env")
    return env_file
