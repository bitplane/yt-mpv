"""
Cache management functions for yt-mpv
"""

import logging
import time
from pathlib import Path

from yt_mpv.utils.config import DL_DIR

# Configure logging
logger = logging.getLogger("yt-mpv")


def remove(video_file: Path, info_file: Path) -> bool:
    """
    Remove video and info files after successful upload.

    Args:
        video_file: Path to the video file
        info_file: Path to the info JSON file

    Returns:
        bool: True if removal was successful
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


def clear() -> tuple[int, int]:
    """
    Clear all files from the cache directory.

    Returns:
        tuple[int, int]: (number of files deleted, total bytes freed)
    """
    cache_dir = DL_DIR

    # Get a list of files (not directories)
    files = [f for f in cache_dir.iterdir() if f.is_file()]

    files_deleted = 0
    bytes_freed = 0

    # Remove each file
    for file_path in files:
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            files_deleted += 1
            bytes_freed += file_size
            logger.debug(f"Removed cache file: {file_path}")
        except OSError as e:
            logger.error(f"Failed to remove file {file_path}: {e}")

    logger.info(
        f"Cleared {files_deleted} files ({bytes_freed / 1048576:.2f} MB) from cache"
    )
    return files_deleted, bytes_freed


def stats() -> tuple[int, int, list[tuple[Path, float]]]:
    """
    Get statistics about the current cache contents.

    Returns:
        tuple[int, int, list[tuple[Path, float]]]:
            (number of files, total size in bytes, list of (file, age in days))
    """
    cache_dir = DL_DIR
    now = time.time()

    files_info = []
    total_size = 0

    # Get all files in cache directory
    for file_path in cache_dir.iterdir():
        if file_path.is_file():
            try:
                stat = file_path.stat()
                size = stat.st_size
                mtime = stat.st_mtime
                age_days = (now - mtime) / (24 * 60 * 60)

                files_info.append((file_path, age_days))
                total_size += size
            except OSError:
                # Skip files with access issues
                pass

    # Sort by age (oldest first)
    files_info.sort(key=lambda x: x[1], reverse=True)

    return len(files_info), total_size, files_info


def summary(max_files: int = 5) -> str:
    """
    Get a formatted summary of cache information.

    Args:
        max_files: Maximum number of files to include in the listing

    Returns:
        str: Formatted cache information
    """
    file_count, total_size, file_details = stats()

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
