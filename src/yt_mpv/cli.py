#!/usr/bin/env python3
"""
Command-line interface for yt-mpv
"""

import argparse
import sys

from yt_mpv.checker import check_archive_status
from yt_mpv.installer import Installer


def main():
    """Command line entry point."""
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

    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch video player")
    launch_parser.add_argument("url", help="URL to play")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if URL is archived")
    check_parser.add_argument("url", help="URL to check")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Create installer with given prefix or default
    if hasattr(args, "prefix"):
        installer = Installer(args.prefix)
    else:
        installer = Installer()

    # Run appropriate command
    if args.command == "install":
        success = installer.install()
        if success:
            # Run setup after successful installation
            setup_success = installer.setup()
            sys.exit(0 if setup_success else 1)
        else:
            sys.exit(1)

    elif args.command == "remove":
        success = installer.remove()
        sys.exit(0 if success else 1)

    elif args.command == "setup":
        success = installer.setup()
        sys.exit(0 if success else 1)

    elif args.command == "launch":
        # Import here to avoid circular imports
        from yt_mpv.launch import main as launch_main

        # Pass the URL to the launch script
        sys.argv = [sys.argv[0], args.url]
        launch_main()

    elif args.command == "check":
        result = check_archive_status(args.url)
        if result:
            print(result)
            sys.exit(0)
        else:
            sys.exit(1)

    # Should never reach here
    sys.exit(1)


if __name__ == "__main__":
    main()
