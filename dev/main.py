#!/usr/bin/env python3
import argparse
import subprocess
import sys
import shutil
import time
from pathlib import Path
import tempfile


def run_command(command: list[str], description: str):
    """Helper to run a command and exit on failure.

    Provides a consistent UI prefix for all development tasks.
    """
    print(f"==> {description}...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during: {description}")
        sys.exit(e.returncode)


def setup():
    """Initializes the development environment with all dependencies."""
    # We explicitly sync all groups here to ensure a full environment build.
    # This includes dev, test, and docs groups.
    run_command(["uv", "sync", "--all-groups"], "Synchronizing all dependency groups")

    # prek install writes the actual hook files into .git/hooks/
    # We must include both 'pre-commit' (for Black) and 'commit-msg' (for Commitizen)
    # to ensure the full quality gate is active.
    run_command(["uv", "run", "prek", "install", "--hook-type", "pre-commit"], "Installing pre-commit hooks")
    run_command(["uv", "run", "prek", "install", "--hook-type", "commit-msg"], "Installing commit-msg hooks")

    print("\n✅ Setup complete! You are ready to develop.")


def lint():
    """Runs all linting checks."""
    run_command(["uv", "run", "ruff", "check", "."], "Running Ruff linter (non-enforcing)")
    run_command(["uv", "run", "bandit", "-c", "pyproject.toml", "."], "Running Bandit security linter (non-enforcing)")
    run_command(["uv", "run", "codespell", "."], "Running Codespell typo checker (non-enforcing)")
    run_command(["uv", "run", "mypy", "."], "Running Mypy type checker")
    run_command(["uv", "run", "black", "--check", "."], "Checking formatting with Black")
    print("\n✅ Linting passed.")


def format_code():
    """Automatically formats the code."""
    run_command(["uv", "run", "black", "."], "Formatting code with Black")
    print("\n✅ Code formatted.")


def test():
    """Runs the test suite."""
    run_command(["uv", "run", "pytest"], "Running tests with pytest")


def docs_serve():
    """Starts the local documentation development server."""
    run_command(["uv", "run", "mkdocs", "serve"], "Starting MkDocs development server")


def docs_build():
    """Builds the static documentation site."""
    run_command(["uv", "run", "mkdocs", "build"], "Building static documentation site")


def gitlab_up():
    """Starts the local GitLab instance via the dedicated setup script."""
    script_path = Path("dev/gitlab/run_gitlab_in_docker.sh")
    if not script_path.exists():
        print(f"❌ Could not find {script_path}.")
        print("Please ensure GitLab assets are moved to 'dev/gitlab/'.")
        sys.exit(1)
    run_command(["bash", str(script_path)], "Executing GitLab setup script")


def gitlab_down():
    """Stops and removes the local GitLab container, with a grace period."""
    # Use a longer timeout for stopping, as GitLab can take time to shut down.
    run_command(["docker", "stop", "--time=30", "gitlab"], "Stopping GitLab container")
    print("==> Waiting 5 seconds for container to fully terminate before removal...")
    time.sleep(5)  # Give Docker a moment to clean up after stopping
    run_command(["docker", "rm", "gitlab"], "Removing GitLab container")


def build():
    """Builds the source distribution and wheel."""
    run_command(["uv", "build"], "Building package distributions")


def verify():
    """Validates the built artifacts."""
    print("==> Verifying built artifacts...")
    dist_path = Path("dist")

    # 1. Early exit if dist directory is missing or empty
    if not dist_path.exists() or not any(dist_path.iterdir()):
        print(f"❌ Build output directory '{dist_path}/' is missing or empty.")
        print("Hint: Run 'uv run build' first to create the distribution files.")
        sys.exit(1)

    # 2. Resolve file paths manually (subprocess does not expand globs like '*')
    wheels = [str(p) for p in dist_path.glob("*.whl")]
    sdists = [str(p) for p in dist_path.glob("*.tar.gz")]

    if not wheels:
        print(f"❌ No .whl files found in '{dist_path}/'. Run 'uv run build' first.")
        sys.exit(1)

    # 3. Check metadata via Twine
    run_command(["uv", "run", "twine", "check"] + wheels + sdists, "Checking metadata via Twine")

    # 4. Check for common wheel packaging errors
    run_command(["uv", "run", "check-wheel-contents"] + wheels, "Checking wheel contents")

    # 5. Smoke test: Verify the entry point is executable from the built wheel
    # This ensures that the published artifact will function correctly.
    wheel_to_test = wheels[0]

    print("==> Verifying gitlabform executable from built wheel in an isolated environment...")
    # tempfile.TemporaryDirectory() creates a unique directory in the system TEMP location
    # (e.g. /tmp/...). It is NOT created in the project root and is deleted automatically.
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_venv = Path(tmpdir) / "venv"
        print(f"Creating ephemeral virtual environment for smoke test...")

        # Create venv and install the wheel using the uv binary from the temp venv
        subprocess.run(["uv", "venv", str(temp_venv)], check=True)

        python_exe = str(temp_venv / "bin" / "python")
        # Use 'uv pip install' to install the local wheel into the ephemeral venv
        subprocess.run(["uv", "pip", "install", "--python", python_exe, wheel_to_test], check=True)

        # Execute the entry point directly from the ephemeral venv
        gitlabform_exe = str(temp_venv / "bin" / "gitlabform")
        subprocess.run([gitlabform_exe, "--version"], check=True)

    print("\n✅ Verification complete. Artifacts in 'dist/' are ready for release.")


def clean():
    """Removes the virtual environment and build artifacts."""
    # Clear pre-commit/prek cache
    run_command(["uv", "run", "prek", "clean"], "Cleaning prek/pre-commit cache")

    paths_to_remove = [
        ".venv",
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        "site",
    ]
    for path_str in paths_to_remove:
        path = Path(path_str)
        if path.exists():
            print(f"==> Removing {path}...")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    print("\n✅ Cleanup complete.")


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
