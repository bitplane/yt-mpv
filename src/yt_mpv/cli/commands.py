"""
Command implementations for yt-mpv CLI
"""

import logging
import sys

# Import functionality from other modules - paths will be updated
# when the modules are created
from yt_mpv.archive.checker import check_archive_status
from yt_mpv.core.archive import archive_url
from yt_mpv.core.launcher import main as launch_main
from yt_mpv.core.player import play_video, update_yt_dlp
from yt_mpv.install.installer import Installer
from yt_mpv.utils.cache import clean_all_cache, format_cache_info, purge_cache
from yt_mpv.utils.config import DL_DIR, VENV_BIN, VENV_DIR

logger = logging.getLogger("yt-mpv")


def cmd_install(args):
    """Install command implementation."""
    installer = Installer(args.prefix)
    success = installer.install()
    if success:
        # Run setup after successful installation
        setup_success = installer.setup()
        return setup_success
    return False


def cmd_remove(args):
    """Remove command implementation."""
    installer = Installer(args.prefix)
    return installer.remove()


def cmd_setup(args):
    """Setup command implementation."""
    installer = Installer(args.prefix)
    return installer.setup()


def cmd_launch(args):
    """Launch command implementation."""
    # Pass the URL to the launch script
    sys.argv = [sys.argv[0], args.url]
    launch_main()
    return True


def cmd_play(args):
    """Play command implementation."""
    # Update yt-dlp if requested
    if args.update_ytdlp:
        update_yt_dlp(VENV_DIR, VENV_BIN)

    # Parse additional MPV args if provided
    mpv_args = args.mpv_args.split() if args.mpv_args else []

    # Play the video
    return play_video(args.url, mpv_args)


def cmd_archive(args):
    """Archive command implementation."""
    # Update yt-dlp if requested
    if args.update_ytdlp:
        update_yt_dlp(VENV_DIR, VENV_BIN)

    # Archive the URL
    return archive_url(args.url, DL_DIR, VENV_BIN)


def cmd_check(args):
    """Check command implementation."""
    result = check_archive_status(args.url)
    if result:
        print(result)
        return True
    else:
        print("URL not found in archive.org", file=sys.stderr)
        return False


def cmd_cache(args):
    """Cache command implementation."""
    if args.cache_command == "info":
        # Show cache information using the formatted output
        print(format_cache_info())
        return True

    elif args.cache_command == "clean":
        if args.all:
            # Remove all files using the dedicated function
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
