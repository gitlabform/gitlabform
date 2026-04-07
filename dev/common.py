"""Shared utilities and logging configuration for the GitLabForm development toolkit."""

import logging
import subprocess
import sys
from rich.logging import RichHandler

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
