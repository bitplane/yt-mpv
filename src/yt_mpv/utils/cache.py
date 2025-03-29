"""
Cache management functions for yt-mpv
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

from yt_mpv.utils.config import DL_DIR

# Configure logging
logger = logging.getLogger("yt-mpv")


def cleanup_cache_files(video_file: Path, info_file: Path) -> bool:
    """
    Remove downloaded video and info files after successful upload.

    Args:
        video_file: Path to the video file
        info_file: Path to the info JSON file

    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    success = True

    # Remove video file
    if video_file.exists():
        try:
            video_file.unlink()
            logger.info(f"Removed cache file: {video_file}")
        except OSError as e:
            logger.error(f"Failed to remove video file {video_file}: {e}")
            success = False

    # Remove info file
    if info_file.exists():
        try:
            info_file.unlink()
            logger.info(f"Removed cache file: {info_file}")
        except OSError as e:
            logger.error(f"Failed to remove info file {info_file}: {e}")
            success = False

    return success


def get_cache_dir() -> Path:
    """
    Get the default cache directory path.

    Returns:
        Path: The default cache directory path
    """
    return DL_DIR


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

    # Handle both Path objects and string paths
    if isinstance(cache_dir, str):
        cache_dir = Path(cache_dir)

    if not cache_dir.exists() or not cache_dir.is_dir():
        logger.warning(f"Cache directory does not exist: {cache_dir}")
        return 0, 0

    now = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    files_deleted = 0
    bytes_freed = 0

    logger.info(f"Purging cache files older than {max_age_days} days from {cache_dir}")

    for item in cache_dir.iterdir():
        if not item.is_file():
            continue

        file_age = now - item.stat().st_mtime

        if file_age > max_age_seconds:
            try:
                file_size = item.stat().st_size
                item.unlink()
                files_deleted += 1
                bytes_freed += file_size
                logger.debug(f"Deleted old cache file: {item}")
            except OSError as e:
                logger.error(f"Failed to delete cache file {item}: {e}")

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

    # Handle both Path objects and string paths
    if isinstance(cache_dir, str):
        cache_dir = Path(cache_dir)

    if not cache_dir.exists() or not cache_dir.is_dir():
        logger.warning(f"Cache directory does not exist: {cache_dir}")
        return 0, 0

    files_deleted = 0
    bytes_freed = 0

    logger.info(f"Removing all cache files from {cache_dir}")

    for item in cache_dir.iterdir():
        if item.is_file():
            try:
                file_size = item.stat().st_size
                item.unlink()
                files_deleted += 1
                bytes_freed += file_size
                logger.debug(f"Deleted cache file: {item}")
            except OSError as e:
                logger.error(f"Failed to delete cache file {item}: {e}")

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
    if cache_dir is None:
        cache_dir = get_cache_dir()

    # Handle both Path objects and string paths
    if isinstance(cache_dir, str):
        cache_dir = Path(cache_dir)

    if not cache_dir.exists() or not cache_dir.is_dir():
        return 0, 0, []

    now = time.time()
    file_count = 0
    total_size = 0
    file_details = []

    for item in cache_dir.iterdir():
        if item.is_file():
            file_count += 1
            size = item.stat().st_size
            total_size += size
            age_days = (now - item.stat().st_mtime) / (24 * 60 * 60)
            file_details.append((item, age_days))

    # Sort by age (oldest first)
    file_details.sort(key=lambda x: x[1], reverse=True)

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
            if i >= max_files:
                break
            lines.append(f"  {file_path.name} - {age_days:.1f} days old")

        if file_count > max_files:
            lines.append(f"  ... and {file_count - max_files} more files")

    return "\n".join(lines)
