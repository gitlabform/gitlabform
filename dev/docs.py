"""Tasks related to documentation generation and serving."""

from dev.common import run_command


def docs_serve(extra_args: list[str] | None = None):
    """Starts the local documentation development server with live-reloading.

    Args:
        extra_args: Additional arguments for mkdocs serve.
    """
    cmd = ["uv", "run", "mkdocs", "serve", "--livereload"] + (extra_args or [])
    run_command(cmd, "Starting MkDocs development server")


def docs_build(extra_args: list[str] | None = None):
    """Generates the static documentation site.

    Args:
        extra_args: Additional arguments for mkdocs build.
    """
    cmd = ["uv", "run", "mkdocs", "build"] + (extra_args or [])
    run_command(cmd, "Building static documentation site")
