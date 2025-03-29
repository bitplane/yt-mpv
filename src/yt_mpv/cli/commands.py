"""
Command implementations for yt-mpv CLI
"""

import logging
import sys

from yt_mpv.archive.archive_org import is_archived
from yt_mpv.archive.yt_dlp import archive_url
from yt_mpv.archive.yt_dlp import update as update_yt_dlp
from yt_mpv.install.setup import configure as setup_app
from yt_mpv.install.setup import install as install_app
from yt_mpv.install.setup import remove as remove_app
from yt_mpv.launcher import main as launch_main
from yt_mpv.player import play as play_player
from yt_mpv.utils.cache import clear, summary
from yt_mpv.utils.config import DL_DIR, VENV_BIN, VENV_DIR

logger = logging.getLogger("yt-mpv")


def install(args):
    """Install command implementation."""
    return install_app(args.prefix)


def remove(args):
    """Remove command implementation."""
    return remove_app(args.prefix)


def setup(args):
    """Setup command implementation."""
    return setup_app(args.prefix)


def launch(args):
    """Launch command implementation."""
    # Pass the URL to the launch script
    sys.argv = [sys.argv[0], args.url]
    launch_main()
    return True


def play(args):
    """Play command implementation."""
    # Update yt-dlp if requested
    if args.update_ytdlp:
        update_yt_dlp(VENV_DIR, VENV_BIN)

    # Parse additional MPV args if provided
    mpv_args = args.mpv_args.split() if args.mpv_args else []

    # Play the video
    return play_player(args.url, mpv_args)


def archive(args):
    """Archive command implementation."""
    # Update yt-dlp if requested
    if args.update_ytdlp:
        update_yt_dlp(VENV_DIR, VENV_BIN)

    # Archive the URL
    return archive_url(args.url, DL_DIR, VENV_BIN)


def check(args):
    """Check command implementation."""
    result = is_archived(args.url)
    if result:
        print(result)
        return True
    else:
        print("URL not found in archive.org", file=sys.stderr)
        return False


def cache(args):
    """Cache command implementation."""
    if args.cache_command == "info":
        # Show cache information
        print(summary())
        return True

    elif args.cache_command == "clean":
        # Just clear all files regardless of --all or --days
        files_deleted, bytes_freed = clear()
        if files_deleted > 0:
            print(f"Removed {files_deleted} files ({bytes_freed / 1048576:.2f} MB)")
        else:
            print("No cache files found")
        return True
    else:
        print("No cache command specified")
        return False
