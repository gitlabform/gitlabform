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
from dev.qa import format_code, lint as run_lint_logic, test as run_test_logic
from dev.release import (
    build as run_build_logic,
    docker_build as run_docker_build_logic,
    publish as run_publish_logic,
    docker_verify as run_docker_verify_logic,
    verify as run_verify_logic,
)


def lint():
    """CLI entry point for the 'lint' command that handles optional toggles."""
    parser = argparse.ArgumentParser(prog="lint", description="Run parallel linters or a specific tool")
    parser.add_argument("linter", nargs="?", help="Specific linter to run (e.g., ruff, all)")
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Arguments for the specific linter")
    args = parser.parse_args()
    run_lint_logic(linter_name=args.linter, extra_args=args.extra_args)


def test():
    """CLI entry point for the 'test' command that passes through arguments."""
    # sys.argv[1:] captures everything passed after 'test'
    run_test_logic(sys.argv[1:])


def build():
    """CLI entry point for the 'build' command."""
    parser = argparse.ArgumentParser(prog="build", description="Build source distribution and wheel")
    parser.parse_args()
    run_build_logic()


def verify():
    """CLI entry point for the 'verify' command."""
    parser = argparse.ArgumentParser(prog="verify", description="Verify built artifacts in isolated environment")
    parser.parse_args()
    run_verify_logic()


def publish():
    """CLI entry point for the 'publish' command."""
    parser = argparse.ArgumentParser(prog="publish", description="Publish built artifacts to PyPI")
    parser.parse_args()
    run_publish_logic()


def docker_build():
    """CLI entry point for the 'docker-build' command."""
    parser = argparse.ArgumentParser(prog="docker-build", description="Build the GitLabForm Docker image")
    parser.add_argument("--image", default="localhost/gitlabform", help="Image name (default: localhost/gitlabform)")
    parser.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    parser.add_argument("--push", action="store_true", help="Push the image after building")
    args = parser.parse_args()
    run_docker_build_logic(image=args.image, tag=args.tag, push=args.push)


def docker_verify():
    """CLI entry point for the 'docker-verify' command."""
    parser = argparse.ArgumentParser(prog="docker-verify", description="Verify the GitLabForm Docker image")
    parser.add_argument("--image", default="localhost/gitlabform", help="Image name (default: localhost/gitlabform)")
    parser.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    args = parser.parse_args()
    run_docker_verify_logic(image=args.image, tag=args.tag)


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
    subparsers.add_parser("clean", help="Remove environment, cache, and build artifacts")

    # Add the lint command with optional linter argument and extra args
    lint_parser = subparsers.add_parser("lint", help="Run parallel linters or a specific tool")
    lint_parser.add_argument("linter", nargs="?", help="Linter name (ruff, codespell, bandit, etc.) or 'all'")
    lint_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for the linter")

    # Add the test command with passthrough arguments
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

    # Docker build command
    docker_parser = subparsers.add_parser("docker-build", help="Build the GitLabForm Docker image")
    docker_parser.add_argument(
        "--image", default="localhost/gitlabform", help="Image name (default: localhost/gitlabform)"
    )
    docker_parser.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    docker_parser.add_argument("--push", action="store_true", help="Push the image after building")

    # Docker verify command
    verify_docker_parser = subparsers.add_parser("docker-verify", help="Verify the GitLabForm Docker image")
    verify_docker_parser.add_argument(
        "--image", default="localhost/gitlabform", help="Image name (default: localhost/gitlabform)"
    )
    verify_docker_parser.add_argument("--tag", default="latest", help="Image tag (default: latest)")

    args = parser.parse_args()

    # Mapping command strings to the functional logic
    dispatch = {
        "setup": setup,
        "format": format_code,
        "docs-serve": docs_serve,
        "docs-build": docs_build,
        "build": run_build_logic,
        "verify": run_verify_logic,
        "publish": run_publish_logic,
        "clean": clean,
    }

    if args.command in dispatch:
        dispatch[args.command]()
    elif args.command == "lint":
        run_lint_logic(linter_name=args.linter, extra_args=args.extra_args)
    elif args.command == "test":
        run_test_logic(args.extra_args)
    elif args.command == "docker-build":
        run_docker_build_logic(image=args.image, tag=args.tag, push=args.push)
    elif args.command == "docker-verify":
        run_docker_verify_logic(image=args.image, tag=args.tag)
    elif args.command == "gitlab-local":
        if args.subcommand == "up":
            gitlab_up(version=args.version, flavor=args.flavor)
        elif args.subcommand == "down":
            gitlab_down()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
