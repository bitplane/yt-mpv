"""
Installation and setup functionality for yt-mpv
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from yt_mpv.install.setup import configure_ia, setup_bookmarklet, setup_desktop_entry
from yt_mpv.utils.system import run_command


class Installer:
    """Handles installation and setup of yt-mpv"""

    def __init__(self, prefix=None):
        """Initialize with installation prefix.

        Args:
            prefix: Installation prefix (defaults to $HOME/.local)
        """
        self.home = Path.home()
        self.prefix = Path(prefix) if prefix else self.home / ".local"
        self.bin_dir = self.prefix / "bin"
        self.share_dir = self.prefix / "share" / "yt-mpv"
        self.venv_dir = self.share_dir / ".venv"
        self.app_dir = self.prefix / "share" / "applications"

        self.launcher_path = self.bin_dir / "yt-mpv"
        self.desktop_path = self.app_dir / "yt-mpv.desktop"

    def create_dirs(self):
        """Create necessary directories."""
        for d in [self.bin_dir, self.share_dir, self.app_dir, self.venv_dir.parent]:
            d.mkdir(parents=True, exist_ok=True)

    def install(self):
        """Install yt-mpv.

        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Installing yt-mpv to {self.prefix}...")
        self.create_dirs()

        # Create virtualenv using current Python interpreter
        if not (self.venv_dir / "bin" / "python").exists():
            print(f"Creating virtualenv at {self.venv_dir}")
            try:
                run_command([sys.executable, "-m", "venv", str(self.venv_dir)])
            except Exception as e:
                print(f"Failed to create virtualenv: {e}")
                return False

        # Get dependencies
        venv_pip = self.venv_dir / "bin" / "pip"

        # Setup environment to ensure we're using the venv
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(self.venv_dir)
        env["PATH"] = f"{self.venv_dir}/bin:{env.get('PATH', '')}"

        # Install core dependencies
        try:
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

        except Exception as e:
            print(f"Failed to install dependencies: {e}")
            return False

        # Write launcher script
        if not self.write_launcher_script():
            return False

        # Setup desktop file
        if not setup_desktop_entry(self.launcher_path, self.desktop_path):
            print(
                "Warning: Could not set up desktop integration. URI handler may not work."
            )

        print(f"yt-mpv installed successfully to {self.prefix}")
        return True

    def write_launcher_script(self):
        """Create launcher script.

        Returns:
            bool: True if successful, False otherwise
        """
        launcher_content = f"""#!/bin/bash
# Launcher for yt-mpv

# Activate virtualenv and launch
source "{self.venv_dir}/bin/activate"
python -m yt_mpv launch "$@"
"""
        try:
            with open(self.launcher_path, "w") as f:
                f.write(launcher_content)
            self.launcher_path.chmod(0o755)  # Make executable
            print(f"Created launcher at {self.launcher_path}")
            return True
        except Exception as e:
            print(f"Failed to create launcher script: {e}")
            return False

    def setup(self):
        """Configure yt-mpv post-installation.

        Returns:
            bool: True if successful, False otherwise
        """
        print("Setting up yt-mpv...")

        # Check for mpv
        if not shutil.which("mpv"):
            print("WARNING: mpv not found in PATH. Please install it.")
            return False

        # Configure internet archive
        venv_bin = self.venv_dir / "bin"
        if not configure_ia(venv_bin):
            print("WARNING: Could not configure Internet Archive.")

        # Open bookmarklet HTML in browser
        if not setup_bookmarklet():
            print("WARNING: Could not open bookmarklet page.")

        print("Setup complete!")
        return True

    def remove(self):
        """Uninstall yt-mpv.

        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Removing yt-mpv from {self.prefix}...")

        # Remove desktop file
        if self.desktop_path.exists():
            try:
                self.desktop_path.unlink()
                print(f"Removed {self.desktop_path}")
            except Exception as e:
                print(f"Could not remove desktop file: {e}")

        # Remove launcher
        if self.launcher_path.exists():
            try:
                self.launcher_path.unlink()
                print(f"Removed {self.launcher_path}")
            except Exception as e:
                print(f"Could not remove launcher: {e}")

        # Remove share directory
        if self.share_dir.exists():
            try:
                shutil.rmtree(self.share_dir)
                print(f"Removed {self.share_dir}")
            except Exception as e:
                print(f"Could not remove share directory: {e}")

        # Update desktop database
        try:
            run_command(["update-desktop-database", str(self.app_dir)], check=False)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        print("yt-mpv removed successfully.")
        return True
