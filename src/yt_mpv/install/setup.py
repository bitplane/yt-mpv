"""
Installation setup for yt-mpv
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from yt_mpv.archive.archive_org import configure as configure_ia
from yt_mpv.install.bookmarklet import open_browser
from yt_mpv.install.desktop import setup_desktop_entry
from yt_mpv.utils.fs import run_command

logger = logging.getLogger("yt-mpv")


def install(prefix=None):
    """Install yt-mpv.

    Args:
        prefix: Installation prefix (defaults to $HOME/.local)

    Returns:
        bool: True if successful, False otherwise
    """
    # Set up paths
    home = Path.home()
    prefix = Path(prefix) if prefix else home / ".local"
    bin_dir = prefix / "bin"
    share_dir = prefix / "share" / "yt-mpv"
    venv_dir = share_dir / ".venv"
    app_dir = prefix / "share" / "applications"
    launcher_path = bin_dir / "yt-mpv"

    print(f"Installing yt-mpv to {prefix}...")

    # Create necessary directories
    for d in [bin_dir, share_dir, app_dir, venv_dir.parent]:
        d.mkdir(parents=True, exist_ok=True)

    # Create virtualenv using current Python interpreter
    if not (venv_dir / "bin" / "python").exists():
        print(f"Creating virtualenv at {venv_dir}")

        run_command([sys.executable, "-m", "venv", str(venv_dir)])

    # Get dependencies
    venv_pip = venv_dir / "bin" / "pip"

    # Setup environment to ensure we're using the venv
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(venv_dir)
    env["PATH"] = f"{venv_dir}/bin:{env.get('PATH', '')}"

    # Install core dependencies
    run_command([str(venv_pip), "install", "-U", "pip"], env=env)
    run_command(
        [str(venv_pip), "install", "-U", "yt-dlp", "internetarchive", "uv"],
        env=env,
    )

    # Try to use freeze_one for deterministic deps if available
    try:
        from freeze_one import freeze_one

        frozen_deps = freeze_one("yt_mpv")
        run_command([str(venv_pip), "install", frozen_deps], env=env)
    except (ImportError, AttributeError):
        # Fall back to installing the package directly
        run_command([str(venv_pip), "install", "-e", "."], env=env)

    # Write launcher script
    launcher_content = f"""#!/bin/bash
# Launcher for yt-mpv

# Activate virtualenv and launch
source "{venv_dir}/bin/activate"
python -m yt_mpv launch "$@"
"""
    with open(launcher_path, "w") as f:
        f.write(launcher_content)
    launcher_path.chmod(0o755)  # Make executable
    print(f"Created launcher at {launcher_path}")

    # Setup desktop file
    if not setup_desktop_entry(
        launcher_path, prefix / "share" / "applications" / "yt-mpv.desktop"
    ):
        print(
            "Warning: Could not set up desktop integration. URI handler may not work."
        )

    print(f"yt-mpv installed successfully to {prefix}")

    # Run setup after successful installation
    setup_success = configure(prefix)
    return setup_success


def configure(prefix=None):
    """Configure yt-mpv post-installation.

    Args:
        prefix: Installation prefix (defaults to $HOME/.local)

    Returns:
        bool: True if successful, False otherwise
    """
    print("Setting up yt-mpv...")

    # Set up paths
    home = Path.home()
    prefix = Path(prefix) if prefix else home / ".local"

    # Check for mpv
    if not shutil.which("mpv"):
        print("WARNING: mpv not found in PATH. Please install it.")
        return False

    # Configure Internet Archive
    if not configure_ia():
        print("WARNING: Could not configure Internet Archive.")

    # Open bookmarklet HTML in browser
    if not open_browser():
        print("WARNING: Could not open bookmarklet page.")

    print("Setup complete!")
    return True


def remove(prefix=None):
    """Uninstall yt-mpv.

    Args:
        prefix: Installation prefix (defaults to $HOME/.local)

    Returns:
        bool: True if successful, False otherwise
    """
    # Set up paths
    home = Path.home()
    prefix = Path(prefix) if prefix else home / ".local"
    bin_dir = prefix / "bin"
    share_dir = prefix / "share" / "yt-mpv"
    app_dir = prefix / "share" / "applications"
    launcher_path = bin_dir / "yt-mpv"
    desktop_path = app_dir / "yt-mpv.desktop"

    print(f"Removing yt-mpv from {prefix}...")

    # Remove desktop file
    if desktop_path.exists():
        try:
            desktop_path.unlink()
            print(f"Removed {desktop_path}")
        except Exception as e:
            print(f"Could not remove desktop file: {e}")

    # Remove launcher
    if launcher_path.exists():
        try:
            launcher_path.unlink()
            print(f"Removed {launcher_path}")
        except Exception as e:
            print(f"Could not remove launcher: {e}")

    # Remove share directory
    if share_dir.exists():
        try:
            shutil.rmtree(share_dir)
            print(f"Removed {share_dir}")
        except Exception as e:
            print(f"Could not remove share directory: {e}")

    # Update desktop database
    try:
        run_command(["update-desktop-database", str(app_dir)], check=False)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    print("yt-mpv removed successfully.")
    return True
