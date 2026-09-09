"""Tasks related to documentation generation and serving."""

from dev.common import run_command


def docs_serve(extra_args: list[str] | None = None):
    """Starts the local documentation development server with live-reloading.

    Args:
        extra_args: Additional arguments for zensical serve.
    """
    cmd = ["uv", "run", "zensical", "serve"] + (extra_args or [])
    run_command(cmd, "Starting Zensical development server")


def docs_build(extra_args: list[str] | None = None):
    """Generates the static documentation site.

    Args:
        extra_args: Additional arguments for zensical build.
    """
    cmd = ["uv", "run", "zensical", "build", "--clean", "--strict"] + (extra_args or [])
    run_command(cmd, "Building static documentation site")
