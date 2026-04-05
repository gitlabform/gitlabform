import argparse
import subprocess
import sys
import shutil
from pathlib import Path


def run_command(command: list[str], description: str):
    """Helper to run a command and exit on failure."""
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
    print("==> Installing Git hooks via prek...")
    subprocess.run(["uv", "run", "prek", "install", "--hook-type", "pre-commit"], check=True)
    subprocess.run(["uv", "run", "prek", "install", "--hook-type", "commit-msg"], check=True)

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
    parser = argparse.ArgumentParser(description="GitLabForm Development Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("setup", help="Sync dependencies and install git hooks")
    subparsers.add_parser("lint", help="Check code style and types")
    subparsers.add_parser("format", help="Auto-format code")
    subparsers.add_parser("test", help="Run tests")
    subparsers.add_parser("clean", help="Remove environment and cache artifacts")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "setup":
        setup()
    elif args.command == "lint":
        lint()
    elif args.command == "format":
        format_code()
    elif args.command == "test":
        test()
    elif args.command == "clean":
        clean()


if __name__ == "__main__":
    main()
