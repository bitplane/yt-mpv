# yt_mpv/__init__.py
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # backport for <3.8

__version__ = version("yt-mpv")
