"""Shared utilities and logging configuration for the GitLabForm development toolkit."""

import logging
import subprocess
import sys
import shutil
from pathlib import Path
from rich.logging import RichHandler

# Single source of truth for the repository root
REPO_ROOT = Path(__file__).resolve().parent.parent

# Configure logging once for the entire toolkit to ensure consistent UI across modules.
# markup=True enables the use of Rich style tags like [bold blue] in log messages.
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(markup=True, rich_tracebacks=True, show_path=False, show_time=False)],
)
logger = logging.getLogger("gitlabform.dev")


def run_command(command: list[str], description: str):
    """Helper to run a system command and exit the process on failure.

    Args:
        command: The list of command arguments to execute.
        description: A human-readable description of the task for logging.
    """
    logger.info(f"[bold blue]==>[/bold blue] {description}...")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[bold red]❌ Error during:[/bold red] {description}")
        sys.exit(e.returncode)


def delete_path(path: Path):
    """Deletes a file or directory, respecting the global DRY_RUN flag."""
    if not path.exists():
        return

    logger.info(f"[bold blue]==>[/bold blue] Removing {path}...")
    shutil.rmtree(path) if path.is_dir() else path.unlink()
