import os
from pathlib import Path

import gemini_cli_bridge as gcb


def test_get_max_out_env_override(monkeypatch):
    # default should be positive
    assert gcb.get_max_out() > 0
    monkeypatch.setenv("GEMINI_BRIDGE_MAX_OUT", "1234")
    assert gcb.get_max_out() == 1234


def test_env_with_path_whitelist(monkeypatch, tmp_path):
    # Create a directory under tmp
    allow_dir = tmp_path / "bin"
    allow_dir.mkdir(parents=True, exist_ok=True)

    # By default /tmp is not allowed; extra path should be ignored
    monkeypatch.setenv("GEMINI_BRIDGE_EXTRA_PATHS", str(allow_dir))
    env = gcb._env_with_path({})
    assert str(allow_dir) not in env.get("PATH", "")

    # Allow /tmp prefix explicitly, then path should be appended
    monkeypatch.setenv("GEMINI_BRIDGE_ALLOWED_PATH_PREFIXES", str(tmp_path))
    env = gcb._env_with_path({})
    assert str(allow_dir) in env.get("PATH", "")

