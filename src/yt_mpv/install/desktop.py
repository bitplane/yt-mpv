"""
Desktop integration for yt-mpv
"""

import logging
import subprocess
from pathlib import Path

from yt_mpv.utils.fs import run_command

# Configure logging
logger = logging.getLogger("yt-mpv")


def setup_desktop_entry(launcher_path: Path, desktop_path: Path) -> bool:
    """Set up desktop entry for URI handler."""
    # Ensure parent directory exists
    desktop_path.parent.mkdir(parents=True, exist_ok=True)

    # Create desktop file content
    desktop_content = f"""[Desktop Entry]
Name=YouTube MPV Player & Archiver
Comment=Play videos in mpv and archive to Internet Archive
Type=Application
Exec={launcher_path} %u
Terminal=false
Categories=Network;Video;
MimeType=x-scheme-handler/x-yt-mpv;x-scheme-handler/x-yt-mpvs;
"""

    # Write desktop file
    with open(desktop_path, "w") as f:
        f.write(desktop_content)

    logger.info(f"Created desktop entry at {desktop_path}")

    # Update desktop database and MIME types
    for cmd in [
        [
            "xdg-mime",
            "default",
            f"{desktop_path.name}",
            "x-scheme-handler/x-yt-mpv",
        ],
        [
            "xdg-mime",
            "default",
            f"{desktop_path.name}",
            "x-scheme-handler/x-yt-mpvs",
        ],
        ["update-desktop-database", str(desktop_path.parent)],
    ]:
        try:
            run_command(cmd, check=False)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning(f"Could not run {cmd[0]}")

    return True
