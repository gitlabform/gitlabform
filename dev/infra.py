"""Orchestration tasks for the local development infrastructure (GitLab)."""

import subprocess
import sys
import time
from dev.common import REPO_ROOT, logger, run_command, get_executable, get_clean_env


def _check_docker_running():
    """Ensures the Docker daemon is accessible."""
    try:
        docker_bin = get_executable("docker")
        subprocess.run([docker_bin, "info"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("[bold red]❌ Docker is not running or not installed.[/bold red]")
        logger.info("Please start Docker Desktop or the Docker daemon and try again.")
        sys.exit(1)


def gitlab_up(extra_args: list[str] | None = None):
    """Starts the local GitLab instance using the legacy setup script.

    Args:
        extra_args: Additional arguments passed directly to the setup script.
    """
    _check_docker_running()
    script_path = REPO_ROOT / "dev/gitlab/run_gitlab_in_docker.sh"
    if not script_path.exists():
        logger.error(f"[bold red]❌ Could not find setup script:[/bold red] {script_path}")
        logger.info("Ensure GitLab assets are correctly located in 'dev/gitlab/'.")
        sys.exit(1)

    cmd = ["bash", str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    # We pass a 'clean' environment to the legacy bash script.
    # This ensures that any calls to 'docker' inside the script resolve to the
    # system binary rather than recursing into our own toolkit entrypoint.
    desc = f"Executing GitLab setup script {' '.join(extra_args) if extra_args else ''}".strip()
    run_command(cmd, desc, env=get_clean_env())


def gitlab_down():
    """Stops and removes the local GitLab container with a grace period for cleanup."""
    _check_docker_running()
    docker_bin = get_executable("docker")
    # GitLab can take significant time to stop; we use a 30s timeout before force-killing.
    run_command([docker_bin, "stop", "--time=30", "gitlab"], "Stopping GitLab container")

    # A small delay ensures the Docker daemon has released volume locks before removal.
    grace_period = 5
    logger.info(f"[bold blue]==>[/bold blue] Waiting {grace_period}s for container termination...")
    time.sleep(grace_period)

    run_command([docker_bin, "rm", "gitlab"], "Removing GitLab container")
    logger.info("[bold green]✅ GitLab instance stopped and removed.[/bold green]")
