"""
Tests for the yt-mpv cache module.
"""

import os
import time

import pytest

from yt_mpv.cache import (
    clean_all_cache,
    cleanup_cache_files,
    format_cache_info,
    get_cache_info,
    purge_cache,
)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory with some test files."""
    # Create test files with different ages
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create 5 files with different modification times
    for i in range(5):
        test_file = cache_dir / f"test_file_{i}.mp4"
        test_file.write_text(f"test content {i}")
        # Set mtime to be i days ago
        mtime = time.time() - (i * 24 * 60 * 60)
        os.utime(test_file, (mtime, mtime))

    return cache_dir


def test_cleanup_cache_files(tmp_path):
    """Test cleanup_cache_files removes the specified files."""
    # Create test files
    video_file = tmp_path / "test_video.mp4"
    info_file = tmp_path / "test_info.json"

    video_file.write_text("video content")
    info_file.write_text("info content")

    # Ensure files exist
    assert video_file.exists()
    assert info_file.exists()

    # Clean up files
    result = cleanup_cache_files(video_file, info_file)

    # Check result
    assert result is True
    assert not video_file.exists()
    assert not info_file.exists()


def test_cleanup_cache_files_missing(tmp_path):
    """Test cleanup_cache_files handles missing files gracefully."""
    # Create paths but don't create the files
    video_file = tmp_path / "nonexistent_video.mp4"
    info_file = tmp_path / "nonexistent_info.json"

    # Clean up non-existent files
    result = cleanup_cache_files(video_file, info_file)

    # Should still return True since nothing failed
    assert result is True


def test_get_cache_info(temp_cache_dir):
    """Test get_cache_info returns correct information."""
    # Pass the temp directory directly instead of mocking Path.home
    file_count, total_size, file_details = get_cache_info(cache_dir=temp_cache_dir)

    # Verify results
    assert file_count == 5
    assert total_size > 0
    assert len(file_details) == 5

    # Files should be sorted by age (oldest first)
    ages = [age for _, age in file_details]
    assert ages == sorted(ages, reverse=True)


def test_purge_cache(temp_cache_dir):
    """Test purge_cache removes files older than specified age."""
    # Files 0, 1 are newer than 2 days
    # Files 2, 3, 4 are older than 2 days
    files_before = list(temp_cache_dir.iterdir())
    assert len(files_before) == 5

    # Make a copy of file stats to verify later
    file_stats = {}
    for file in files_before:
        mtime = file.stat().st_mtime
        age_days = (time.time() - mtime) / (24 * 60 * 60)
        file_stats[file.name] = age_days

    # Purge files older than 2 days
    files_deleted, bytes_freed = purge_cache(cache_dir=temp_cache_dir, max_age_days=2)

    # Check results
    expected_deleted = sum(1 for age in file_stats.values() if age > 2)
    assert files_deleted == expected_deleted
    assert bytes_freed > 0

    files_after = list(temp_cache_dir.iterdir())
    expected_remaining = sum(1 for age in file_stats.values() if age <= 2)
    assert len(files_after) == expected_remaining


def test_clean_all_cache(temp_cache_dir):
    """Test clean_all_cache removes all files."""
    # Verify initial state
    files_before = list(temp_cache_dir.iterdir())
    assert len(files_before) == 5

    # Calculate expected total size
    total_size = sum(f.stat().st_size for f in files_before)
    assert total_size > 0

    # Remove all files
    files_deleted, bytes_freed = clean_all_cache(cache_dir=temp_cache_dir)

    # Check results
    assert files_deleted == 5
    assert bytes_freed == total_size

    # Verify all files are gone
    files_after = list(temp_cache_dir.iterdir())
    assert len(files_after) == 0


def test_format_cache_info(temp_cache_dir):
    """Test format_cache_info returns properly formatted info."""
    # Get formatted info
    formatted_info = format_cache_info(cache_dir=temp_cache_dir, max_files=3)

    # Check output format
    assert "Cache information:" in formatted_info
    assert "Files: 5" in formatted_info
    assert "Total size:" in formatted_info
    assert "MB" in formatted_info
    assert "Oldest files:" in formatted_info

    # Should show 3 files as specified by max_files
    assert "test_file_" in formatted_info
    assert "days old" in formatted_info

    # Should mention 2 more files
    assert "... and 2 more files" in formatted_info
