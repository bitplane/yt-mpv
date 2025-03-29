"""
Tests for the command-line argument parsing.
"""

from yt_mpv.cli.args import create_parser, parse_args


def test_create_parser():
    """Test that the argument parser is created correctly."""
    parser = create_parser()

    # Check that the parser has the expected commands
    subparsers_actions = [
        action for action in parser._actions if action.dest == "command"
    ]
    assert len(subparsers_actions) == 1

    # Get the choices from the subparser
    choices = subparsers_actions[0].choices.keys()

    # Check that all the expected commands are present
    expected_commands = {
        "install",
        "remove",
        "setup",
        "launch",
        "play",
        "archive",
        "check",
        "cache",
    }

    assert set(choices) == expected_commands


def test_parse_args_install():
    """Test parsing install command arguments."""
    args = parse_args(["install"])
    assert args.command == "install"
    assert args.prefix is None


def test_parse_args_play():
    """Test parsing play command arguments."""
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    args = parse_args(["play", test_url])

    assert args.command == "play"
    assert args.url == test_url
    assert args.update_ytdlp is False
    assert args.mpv_args is None


def test_parse_args_play_with_options():
    """Test parsing play command with additional options."""
    args = parse_args(
        [
            "play",
            "https://example.com",
            "--update-ytdlp",
            "--mpv-args",
            "--fullscreen --volume=50",
        ]
    )

    assert args.command == "play"
    assert args.update_ytdlp is True
