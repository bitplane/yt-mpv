"""
Post-installation setup for yt-mpv
"""

import logging
import subprocess
from pathlib import Path

from yt_mpv.install.bookmarklet import open_bookmarklet
from yt_mpv.utils.system import run_command

# Configure logging
logger = logging.getLogger("yt-mpv")


def configure_ia(venv_bin: Path) -> bool:
    """Configure Internet Archive credentials.

    Args:
        venv_bin: Path to virtual environment bin directory

    Returns:
        bool: True if successful, False otherwise
    """
    home = Path.home()
    ia_config = home / ".config" / "ia.ini"
    ia_config_alt = home / ".config" / "internetarchive" / "ia.ini"

    # Check if already configured
    if ia_config.exists() or ia_config_alt.exists():
        logger.info("Internet Archive already configured")
        return True

    # Ensure config directory exists
    if not ia_config.parent.exists():
        ia_config.parent.mkdir(parents=True, exist_ok=True)

    # Run ia configure command
    logger.info("Setting up Internet Archive credentials...")
    venv_ia = venv_bin / "ia"

    try:
        run_command([str(venv_ia), "configure"])
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to configure Internet Archive: {e}")
        print("Please run manually:")
        print(f"{venv_ia} configure")
        return False


def setup_desktop_entry(launcher_path: Path, desktop_path: Path) -> bool:
    """Set up desktop entry for URI handler.

    Args:
        launcher_path: Path to launcher script
        desktop_path: Path to desktop file

    Returns:
        bool: True if successful, False otherwise
    """
    # Ensure parent directory exists
    desktop_path.parent.mkdir(parents=True, exist_ok=True)

    # Read template desktop file
    try:
        from importlib.resources import files

        template_path = files("yt_mpv.install.resources").joinpath("yt-mpv.desktop")
        with open(template_path, "r") as f:
            desktop_content = f.read()
    except (ImportError, AttributeError):
        # Fallback for earlier Python versions
        import pkg_resources

        template_path = pkg_resources.resource_filename(
            "yt_mpv", "install/resources/yt-mpv.desktop"
        )
        with open(template_path, "r") as f:
            desktop_content = f.read()

    # Replace placeholder with actual launcher path
    desktop_content = desktop_content.replace("${INSTALL_PATH}", str(launcher_path))

    # Write desktop file
    try:
        with open(desktop_path, "w") as f:
            f.write(desktop_content)

        logger.info(f"Created desktop entry at {desktop_path}")

        # Update desktop database and MIME types
        for cmd in [
            ["xdg-mime", "default", "yt-mpv.desktop", "x-scheme-handler/x-yt-mpv"],
            ["xdg-mime", "default", "yt-mpv.desktop", "x-scheme-handler/x-yt-mpvs"],
            ["update-desktop-database", str(desktop_path.parent)],
        ]:
            try:
                run_command(cmd, check=False)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning(f"Could not run {cmd[0]}")

        return True
    except Exception as e:
        logger.error(f"Failed to create desktop entry: {e}")
        return False


def setup_bookmarklet() -> bool:
    """Set up bookmarklet in browser.

    Returns:
        bool: True if successful, False otherwise
    """
    return open_bookmarklet()
