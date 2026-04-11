#!/usr/bin/env -S uv run
"""Central entry point and CLI facade for the GitLabForm development toolkit."""

import argparse
import os
import sys
from pathlib import Path

# Add the project root to sys.path to allow running this script directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dev.docs import docs_build, docs_serve
from dev.env import clean as run_clean_logic, setup as run_setup_logic
from dev.infra import gitlab_down, gitlab_up
from dev.qa import format_code, lint as run_qa_logic, test as run_test_logic
from dev.release import (
    build as run_build_logic,
    docker_build as run_docker_build_logic,
    publish as run_publish_logic,
    docker_verify as run_docker_verify_logic,
    verify as run_verify_logic,
)

# --- Constant Descriptions for Unification ---

DESC_WORKSPACE = "Workspace and lifecycle management. Utilities for initializing, updating, and resetting the local development environment."
DESC_QA = "Quality Assurance suite. Provides access to code formatting (Black), parallelized linting, and the pytest-driven test suite."
DESC_DOCS = "Documentation management. Utilities for building the static documentation site and running the local development server with live-reloading."
DESC_PACKAGE = "Python packaging and distribution. Manage the packaging lifecycle: build artifacts, verify integrity, and publish to PyPI."
DESC_DOCKER = "Docker image management. Build and verify the production-ready GitLabForm Docker images."
DESC_INFRA = "Local infrastructure orchestration. Manage a disposable GitLab instance in Docker for acceptance testing and feature validation."

# --- Domain Helpers ---


def _add_workspace_subcommands(subparsers):
    """Configures environment management commands."""
    subparsers.add_parser(
        "setup",
        help="Initialize the environment and install Git hooks",
        description="Initialize the development workspace. This synchronizes all dependency groups via 'uv' and installs Git hooks to enforce QA standards.",
    )
    subparsers.add_parser(
        "clean",
        help="Remove build artifacts and development caches",
        description="Clear the virtual environment, build/distribution directories, and various tool-specific caches.",
    )


def _dispatch_workspace(args):
    """Executes environment logic."""
    if args.command == "setup":
        run_setup_logic()
    elif args.command == "clean":
        run_clean_logic()


def _add_docs_subcommands(subparsers):
    """Configures documentation management commands."""
    serve = subparsers.add_parser(
        "serve",
        help="Start the documentation server with live-reload",
        description="Start the MkDocs live-reload server. Provides an interactive preview of the documentation at http://localhost:8000.",
    )
    serve.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for mkdocs serve")

    build_p = subparsers.add_parser(
        "build",
        help="Generate the static documentation site",
        description="Compile the markdown documentation into a static HTML site ready for deployment.",
    )
    build_p.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for mkdocs build")


def _dispatch_docs(args):
    """Executes documentation logic."""
    if args.command == "serve":
        docs_serve(args.extra_args)
    elif args.command == "build":
        docs_build(args.extra_args)


def _add_package_subcommands(subparsers):
    """Configures Python package distribution commands."""
    b = subparsers.add_parser(
        "build",
        help="Generate source distribution and wheel",
        description="Generate distribution artifacts. Creates a source distribution and a PEP 427 wheel in the 'dist/' directory.",
    )
    b.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for uv build")

    v = subparsers.add_parser(
        "verify",
        help="Audit build artifacts and run smoke tests",
        description="Perform a comprehensive pre-release audit. Validates package metadata, audits wheel contents, and runs a functional smoke test.",
    )
    v.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for verification tools")

    p = subparsers.add_parser(
        "publish",
        help="Upload built artifacts to PyPI",
        description="Upload built artifacts to PyPI. Ensures that only verified distributions are released to the public index.",
    )
    p.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for uv publish")


def _dispatch_package(args):
    """Executes packaging logic."""
    if args.command == "build":
        run_build_logic(args.extra_args)
    elif args.command == "verify":
        run_verify_logic(args.extra_args)
    elif args.command == "publish":
        run_publish_logic(args.extra_args)


def _add_docker_subcommands(subparsers):
    """Configures Docker image management commands."""
    b = subparsers.add_parser("build", help="Build the production Docker image", description=DESC_DOCKER)
    b.add_argument("--image", default="localhost/gitlabform", help="Image name (default: localhost/gitlabform)")
    b.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    b.add_argument("--push", action="store_true", help="Push the image to the registry")
    b.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for docker build")

    v = subparsers.add_parser("verify", help="Validate the image with a smoke test", description=DESC_DOCKER)
    v.add_argument("--image", default="localhost/gitlabform", help="Image name (default: localhost/gitlabform)")
    v.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    v.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for docker run")


def _dispatch_docker(args):
    """Executes Docker logic."""
    # Reconstruct arguments to maintain compatibility with the backend parser
    # and ensure that help/defaults defined in the CLI are respected.
    extra_args = ["--image", args.image, "--tag", args.tag]
    if args.command == "build" and args.push:
        extra_args.append("--push")

    # Append any remaining raw arguments passed via REMAINDER
    if args.extra_args:
        extra_args.extend(args.extra_args)

    if args.command == "build":
        run_docker_build_logic(extra_args=extra_args)
    elif args.command == "verify":
        run_docker_verify_logic(extra_args=extra_args)


def _add_infra_subcommands(subparsers):
    """Configures infrastructure orchestration commands."""
    up = subparsers.add_parser(
        "up",
        help="Start a local GitLab Docker instance",
        description="Start a local GitLab instance in Docker. Allows specifying the edition (EE/CE) and version tag for targeted testing.",
    )
    up.add_argument("--version", default="latest", help="GitLab version tag (default: latest)")
    up.add_argument("--flavor", default="ee", choices=["ee", "ce"], help="GitLab flavor (default: ee)")

    subparsers.add_parser(
        "down",
        help="Stop and remove the GitLab instance",
        description="Gracefully stop and remove the local GitLab infrastructure container.",
    )


def _dispatch_infra(args):
    """Executes infrastructure logic."""
    if args.command == "up":
        gitlab_up(version=args.version, flavor=args.flavor)
    elif args.command == "down":
        gitlab_down()


def _add_qa_subcommands(subparsers_action):
    """Configures the 'lint', 'format', and 'test' commands under a subparser."""
    # QA -> Lint
    lint_parser = subparsers_action.add_parser(
        "lint",
        help="Execute parallel linters or a specific tool",
        description="Execute static analysis. Runs parallelized checks (Ruff, Mypy, etc.) or a specific tool with custom arguments.",
    )
    lint_parser.add_argument("linter", nargs="?", help="Linter name (ruff, codespell, bandit, etc.) or 'all'")
    lint_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for the linter")

    # QA -> Format
    format_parser = subparsers_action.add_parser(
        "format",
        help="Auto-format code using Black",
        description="Auto-format Python source code using Black to maintain consistent project styling.",
    )
    format_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments for Black")

    # QA -> Test
    test_parser = subparsers_action.add_parser(
        "test",
        help="Run the pytest suite",
        description="Run the pytest suite. Supports full argument passthrough for filtering tests, generating coverage reports, or debugging.",
    )
    test_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Arguments to pass directly to pytest")


def _dispatch_qa(args):
    """Executes the appropriate QA logic based on the parsed command."""
    if args.command == "lint":
        run_qa_logic(linter_name=args.linter, extra_args=args.extra_args)
    elif args.command == "format":
        format_code(args.extra_args)
    elif args.command == "test":
        run_test_logic(args.extra_args)


# --- Domain Shortcut Entry Points ---


def _domain_entrypoint(prog, description, setup_fn, dispatch_fn):
    """Generic helper for domain-specific entry points."""
    parser = argparse.ArgumentParser(prog=prog, description=description)
    setup_fn(parser.add_subparsers(dest="command"))
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch_fn(args)


def workspace():
    """Shortcut for 'uv run workspace'."""
    _domain_entrypoint("workspace", DESC_WORKSPACE, _add_workspace_subcommands, _dispatch_workspace)


def qa():
    """Shortcut for 'uv run qa'."""
    _domain_entrypoint("qa", DESC_QA, _add_qa_subcommands, _dispatch_qa)


def docs():
    """Shortcut for 'uv run docs'."""
    _domain_entrypoint("docs", DESC_DOCS, _add_docs_subcommands, _dispatch_docs)


def package():
    """Shortcut for 'uv run package'."""
    _domain_entrypoint("package", DESC_PACKAGE, _add_package_subcommands, _dispatch_package)


def docker():
    """Shortcut for 'uv run docker'."""
    _domain_entrypoint("docker", DESC_DOCKER, _add_docker_subcommands, _dispatch_docker)


def gitlab_local():
    """Shortcut for 'uv run gitlab-local'. Provides orchestration for the local GitLab instance."""
    _domain_entrypoint("gitlab-local", DESC_INFRA, _add_infra_subcommands, _dispatch_infra)


def main():
    """Main entry point for direct script execution."""
    parser = argparse.ArgumentParser(description="GitLabForm Development Toolkit")
    subparsers = parser.add_subparsers(dest="domain", help="Task domains")

    # Register Domains
    domains = {
        "workspace": (
            "Workspace and lifecycle management",
            DESC_WORKSPACE,
            _add_workspace_subcommands,
            _dispatch_workspace,
        ),
        "qa": ("Quality Assurance (linting, formatting, testing)", DESC_QA, _add_qa_subcommands, _dispatch_qa),
        "docs": ("Documentation management", DESC_DOCS, _add_docs_subcommands, _dispatch_docs),
        "package": ("Python packaging and distribution", DESC_PACKAGE, _add_package_subcommands, _dispatch_package),
        "docker": ("Docker image management", DESC_DOCKER, _add_docker_subcommands, _dispatch_docker),
        "gitlab-local": ("Local infrastructure orchestration", DESC_INFRA, _add_infra_subcommands, _dispatch_infra),
    }

    parsers = {}
    for name, (help_text, description, setup_fn, _) in domains.items():
        p = subparsers.add_parser(name, help=help_text, description=description)
        setup_fn(p.add_subparsers(dest="command"))
        parsers[name] = p

    args = parser.parse_args()

    if not args.domain:
        parser.print_help()
        sys.exit(0)

    if args.domain in domains:
        if not args.command:
            parsers[args.domain].print_help()
            sys.exit(0)
        domains[args.domain][3](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
