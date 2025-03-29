"""
Main CLI entry point for yt-mpv
"""

import logging
import sys

from yt_mpv.cli.args import parse_args
from yt_mpv.cli.commands import (
    archive,
    cache,
    check,
    install,
    launch,
    play,
    remove,
    setup,
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
        "install": install,
        "remove": remove,
        "setup": setup,
        "launch": launch,
        "play": play,
        "archive": archive,
        "check": check,
        "cache": cache,
    }

    # Get the handler for the specified command
    handler = command_handlers.get(args.command)
    if not handler:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)

    # Run the command handler
    success = handler(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
