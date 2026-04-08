"""Tasks related to building distributions and verifying package integrity."""

import subprocess
import sys
import tempfile
from pathlib import Path
from dev.common import REPO_ROOT, logger, run_command


def build():
    """Builds the source distribution and wheel using the configured build backend."""
    run_command(["uv", "build"], "Building package distributions")


def verify():
    """Performs rigorous verification of the built artifacts in an isolated environment."""
    logger.info("[bold blue]==>[/bold blue] Verifying built artifacts...")
    dist_path = REPO_ROOT / "dist"

    # 1. Ensure build artifacts exist
    if not dist_path.exists() or not any(dist_path.iterdir()):
        logger.error(f"[bold red]❌ Build directory '{dist_path}/' is missing or empty.[/bold red]")
        logger.info("Hint: Run 'uv run build' first.")
        sys.exit(1)

    wheels = [str(p) for p in dist_path.glob("*.whl")]
    sdists = [str(p) for p in dist_path.glob("*.tar.gz")]

    if not wheels:
        logger.error(f"[bold red]❌ No .whl files found in '{dist_path}/'.[/bold red]")
        sys.exit(1)

    # 2. Check metadata compliance via Twine
    run_command(["uv", "run", "twine", "check"] + wheels + sdists, "Checking metadata via Twine")

    # 3. Audit wheel contents for accidental inclusion of dev files
    run_command(["uv", "run", "check-wheel-contents"] + wheels, "Checking wheel contents")

    # 4. Smoke test the entry point from the wheel in a fresh environment
    # This is the most critical test: ensuring the published package actually works.
    wheel_to_test = wheels[0]
    logger.info("[bold blue]==>[/bold blue] Verifying executable from wheel in an isolated environment...")

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_venv = Path(tmpdir) / "venv"
        logger.info("Creating ephemeral virtual environment for smoke test...")
        subprocess.run(["uv", "venv", str(temp_venv)], check=True)

        python_exe = str(temp_venv / "bin" / "python")
        # Install the built wheel into the temporary environment
        subprocess.run(["uv", "pip", "install", "--python", python_exe, wheel_to_test], check=True)

        # Execute the entry point directly from the ephemeral environment
        gitlabform_exe = str(temp_venv / "bin" / "gitlabform")
        subprocess.run([gitlabform_exe, "--version"], check=True)

    logger.info("[bold green]✅ Verification complete. Artifacts are ready for release.[/bold green]")


def docker_build(image: str = "localhost/gitlabform", tag: str = "latest", push: bool = False):
    """Builds the GitLabForm Docker image."""
    image_name = f"{image}:{tag}"

    run_command(
        ["docker", "build", "--pull", "-t", image_name, str(REPO_ROOT)],
        f"Building Docker image: [bold cyan]{image_name}[/bold cyan]",
    )

    if push:
        run_command(["docker", "push", image_name], f"Pushing Docker image: [bold cyan]{image_name}[/bold cyan]")


def docker_verify(image: str = "localhost/gitlabform", tag: str = "latest"):
    """Verifies the built Docker image with a smoke test."""
    image_name = f"{image}:{tag}"
    run_command(
        ["docker", "run", "--rm", image_name, "gitlabform", "--version"],
        f"Verifying Docker image: [bold cyan]{image_name}[/bold cyan]",
    )
