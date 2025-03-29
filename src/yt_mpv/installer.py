"""
Installation and setup functionality for yt-mpv
"""

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from freeze_one import freeze_one


class Installer:
    """Handles installation and setup of yt-mpv"""

    def __init__(self, prefix=None):
        """Initialize with installation prefix."""
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

    def run_command(self, cmd, check=True, env=None, **kwargs):
        """Run a command and return the result."""
        print(f"Running: {' '.join(str(c) for c in cmd)}")
        return subprocess.run(cmd, check=check, env=env, **kwargs)

    def install(self):
        """Install yt-mpv."""
        print(f"Installing yt-mpv to {self.prefix}...")
        self.create_dirs()

        # Create virtualenv using current Python interpreter
        if not (self.venv_dir / "bin" / "python").exists():
            print(f"Creating virtualenv at {self.venv_dir}")
            self.run_command([sys.executable, "-m", "venv", str(self.venv_dir)])

        # Get frozen requirements
        frozen_deps = freeze_one("yt_mpv")

        # Install dependencies into venv
        venv_pip = self.venv_dir / "bin" / "pip"

        # Setup environment to ensure we're using the venv
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(self.venv_dir)
        env["PATH"] = f"{self.venv_dir}/bin:{env.get('PATH', '')}"

        # Install core dependencies
        self.run_command([str(venv_pip), "install", "-U", "pip"], env=env)
        self.run_command(
            [str(venv_pip), "install", "-U", "yt-dlp", "internetarchive", "uv"], env=env
        )
        self.run_command([str(venv_pip), "install", frozen_deps], env=env)

        # Write launcher script
        self.write_launcher_script()

        # Copy desktop file
        self.write_desktop_file()

        # Update desktop database
        self.update_desktop_db()

        print(f"yt-mpv installed successfully to {self.prefix}")
        return True

    def write_launcher_script(self):
        """Create launcher script."""
        launcher_content = f"""#!/bin/bash
# Launcher for yt-mpv

# Activate virtualenv and launch
source "{self.venv_dir}/bin/activate"
python -m yt_mpv.cli launch "$@"
"""
        with open(self.launcher_path, "w") as f:
            f.write(launcher_content)
        self.launcher_path.chmod(0o755)  # Make executable
        print(f"Created launcher at {self.launcher_path}")

    def write_desktop_file(self):
        """Create desktop file for URI handler."""
        desktop_content = f"""[Desktop Entry]
Name=YouTube MPV Player & Archiver
Comment=Play videos in mpv and archive to Internet Archive
Type=Application
Exec={self.launcher_path} %u
Terminal=false
Categories=Network;Video;
MimeType=x-scheme-handler/x-yt-mpv;x-scheme-handler/x-yt-mpvs;
"""
        with open(self.desktop_path, "w") as f:
            f.write(desktop_content)
        print(f"Created desktop entry at {self.desktop_path}")

    def update_desktop_db(self):
        """Update desktop database and MIME types."""
        # Set as default handler for URI schemes
        for cmd in [
            ["xdg-mime", "default", "yt-mpv.desktop", "x-scheme-handler/x-yt-mpv"],
            ["xdg-mime", "default", "yt-mpv.desktop", "x-scheme-handler/x-yt-mpvs"],
            ["update-desktop-database", str(self.app_dir)],
        ]:
            try:
                self.run_command(cmd, check=False)
            except (subprocess.SubprocessError, FileNotFoundError):
                print(f"Warning: Could not run {cmd[0]}")

    def setup(self):
        """Configure yt-mpv post-installation."""
        print("Setting up yt-mpv...")

        # Check for mpv
        if not shutil.which("mpv"):
            print("WARNING: mpv not found in PATH. Please install it.")
            return False

        # Configure internet archive if needed
        ia_config = self.home / ".config" / "ia.ini"
        ia_config_alt = self.home / ".config" / "internetarchive" / "ia.ini"

        if not ia_config.exists() and not ia_config_alt.exists():
            print("Setting up Internet Archive credentials...")
            venv_ia = self.venv_dir / "bin" / "ia"
            try:
                self.run_command([str(venv_ia), "configure"])
            except subprocess.SubprocessError:
                print("Failed to configure Internet Archive. Please run manually:")
                print(f"{venv_ia} configure")
                return False

        # Open bookmarklet HTML in browser
        self.open_bookmarklet()

        print("Setup complete!")
        return True

    def open_bookmarklet(self):
        """Open the bookmarklet HTML in a browser."""
        try:
            import shutil
            from pathlib import Path

            # Use the cache directory to store the bookmarklet HTML
            cache_dir = Path.home() / ".cache/yt-mpv"
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Path for the copied bookmarklet HTML
            dest_path = cache_dir / "bookmarklet.html"

            # Find and copy the original bookmarklet HTML
            try:
                # For Python 3.9+
                from importlib import resources

                bookmark_path = resources.files("yt_mpv.install").joinpath(
                    "bookmark.html"
                )
                shutil.copy(bookmark_path, dest_path)
            except (AttributeError, ImportError):
                # Fallback for earlier Python versions
                import pkg_resources

                bookmarklet_path = pkg_resources.resource_filename(
                    "yt_mpv", "install/bookmark.html"
                )
                shutil.copy(bookmarklet_path, dest_path)

            dest_path.chmod(0o644)

            print(f"Opening bookmarklet page at {dest_path}")

            webbrowser.open(f"file://{dest_path}")

        except Exception as e:
            print(f"Could not open bookmarklet HTML: {e}")

    def remove(self):
        """Uninstall yt-mpv."""
        print(f"Removing yt-mpv from {self.prefix}...")

        # Remove desktop file
        if self.desktop_path.exists():
            self.desktop_path.unlink()
            print(f"Removed {self.desktop_path}")

        # Remove launcher
        if self.launcher_path.exists():
            self.launcher_path.unlink()
            print(f"Removed {self.launcher_path}")

        # Remove share directory
        if self.share_dir.exists():
            shutil.rmtree(self.share_dir)
            print(f"Removed {self.share_dir}")

        # Update desktop database
        try:
            self.run_command(
                ["update-desktop-database", str(self.app_dir)], check=False
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        print("yt-mpv removed successfully.")
        return True
