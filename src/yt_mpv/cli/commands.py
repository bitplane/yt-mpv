"""
Command implementations for yt-mpv CLI
"""

import logging
import sys

from yt_mpv.archive.archive_org import check_archive_status
from yt_mpv.archive.yt_dlp import archive_url
from yt_mpv.install.setup import install_app, remove_app, setup_app
from yt_mpv.launcher import main as launch_main
from yt_mpv.player import play_video, update_yt_dlp
from yt_mpv.utils.config import DL_DIR, VENV_BIN, VENV_DIR
from yt_mpv.utils.fs import clean_all_cache, format_cache_info, purge_cache

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
    return play_video(args.url, mpv_args)


def archive(args):
    """Archive command implementation."""
    # Update yt-dlp if requested
    if args.update_ytdlp:
        update_yt_dlp(VENV_DIR, VENV_BIN)

    # Archive the URL
    return archive_url(args.url, DL_DIR, VENV_BIN)


def check(args):
    """Check command implementation."""
    result = check_archive_status(args.url)
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
        print(format_cache_info())
        return True

    elif args.cache_command == "clean":
        if args.all:
            # Remove all files
            files_deleted, bytes_freed = clean_all_cache()
            if files_deleted > 0:
                print(
                    f"Removed all {files_deleted} files ({bytes_freed / 1048576:.2f} MB)"
                )
            else:
                print("No cache files found")
            return True
        else:
            # Remove files older than specified days
            files_deleted, bytes_freed = purge_cache(max_age_days=args.days)
            if files_deleted > 0:
                print(f"Removed {files_deleted} files ({bytes_freed / 1048576:.2f} MB)")
            else:
                print(f"No files older than {args.days} days found")
            return True
    else:
        print("No cache command specified")
        return False
