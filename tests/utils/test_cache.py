"""
Tests for the yt-mpv cache module.
"""

import os
import time

import pytest

from yt_mpv.utils.cache import (
    clear,
    remove,
    stats,
    summary,
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


def test_remove(tmp_path):
    """Test remove removes the specified files."""
    # Create test files
    video_file = tmp_path / "test_video.mp4"
    info_file = tmp_path / "test_info.json"

    video_file.write_text("video content")
    info_file.write_text("info content")

    # Ensure files exist
    assert video_file.exists()
    assert info_file.exists()

    # Clean up files
    result = remove(video_file, info_file)

    # Check result
    assert result is True
    assert not video_file.exists()
    assert not info_file.exists()


def test_remove_missing(tmp_path):
    """Test remove handles missing files gracefully."""
    # Create paths but don't create the files
    video_file = tmp_path / "nonexistent_video.mp4"
    info_file = tmp_path / "nonexistent_info.json"

    # Clean up non-existent files
    result = remove(video_file, info_file)

    # Should still return True since nothing failed
    assert result is True


def test_stats(temp_cache_dir, monkeypatch):
    """Test stats returns correct information."""
    # Mock DL_DIR to use our temp directory
    monkeypatch.setattr("yt_mpv.utils.cache.DL_DIR", temp_cache_dir)
    file_count, total_size, file_details = stats()

    # Verify results
    assert file_count == 5
    assert total_size > 0
    assert len(file_details) == 5

    # Files should be sorted by age (oldest first)
    ages = [age for _, age in file_details]
    assert ages == sorted(ages, reverse=True)


def test_clear(temp_cache_dir, monkeypatch):
    """Test clear removes all files."""
    # Mock DL_DIR to use our temp directory
    monkeypatch.setattr("yt_mpv.utils.cache.DL_DIR", temp_cache_dir)

    # Verify initial state
    files_before = list(temp_cache_dir.iterdir())
    assert len(files_before) == 5

    # Calculate expected total size
    total_size = sum(f.stat().st_size for f in files_before)
    assert total_size > 0

    # Remove all files
    files_deleted, bytes_freed = clear()

    # Check results
    assert files_deleted == 5
    assert bytes_freed == total_size

    # Verify all files are gone
    files_after = list(temp_cache_dir.iterdir())
    assert len(files_after) == 0


def test_summary(temp_cache_dir, monkeypatch):
    """Test summary returns properly formatted info."""
    # Mock DL_DIR to use our temp directory
    monkeypatch.setattr("yt_mpv.utils.cache.DL_DIR", temp_cache_dir)

    # Get formatted info
    formatted_info = summary(max_files=3)

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
