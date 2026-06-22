"""Tasks related to building and verifying Docker images."""

import argparse
from dev.common import REPO_ROOT, logger, run_command, get_executable
from dev.release import publish_docker


def build(extra_args: list[str] | None = None):
    """Builds the GitLabForm Docker image.

    Args:
        extra_args: Arguments for the docker build command (e.g., --image, --tag, --push).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")
    parser.add_argument("--push", action="store_true", help="Automatically push after build")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"

    # TODO: Add a check here if the Dockerfile is ever updated to require
    # pre-built wheels from the 'dist/' directory.

    docker_bin = get_executable("docker")
    # Note: REPO_ROOT is the context, so the Dockerfile can access dist/ if needed.
    build_cmd = [docker_bin, "build", "--pull", "-t", image_name] + remaining + [str(REPO_ROOT)]

    run_command(build_cmd, f"Building Docker image: [bold cyan]{image_name}[/bold cyan]")

    if parsed.push:
        # Delegate to the release domain to ensure consistent push logic
        publish_docker([f"--image={parsed.image}", f"--tag={parsed.tag}"])


def verify(extra_args: list[str] | None = None):
    """Verifies the built Docker image with a smoke test."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"

    docker_bin = get_executable("docker")
    cmd = [docker_bin, "run", "--rm"] + remaining + [image_name, "gitlabform", "--version"]
    run_command(cmd, f"Verifying Docker image: [bold cyan]{image_name}[/bold cyan]")
