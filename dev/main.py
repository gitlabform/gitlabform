#!/usr/bin/env -S uv run
"""Central entry point and CLI facade for the GitLabForm development toolkit."""

import argparse
import os
import sys
from pathlib import Path

# Add the project root to sys.path to allow running this script directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dev.docs import docs_build, docs_serve
from dev.env import clean, setup
from dev.infra import gitlab_down, gitlab_up
from dev.qa import format_code, lint, test as run_test_logic
from dev.release import build, verify


def test():
    """CLI entry point for the 'test' command that passes through arguments."""
    # sys.argv[1:] captures everything passed after 'test'
    run_test_logic(sys.argv[1:])


def gitlab_local():
    """Unified CLI for managing the local GitLab environment."""
    parser = argparse.ArgumentParser(prog="gitlab-local", description="Manage local GitLab test environment")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    up = subparsers.add_parser("up", help="Start the local GitLab instance")
    up.add_argument("--version", default="latest", help="GitLab version tag (default: latest)")
    up.add_argument("--flavor", default="ee", choices=["ee", "ce"], help="GitLab flavor (default: ee)")

    subparsers.add_parser("down", help="Stop and remove the local GitLab container")

    args = parser.parse_args()
    if args.subcommand == "up":
        gitlab_up(version=args.version, flavor=args.flavor)
    elif args.subcommand == "down":
        gitlab_down()


def main():
    """Main entry point for direct script execution."""
    parser = argparse.ArgumentParser(description="GitLabForm Development Toolkit")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("setup", help="Initialize development environment and git hooks")
    subparsers.add_parser("lint", help="Run linters and formatting checks")
    subparsers.add_parser("format", help="Automatically format code")
    test_parser = subparsers.add_parser("test", help="Run the project test suite")
    test_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Arguments to pass to pytest")

    # Add the unified gitlab command to the main parser
    gitlab_parser = subparsers.add_parser("gitlab-local", help="Manage local GitLab Docker instance")
    gitlab_subparsers = gitlab_parser.add_subparsers(dest="subcommand", required=True)
    up = gitlab_subparsers.add_parser("up")
    up.add_argument("--version", default="latest")
    up.add_argument("--flavor", default="ee", choices=["ee", "ce"])
    gitlab_subparsers.add_parser("down")

    subparsers.add_parser("docs-serve", help="Serve documentation with live-reload")
    subparsers.add_parser("docs-build", help="Build static documentation site")
    subparsers.add_parser("build", help="Build source distribution and wheel")
    subparsers.add_parser("verify", help="Verify built artifacts in isolated environment")
    subparsers.add_parser("clean", help="Remove environment, cache, and build artifacts")

    args = parser.parse_args()

    # Mapping command strings to the functional logic
    dispatch = {
        "setup": setup,
        "lint": lint,
        "format": format_code,
        "docs-serve": docs_serve,
        "docs-build": docs_build,
        "build": build,
        "verify": verify,
        "clean": clean,
    }

    if args.command in dispatch:
        dispatch[args.command]()
    elif args.command == "test":
        run_test_logic(args.extra_args)
    elif args.command == "gitlab-local":
        if args.subcommand == "up":
            gitlab_up(version=args.version, flavor=args.flavor)
        elif args.subcommand == "down":
            gitlab_down()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
