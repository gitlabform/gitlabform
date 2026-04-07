#!/usr/bin/env python3
"""Central entry point and CLI facade for the GitLabForm development toolkit."""

import argparse
from dev.docs import docs_build, docs_serve
from dev.env import clean, setup
from dev.infra import gitlab_down, gitlab_up
from dev.qa import format_code, lint, test
from dev.release import build, verify


def main():
    """Main entry point for direct script execution."""
    parser = argparse.ArgumentParser(description="GitLabForm Development Toolkit")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("setup", help="Initialize development environment and git hooks")
    subparsers.add_parser("lint", help="Run linters and formatting checks")
    subparsers.add_parser("format", help="Automatically format code")
    subparsers.add_parser("test", help="Run the project test suite")
    subparsers.add_parser("gitlab-up", help="Start local GitLab instance via Docker")
    subparsers.add_parser("gitlab-down", help="Stop local GitLab instance")
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
        "test": test,
        "gitlab-up": gitlab_up,
        "gitlab-down": gitlab_down,
        "docs-serve": docs_serve,
        "docs-build": docs_build,
        "build": build,
        "verify": verify,
        "clean": clean,
    }

    if args.command in dispatch:
        dispatch[args.command]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
