"""
Cache management functions for yt-mpv
"""

import logging
import time
from collections import namedtuple
from pathlib import Path
from typing import List, Optional, Tuple

from yt_mpv.utils.config import DL_DIR

# Configure logging
logger = logging.getLogger("yt-mpv")

# Define a namedtuple for file information
CacheFileInfo = namedtuple("CacheFileInfo", ["path", "size", "age_days", "mtime"])


def cleanup_cache_files(video_file: Path, info_file: Path) -> bool:
    """
    Remove downloaded video and info files after successful upload.

    Args:
        video_file: Path to the video file
        info_file: Path to the info JSON file

    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    files_to_remove = [video_file, info_file]
    success = True

    for file_path in files_to_remove:
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Removed cache file: {file_path}")
            except OSError as e:
                logger.error(f"Failed to remove file {file_path}: {e}")
                success = False

    return success


def get_cache_dir() -> Path:
    """
    Get the default cache directory path.

    Returns:
        Path: The default cache directory path
    """
    return DL_DIR


def _get_cache_file_info(cache_dir: Optional[Path] = None) -> List[CacheFileInfo]:
    """
    Internal function to get detailed information about cache files.

    Args:
        cache_dir: Cache directory path (defaults to HOME/.cache/yt-mpv)

    Returns:
        List[CacheFileInfo]: List of file information
    """
    if cache_dir is None:
        cache_dir = get_cache_dir()

    # Handle both Path objects and string paths
    if isinstance(cache_dir, str):
        cache_dir = Path(cache_dir)

    if not cache_dir.exists() or not cache_dir.is_dir():
        return []

    now = time.time()
    file_info = []

    for item in cache_dir.iterdir():
        if item.is_file():
            stat = item.stat()
            size = stat.st_size
            mtime = stat.st_mtime
            age_days = (now - mtime) / (24 * 60 * 60)
            file_info.append(CacheFileInfo(item, size, age_days, mtime))

    # Sort by age (oldest first)
    file_info.sort(key=lambda x: x.age_days, reverse=True)

    return file_info


def purge_cache(
    cache_dir: Optional[Path] = None, max_age_days: int = 7
) -> Tuple[int, int]:
    """
    Purge old files from the cache directory.

    Args:
        cache_dir: Cache directory path (defaults to HOME/.cache/yt-mpv)
        max_age_days: Maximum age of files to keep in days

    Returns:
        Tuple[int, int]: (number of files deleted, total bytes freed)
    """
    if cache_dir is None:
        cache_dir = get_cache_dir()

    # Get file information
    file_info = _get_cache_file_info(cache_dir)

    files_deleted = 0
    bytes_freed = 0

    logger.info(f"Purging cache files older than {max_age_days} days from {cache_dir}")

    # Delete files older than max_age_days
    for file_info_item in file_info:
        if file_info_item.age_days > max_age_days:
            try:
                file_info_item.path.unlink()
                files_deleted += 1
                bytes_freed += file_info_item.size
                logger.debug(f"Deleted old cache file: {file_info_item.path}")
            except OSError as e:
                logger.error(f"Failed to delete cache file {file_info_item.path}: {e}")

    logger.info(
        f"Cache cleanup: removed {files_deleted} files ({bytes_freed / 1048576:.2f} MB)"
    )
    return files_deleted, bytes_freed


def clean_all_cache(cache_dir: Optional[Path] = None) -> Tuple[int, int]:
    """
    Remove all files from the cache directory.

    Args:
        cache_dir: Cache directory path (defaults to HOME/.cache/yt-mpv)

    Returns:
        Tuple[int, int]: (number of files deleted, total bytes freed)
    """
    if cache_dir is None:
        cache_dir = get_cache_dir()

    # Get file information
    file_info = _get_cache_file_info(cache_dir)

    files_deleted = 0
    bytes_freed = 0

    logger.info(f"Removing all cache files from {cache_dir}")

    # Delete all files
    for file_info_item in file_info:
        try:
            file_info_item.path.unlink()
            files_deleted += 1
            bytes_freed += file_info_item.size
            logger.debug(f"Deleted cache file: {file_info_item.path}")
        except OSError as e:
            logger.error(f"Failed to delete cache file {file_info_item.path}: {e}")

    logger.info(
        f"Cache cleanup: removed all {files_deleted} files ({bytes_freed / 1048576:.2f} MB)"
    )
    return files_deleted, bytes_freed


def get_cache_info(
    cache_dir: Optional[Path] = None,
) -> Tuple[int, int, List[Tuple[Path, float]]]:
    """
    Get information about the current cache contents.

    Args:
        cache_dir: Cache directory path (defaults to HOME/.cache/yt-mpv)

    Returns:
        Tuple[int, int, List[Tuple[Path, float]]]:
            (number of files, total size in bytes, list of (file, age in days))
    """
    file_info = _get_cache_file_info(cache_dir)

    file_count = len(file_info)
    total_size = sum(item.size for item in file_info)

    # Convert to format expected by the test - exactly (Path, age_days) tuples
    file_details = [(item.path, item.age_days) for item in file_info]

    return file_count, total_size, file_details


def format_cache_info(cache_dir: Optional[Path] = None, max_files: int = 5) -> str:
    """
    Get a formatted string with cache information.

    Args:
        cache_dir: Cache directory path (defaults to HOME/.cache/yt-mpv)
        max_files: Maximum number of files to include in the listing

    Returns:
        str: Formatted cache information
    """
    file_count, total_size, file_details = get_cache_info(cache_dir)

    lines = []
    lines.append("Cache information:")
    lines.append(f"Files: {file_count}")
    lines.append(f"Total size: {total_size / 1048576:.2f} MB")

    if file_count > 0:
        lines.append("\nOldest files:")
        for i, (file_path, age_days) in enumerate(file_details[:max_files]):
            lines.append(f"  {file_path.name} - {age_days:.1f} days old")

        if file_count > max_files:
            lines.append(f"  ... and {file_count - max_files} more files")

    return "\n".join(lines)
