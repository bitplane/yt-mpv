"""
Core functionality for yt-mpv
"""

# Core functionality imports
from yt_mpv.core.archive import archive_url
from yt_mpv.core.player import check_mpv_installed, play_video, update_yt_dlp

__all__ = ["archive_url", "play_video", "check_mpv_installed", "update_yt_dlp"]
