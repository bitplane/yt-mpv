"""
Command-line argument parsing for yt-mpv
"""

import argparse


def create_parser():
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="yt-mpv: Play YouTube videos in MPV while archiving to archive.org"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install yt-mpv")
    install_parser.add_argument(
        "--prefix", help="Installation prefix (default: $HOME/.local)"
    )

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove yt-mpv")
    remove_parser.add_argument(
        "--prefix", help="Installation prefix (default: $HOME/.local)"
    )

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure yt-mpv")
    setup_parser.add_argument(
        "--prefix", help="Installation prefix (default: $HOME/.local)"
    )

    # Launch command (combined play and archive)
    launch_parser = subparsers.add_parser(
        "launch", help="Launch video player and archive"
    )
    launch_parser.add_argument("url", help="URL to play and archive")

    # Play command (playback only)
    play_parser = subparsers.add_parser("play", help="Play video without archiving")
    play_parser.add_argument("url", help="URL to play")
    play_parser.add_argument(
        "--update-ytdlp", action="store_true", help="Update yt-dlp before playing"
    )
    play_parser.add_argument(
        "--mpv-args",
        help="Additional arguments to pass to mpv (quote and separate with spaces)",
    )

    # Archive command (archiving only)
    archive_parser = subparsers.add_parser(
        "archive", help="Archive video without playing"
    )
    archive_parser.add_argument("url", help="URL to archive")
    archive_parser.add_argument(
        "--update-ytdlp", action="store_true", help="Update yt-dlp before archiving"
    )

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if URL is archived")
    check_parser.add_argument("url", help="URL to check")

    # Cache management commands
    cache_parser = subparsers.add_parser("cache", help="Manage cache files")
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_command", help="Cache command to run"
    )

    # Cache info command
    cache_subparsers.add_parser("info", help="Show cache information")

    # Cache clean command
    cache_clean_parser = cache_subparsers.add_parser("clean", help="Clean cache files")
    cache_clean_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Remove files older than this many days (default: 7)",
    )
    cache_clean_parser.add_argument(
        "--all", action="store_true", help="Remove all cache files"
    )

    return parser


def parse_args(args=None):
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args(args)
