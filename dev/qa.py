"""Quality Assurance tasks including linting, formatting, and testing."""

import sys
from concurrent.futures import ThreadPoolExecutor
from dev.common import logger, run_command


def lint(linter_name: str | None = None, extra_args: list[str] | None = None):
    """Runs the suite of static analysis and formatting checks.

    Args:
        linter_name: Specific linter to run (e.g., 'ruff', 'mypy', 'all').
                     If None, runs default project linters.
        extra_args: Additional arguments to pass to the linter.
    """

    # Mapping of toolkit-supported linters to their standard project commands.
    # Defaults include target paths ('.') and project-specific flags.
    SUPPORTED_LINTERS = {
        "bandit": (["uv", "run", "bandit", "-c", "pyproject.toml", "."], "Bandit security linter"),
        "black": (["uv", "run", "black", "--check", "."], "Black formatting check"),
        "codespell": (["uv", "run", "codespell", "."], "Codespell typo checker"),
        "mypy": (["uv", "run", "mypy", "."], "Mypy type checker"),
        "ruff": (["uv", "run", "ruff", "check", "."], "Ruff linter"),
    }

    if linter_name == "all":
        tasks = list(SUPPORTED_LINTERS.values())
    elif not linter_name:
        # Default Project Gate: Run Black and Mypy in parallel
        tasks = [SUPPORTED_LINTERS["black"], SUPPORTED_LINTERS["mypy"]]
    elif linter_name in SUPPORTED_LINTERS:
        cmd, desc = SUPPORTED_LINTERS[linter_name]
        if extra_args:
            # If user provides specific paths/args, we remove the default '.' and append their input
            cmd = cmd[:-1] + extra_args if cmd[-1] == "." else cmd + extra_args
        run_command(cmd, desc)
        return
    else:
        logger.error(f"[bold red]❌ Unsupported linter:[/bold red] {linter_name}")
        logger.info(f"Available: {', '.join(SUPPORTED_LINTERS.keys())} or 'all'")
        sys.exit(1)

    logger.info(f"[bold blue]==>[/bold blue] Starting parallel linting suite ({len(tasks)} tasks)...")

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_command, cmd, desc) for cmd, desc in tasks]
        for future in futures:
            try:
                future.result()
            except Exception:
                pass  # Individual failures are logged by run_command within the thread

    logger.info("[bold green]✅ Linting passed.[/bold green]")


def format_code(extra_args: list[str] | None = None):
    """Automatically formats the codebase using Black.

    Args:
        extra_args: Additional arguments to pass to black (e.g., --check, --diff).
    """
    cmd = ["uv", "run", "black", "."] + (extra_args or [])
    run_command(cmd, "Formatting code with Black")
    logger.info("[bold green]✅ Code formatted.[/bold green]")


def test(extra_args: list[str] | None = None):
    """Runs the project test suite using pytest.

    Args:
        extra_args: Additional arguments to pass directly to pytest (e.g., file paths, filters).
    """
    command = ["uv", "run", "pytest"]
    if extra_args:
        command.extend(extra_args)
    run_command(command, "Running tests with pytest")
