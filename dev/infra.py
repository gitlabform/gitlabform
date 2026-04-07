"""Orchestration tasks for the local development infrastructure (GitLab)."""

import sys
import time
from pathlib import Path
from dev.common import logger, run_command


def gitlab_up():
    """Starts the local GitLab instance using the legacy setup script."""
    script_path = Path("dev/gitlab/run_gitlab_in_docker.sh")
    if not script_path.exists():
        logger.error(f"[bold red]❌ Could not find setup script:[/bold red] {script_path}")
        logger.info("Ensure GitLab assets are correctly located in 'dev/gitlab/'.")
        sys.exit(1)
    run_command(["bash", str(script_path)], "Executing GitLab setup script")


def gitlab_down():
    """Stops and removes the local GitLab container with a grace period for cleanup."""
    # GitLab can take significant time to stop; we use a 30s timeout before force-killing.
    run_command(["docker", "stop", "--time=30", "gitlab"], "Stopping GitLab container")

    # A small delay ensures the Docker daemon has released volume locks before removal.
    grace_period = 5
    logger.info(f"[bold blue]==>[/bold blue] Waiting {grace_period}s for container termination...")
    time.sleep(grace_period)

    run_command(["docker", "rm", "gitlab"], "Removing GitLab container")
    logger.info("[bold green]✅ GitLab instance stopped and removed.[/bold green]")
