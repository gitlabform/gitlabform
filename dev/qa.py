"""Quality Assurance tasks including linting, formatting, and testing."""

from dev.common import logger, run_command


def lint():
    """Runs the full suite of static analysis and formatting checks."""
    run_command(["uv", "run", "ruff", "check", "."], "Running Ruff linter (non-enforcing)")
    run_command(["uv", "run", "bandit", "-c", "pyproject.toml", "."], "Running Bandit security linter (non-enforcing)")
    run_command(["uv", "run", "codespell", "."], "Running Codespell typo checker (non-enforcing)")
    run_command(["uv", "run", "mypy", "."], "Running Mypy type checker")
    run_command(["uv", "run", "black", "--check", "."], "Checking formatting with Black")
    logger.info("[bold green]✅ Linting passed.[/bold green]")


def format_code():
    """Automatically formats the codebase using Black."""
    run_command(["uv", "run", "black", "."], "Formatting code with Black")
    logger.info("[bold green]✅ Code formatted.[/bold green]")


def test():
    """Runs the project test suite using pytest."""
    # Note: Acceptance tests may require a local GitLab instance (run gitlab-up first)
    run_command(["uv", "run", "pytest"], "Running tests with pytest")
