"""Orchestration tasks for the local development infrastructure (GitLab)."""

import subprocess
import sys
import time
from dev.common import REPO_ROOT, logger, run_command


def _check_docker_running():
    """Ensures the Docker daemon is accessible."""
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("[bold red]❌ Docker is not running or not installed.[/bold red]")
        logger.info("Please start Docker Desktop or the Docker daemon and try again.")
        sys.exit(1)


def gitlab_up(version: str = "latest", flavor: str = "ee"):
    """Starts the local GitLab instance using the legacy setup script.

    Args:
        version: The GitLab Docker image tag (e.g., 'latest', '16.5.0-ee.0').
        flavor: The GitLab edition ('ee' or 'ce').
    """
    _check_docker_running()
    script_path = REPO_ROOT / "dev/gitlab/run_gitlab_in_docker.sh"
    if not script_path.exists():
        logger.error(f"[bold red]❌ Could not find setup script:[/bold red] {script_path}")
        logger.info("Ensure GitLab assets are correctly located in 'dev/gitlab/'.")
        sys.exit(1)

    cmd = ["bash", str(script_path), "--gitlab-version", version, "--gitlab-flavor", flavor]
    run_command(cmd, f"Executing GitLab setup script (Flavor: {flavor}, Version: {version})")


def gitlab_down():
    """Stops and removes the local GitLab container with a grace period for cleanup."""
    _check_docker_running()
    # GitLab can take significant time to stop; we use a 30s timeout before force-killing.
    run_command(["docker", "stop", "--time=30", "gitlab"], "Stopping GitLab container")

    # A small delay ensures the Docker daemon has released volume locks before removal.
    grace_period = 5
    logger.info(f"[bold blue]==>[/bold blue] Waiting {grace_period}s for container termination...")
    time.sleep(grace_period)

    run_command(["docker", "rm", "gitlab"], "Removing GitLab container")
    logger.info("[bold green]✅ GitLab instance stopped and removed.[/bold green]")
