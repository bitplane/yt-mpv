"""
Tests for the installer functionality.
"""

from pathlib import Path
from unittest.mock import patch

from yt_mpv.install.installer import Installer


def test_installer_init():
    """Test Installer initialization."""
    # Test with default prefix
    with patch("pathlib.Path.home", return_value=Path("/home/user")):
        installer = Installer()
        assert installer.prefix == Path("/home/user/.local")
        assert installer.bin_dir == Path("/home/user/.local/bin")
        assert installer.share_dir == Path("/home/user/.local/share/yt-mpv")

    # Test with custom prefix
    custom_prefix = "/opt/yt-mpv"
    installer = Installer(custom_prefix)
    assert installer.prefix == Path(custom_prefix)
    assert installer.bin_dir == Path(f"{custom_prefix}/bin")
    assert installer.share_dir == Path(f"{custom_prefix}/share/yt-mpv")


def test_create_dirs(tmp_path):
    """Test directory creation."""
    installer = Installer(tmp_path)
    installer.create_dirs()

    assert installer.bin_dir.exists()
    assert installer.share_dir.exists()
