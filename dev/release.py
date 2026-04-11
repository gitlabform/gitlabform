"""Tasks related to building distributions and verifying package integrity."""

import subprocess
import argparse
import sys
import tempfile
from pathlib import Path
from dev.common import REPO_ROOT, logger, run_command, get_executable


def build(extra_args: list[str] | None = None):
    """Builds the source distribution and wheel using the configured build backend.

    Args:
        extra_args: Additional arguments for uv build.
    """
    run_command(["uv", "build"] + (extra_args or []), "Building package distributions")


def publish(extra_args: list[str] | None = None):
    """Publishes the built artifacts to PyPI.

    Args:
        extra_args: Additional arguments for uv publish.
    """
    run_command(["uv", "publish"] + (extra_args or []), "Publishing package to PyPI")


def verify(extra_args: list[str] | None = None):
    """Performs rigorous verification of the built artifacts in an isolated environment.

    Args:
        extra_args: Additional arguments for verification tools (e.g. twine check).
    """
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
    run_command(["uv", "run", "twine", "check"] + wheels + sdists + (extra_args or []), "Checking metadata via Twine")

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


def docker_build(extra_args: list[str] | None = None):
    """Builds the GitLabForm Docker image, parsing image/tag/push from extra_args.

    Args:
        extra_args: All arguments passed to the docker build command.
    """
    # Internal parser to handle defaults for local development
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")
    parser.add_argument("--push", action="store_true")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"

    # Construct the docker build command with passthrough for any other docker flags
    docker_bin = get_executable("docker")
    cmd = [docker_bin, "build", "--pull", "-t", image_name] + remaining + [str(REPO_ROOT)]

    run_command(
        cmd,
        f"Building Docker image: [bold cyan]{image_name}[/bold cyan]",
    )

    if parsed.push:
        docker_bin = get_executable("docker")
        run_command([docker_bin, "push", image_name], f"Pushing Docker image: [bold cyan]{image_name}[/bold cyan]")


def docker_verify(extra_args: list[str] | None = None):
    """Verifies the built Docker image with a smoke test, parsing image/tag from extra_args.

    Args:
        extra_args: All arguments passed to the docker verify command.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"

    # Construct the docker run command
    docker_bin = get_executable("docker")
    cmd = [docker_bin, "run", "--rm"] + remaining + [image_name, "gitlabform", "--version"]
    run_command(
        cmd,
        f"Verifying Docker image: [bold cyan]{image_name}[/bold cyan]",
    )
