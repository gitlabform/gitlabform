"""Tasks related to documentation generation and serving."""

from dev.common import run_command


def docs_serve():
    """Starts the local documentation development server with live-reloading."""
    run_command(["uv", "run", "mkdocs", "serve", "--livereload"], "Starting MkDocs development server")


def docs_build():
    """Generates the static documentation site."""
    run_command(["uv", "run", "mkdocs", "build"], "Building static documentation site")
