"""Tasks related to environment initialization and cleanup."""

import shutil
from pathlib import Path
from dev.common import logger, run_command


def setup():
    """Initializes the development environment with all dependencies and git hooks."""
    # We explicitly sync all groups to ensure a full environment build (dev, test, docs).
    run_command(["uv", "sync", "--all-groups"], "Synchronizing all dependency groups")

    # prek install writes the actual hook files into .git/hooks/
    run_command(["uv", "run", "prek", "install", "--hook-type", "pre-commit"], "Installing pre-commit hooks")
    run_command(["uv", "run", "prek", "install", "--hook-type", "commit-msg"], "Installing commit-msg hooks")

    logger.info("[bold green]✅ Setup complete! You are ready to develop.[/bold green]")


def clean():
    """Removes the virtual environment, build artifacts, and development caches."""
    # Clear pre-commit/prek cache managed by prek
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
            logger.info(f"[bold blue]==>[/bold blue] Removing {path}...")
            shutil.rmtree(path) if path.is_dir() else path.unlink()
    logger.info("[bold green]✅ Cleanup complete.[/bold green]")
