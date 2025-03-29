"""
Command-line interface for archive checker
"""

import sys

from yt_mpv.archive.checker import check_archive_status


def main():
    """Command line entry point for checking archive status."""
    if len(sys.argv) < 2:
        print("Usage: python -m yt_mpv.archive.cli URL", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    result = check_archive_status(url)

    if result:
        print(result)
        sys.exit(0)
    else:
        print(f"URL not found in archive.org: {url}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
