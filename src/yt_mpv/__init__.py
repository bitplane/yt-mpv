"""
yt-mpv: Play YouTube videos in MPV while archiving to archive.org
"""

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # backport for <3.8

__version__ = version("yt-mpv")
