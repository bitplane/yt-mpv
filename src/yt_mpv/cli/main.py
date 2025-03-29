"""
Main CLI entry point for yt-mpv
"""

import logging
import sys

from yt_mpv.cli.args import parse_args
from yt_mpv.cli.commands import (
    cmd_archive,
    cmd_cache,
    cmd_check,
    cmd_install,
    cmd_launch,
    cmd_play,
    cmd_remove,
    cmd_setup,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yt-mpv")


def main():
    """Command line entry point."""
    args = parse_args()

    if args.command is None:
        # No command specified, show help
        from yt_mpv.cli.args import create_parser

        create_parser().print_help()
        sys.exit(1)

    # Map commands to their handler functions
    command_handlers = {
        "install": cmd_install,
        "remove": cmd_remove,
        "setup": cmd_setup,
        "launch": cmd_launch,
        "play": cmd_play,
        "archive": cmd_archive,
        "check": cmd_check,
        "cache": cmd_cache,
    }

    # Get the handler for the specified command
    handler = command_handlers.get(args.command)
    if not handler:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)

    # Run the command handler
    try:
        success = handler(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
