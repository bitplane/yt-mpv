"""
Configuration and paths for yt-mpv
"""

import os
from pathlib import Path

# Common constants
HOME = Path.home()
DL_DIR = HOME / ".cache/yt-mpv"
VENV_DIR = Path(os.environ.get("YT_MPV_VENV", HOME / ".local/share/yt-mpv/.venv"))
VENV_BIN = VENV_DIR / "bin"

# Ensure cache directory exists
DL_DIR.mkdir(parents=True, exist_ok=True)


def get_config_path(config_name=None):
    """Get path to a configuration file or directory."""
    config_dir = HOME / ".config/yt-mpv"
    config_dir.mkdir(parents=True, exist_ok=True)

    if config_name:
        return config_dir / config_name
    return config_dir
