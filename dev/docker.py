"""Tasks related to building and verifying Docker images."""

import argparse
from pathlib import Path

from dev.common import REPO_ROOT, logger, run_command, get_executable
from dev.release import publish_docker


def build(extra_args: list[str] | None = None):
    """Builds the GitLabForm Docker image from a prebuilt wheel in dist/.

    Args:
        extra_args: Arguments for the docker build command (e.g., --image, --tag, --push, --output).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")
    parser.add_argument("--push", action="store_true", help="Automatically push after build")
    parser.add_argument(
        "--output", help="Write the built image to an archive file (for example: type=docker,dest=/tmp/image.tar)"
    )

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"

    # Ensure the Docker build has access to the prebuilt wheel artifact.
    dist_dir = REPO_ROOT / "dist"
    if not dist_dir.exists() or not any(dist_dir.glob("*.whl")):
        logger.error("No Python wheel found in dist/. Run `uv run package build` before building the Docker image.")
        raise SystemExit(1)

    docker_bin = get_executable("docker")
    build_cmd = [docker_bin, "buildx", "build", "--pull", "-t", image_name]
    if parsed.output:
        build_cmd.extend(["--output", parsed.output])
    build_cmd.extend(remaining)
    build_cmd.append(str(REPO_ROOT))

    run_command(build_cmd, f"Building Docker image: [bold cyan]{image_name}[/bold cyan]")

    if parsed.push:
        # Delegate to the release domain to ensure consistent push logic
        publish_docker([f"--image={parsed.image}", f"--tag={parsed.tag}"])


def verify(extra_args: list[str] | None = None):
    """Verifies the built Docker image with a smoke test."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")
    parser.add_argument("--input", help="Load a Docker image archive from disk before verifying it")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"

    docker_bin = get_executable("docker")
    if parsed.input:
        archive = Path(parsed.input).expanduser()
        if not archive.exists():
            logger.error(f"Docker archive not found: {archive}")
            raise SystemExit(1)
        load_cmd = [docker_bin, "load", "--input", str(archive)]
        run_command(load_cmd, f"Loading Docker image archive: [bold cyan]{archive}[/bold cyan]")

    cmd = [docker_bin, "run", "--rm"] + remaining + [image_name, "gitlabform", "--version"]
    run_command(cmd, f"Verifying Docker image: [bold cyan]{image_name}[/bold cyan]")
