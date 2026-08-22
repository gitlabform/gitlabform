"""Tasks related to building and verifying Docker images."""

import argparse
from pathlib import Path

from dev.common import REPO_ROOT, logger, run_command, get_executable
from dev.release import publish_docker


def build(extra_args: list[str] | None = None):
    """Builds the GitLabForm Docker image from a prebuilt wheel in dist/.

    The Dockerfile installs the packaged wheel rather than building from the source tree,
    so the local prerequisite is always: `uv run package build` before `uv run docker build`.

    Local development usually builds for the host architecture only (for example, `docker buildx build`
    with no explicit `--platform` override). CI uses the same toolkit commands but passes explicit
    `--platform` values for multi-arch validation; the reusable build workflow validates each target
    architecture without pushing registry credentials. This keeps the CLI surface consistent across
    local development and GitHub Actions while the actual GHCR publication remains in the release
    workflow.

    Args:
        extra_args: Arguments for the docker build command (e.g., --tag, --push, --output).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tag", default="localhost/gitlabform:latest")
    parser.add_argument("--push", action="store_true", help="Automatically push after build")
    parser.add_argument(
        "--output", help="Write the built image to an archive file (for example: type=docker,dest=/tmp/image.tar)"
    )

    parsed, remaining = parser.parse_known_args(extra_args or [])
    # image_name = f"{parsed.tag}"

    # Ensure the Docker build has access to the prebuilt wheel artifact.
    dist_dir = REPO_ROOT / "dist"
    if not dist_dir.exists() or not any(dist_dir.glob("*.whl")):
        logger.error("No Python wheel found in dist/. Run `uv run package build` before building the Docker image.")
        raise SystemExit(1)

    docker_bin = get_executable("docker")
    build_cmd = [docker_bin, "buildx", "build", "--pull", "-t", parsed.tag]
    if parsed.output:
        build_cmd.extend(["--output", parsed.output])
    build_cmd.extend(remaining)
    build_cmd.append(str(REPO_ROOT))

    run_command(build_cmd, f"Building Docker image: [bold cyan]{parsed.tag}[/bold cyan]")

    if parsed.push:
        # Delegate to the release domain to ensure consistent push logic
        publish_docker([f"--tag={parsed.tag}"])


def verify(extra_args: list[str] | None = None):
    """Verifies the built Docker image with a smoke test."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tag", default="localhost/gitlabform:latest")
    parser.add_argument("--input", help="Load a Docker image archive from disk before verifying it")

    parsed, remaining = parser.parse_known_args(extra_args or [])

    docker_bin = get_executable("docker")
    if parsed.input:
        archive = Path(parsed.input).expanduser()
        if not archive.exists():
            logger.error(f"Docker archive not found: {archive}")
            raise SystemExit(1)
        load_cmd = [docker_bin, "load", "--input", str(archive)]
        run_command(load_cmd, f"Loading Docker image archive: [bold cyan]{archive}[/bold cyan]")

    cmd = [docker_bin, "run", "--rm"] + remaining + [parsed.tag, "gitlabform", "--version"]
    run_command(cmd, f"Verifying Docker image: [bold cyan]{parsed.tag}[/bold cyan]")
