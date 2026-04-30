"""Shared utilities and logging configuration for the GitLabForm development toolkit."""

import logging
import os
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


def run_command(command: list[str], description: str, env: dict[str, str] | None = None):
    """Helper to run a system command and exit the process on failure.

    Args:
        command: The list of command arguments to execute.
        description: A human-readable description of the task for logging.
        env: Optional environment variables for the subprocess.
    """
    logger.info(f"[bold blue]==>[/bold blue] {description}...")

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as e:
        logger.error(f"[bold red]❌ Error during:[/bold red] {description}")
        sys.exit(e.returncode)


def delete_path(path: Path):
    """Deletes a file or directory, respecting the global DRY_RUN flag."""
    if not path.exists():
        return

    logger.info(f"[bold blue]==>[/bold blue] Removing {path}...")
    shutil.rmtree(path) if path.is_dir() else path.unlink()


def get_executable(name: str) -> str:
    """Finds the system executable, avoiding shadowing by the toolkit's own scripts."""
    path_env = os.environ.get("PATH", "").split(os.pathsep)

    # Filter out the virtualenv bin directory to avoid calling our own CLI recursively
    if sys.prefix:
        venv_bin = str(Path(sys.prefix) / "bin")
        path_env = [p for p in path_env if p != venv_bin]

    return shutil.which(name, path=os.pathsep.join(path_env)) or name


def get_clean_env() -> dict[str, str]:
    """Returns a copy of the environment with the toolkit's bin directory removed from PATH."""
    new_env = os.environ.copy()
    path_env = new_env.get("PATH", "").split(os.pathsep)
    if sys.prefix:
        venv_bin = str(Path(sys.prefix) / "bin")
        path_env = [p for p in path_env if p != venv_bin]
    new_env["PATH"] = os.pathsep.join(path_env)
    return new_env
