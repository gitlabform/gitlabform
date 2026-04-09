# Local Development

Welcome to the GitLabForm development guide. We use **uv** and a unified development toolkit to manage our lifecycle, ensuring a fast, deterministic, and reproducible environment for all contributors.

## Required tools

Following tools are used in this project. Please make sure you have them installed:

- **uv**: The primary tool for dependency management and running development tasks. It automatically manages the required Python version and virtual environment. [Install uv](https://docs.astral.sh/uv/getting-started/installation/).
- **Docker**: Required for running local GitLab instances and for building container images. [Install Docker](https://docs.docker.com/get-docker/).
- **jq**: A command-line JSON processor used for orchestrating local GitLab instances. [Install jq](https://jqlang.github.io/jq/download/).

## Typical development workflow

The project provides a comprehensive CLI (the **development toolkit**) to manage the entire development lifecycle. You can discover all available commands and their specific options by running:

```bash
uv run dev --help
```

A standard lifecycle for implementing a new feature or bug fix typically involves:

1. **Setup**: Initialize or update your local environment using `uv run setup`. This also installs the Git hooks. See [Environment setup](#environment-setup) section for more details.
2. **Develop**: Implement your logic or fix in the codebase.
3. **Quality**: Format and lint your code. See [Code quality](#code-quality) section for more details.
4. **Test**: Be sure to include/update tests for your changes. See [Testing](#testing) section for more details.
5. **Validate**: Perform a final check on the build artifacts. See [Building & Verification](#building-verification) section for more details.
6. **Commit**: Record your changes using the **Conventional Commits** standard. The Git hooks installed during setup will automatically validate your commit messages.
    - *Tip*: You can use `uv run cz commit` for a guided experience.
7. **Documentation**: Add/update documentation if necessary for the change being introduced. See [Documentation](#documentation) section for more details.

## Environment setup

Initializing your development environment is a single-step process. We use **uv** to provide a consistent, isolated, and reproducible workspace. Everything is contained within a virtual environment (`.venv`) that is automatically managed by the toolchain.

```bash
uv run setup
```

This command performs several automated tasks:

1. **Python Management**: Automatically downloads and installs the specific Python version required by the project.
2. **Virtual Environment**: Creates a `.venv` directory in the project root. You do not need to manually create or activate this environment. `uv run` handles the activation context for you.
3. **Dependency Synchronization**: Installs all required runtime and development dependencies, ensuring your environment exactly matches the `uv.lock` file.
4. **Git Hook Installation**: Configures Git hooks to enforce linting, formatting, and Conventional Commit standards.

To reset your environment and remove all build artifacts, caches, and the virtual environment:

```bash
uv run clean
```

## Code Quality

Maintaining high code quality is essential for the stability and readability of the project. We use a suite of tools for automatic formatting and static analysis.

### Formatting

We use black to enforce a consistent code style across the entire repository. This ensures that the codebase remains readable and reduces friction during code reviews.

```bash
uv run format
```

### Linting

We use several tools (including `mypy` for type checking and `bandit` for security auditing) to catch potential issues before they are committed. By default, the `lint` command runs all configured checks in parallel.

```bash
uv run lint
```

You can also run a specific tool or pass additional arguments directly to the underlying linter. For example, to run only mypy with specific flags:

```bash
uv run lint mypy .
```

To see the list of available linting tools and help:

```bash
uv run lint --help
```

## Testing

We use **pytest** as the underlying engine for our entire test suite. The toolkit's `test` command acts as a passthrough, meaning any valid `pytest` argument or flag can be provided directly.

To discover all available testing options:
```bash
uv run test --help
```

**Common examples:**
- Run tests matching a keyword: `uv run test -k "archive"`
- Run tests with verbose output: `uv run test -v`
- Run with coverage reporting: `uv run test --cov=.`
- Run a specific test file/suite: `uv run test tests/<path-to-test-file>`
- Run a specific test within a test file/suite: `uv run test tests/<path-to-test-file>::<test-class>::<test-method>`

### Unit Tests

Unit tests are fast, isolated, and do not require a running GitLab instance. They are ideal for validating logic and configuration parsing:

```bash
uv run test tests/unit
```

### Acceptance Tests

Acceptance tests perform real operations against a running GitLab instance. Because they interact with an actual API, they are slower and require more setup than unit tests.

#### 1. Start Local GitLab

We recommend running tests against a disposable GitLab instance in Docker to ensure your environment matches our CI/CD pipelines:

```bash
uv run gitlab-local up # Starts Enterprise Edition (EE) by default
```

*Note: Use `uv run gitlab-local up --flavor ce` to test against Community Edition.*

To see all available infrastructure management options:

```bash
uv run gitlab-local --help
```

#### 2. Run the Suite

Once the GitLab instance is healthy and accessible, execute the acceptance suite:

```bash
uv run test tests/acceptance
```

To run a specific test class or method:

```bash
uv run test tests/acceptance -k "TestArchiveProject"
```

#### 3. Paid Features

To test features requiring a Premium or Ultimate license, set the `GITLAB_EE_LICENSE` environment variable or place your license in a file named `Gitlab.gitlab-license` in the project root. Our infrastructure scripts will automatically detect and apply this license during the setup.

### Using a Remote GitLab Instance

If you prefer to run tests against your own instance, provide the credentials via environment variables:

```bash
export GITLAB_URL="https://mygitlab.company.com"
export GITLAB_TOKEN="<admin_api_token>"
uv run test tests/acceptance
```

## Building & Verification

This section covers creating the distributable artifacts for the project, including the Python package and the Docker image.

### Python Distributions

We generate standard Python distribution artifacts (source distribution and wheels) that can be uploaded to PyPI. To generate the artifacts in the `dist/` directory:

```bash
uv run build
```

To see available build options:

```bash
uv run build --help
```

The `verify` command performs a rigorous audit of the built files to ensure they are ready for release. This includes metadata validation via **Twine**, content auditing via **check-wheel-contents**, and an automated smoke test that installs the wheel in an isolated environment to check the entry point.

```bash
uv run verify
```

To see the verification steps:

```bash
uv run verify --help
```

### Docker Images

The Docker image is the recommended way to run GitLabForm in CI/CD environments. To build the image locally using our multi-stage `Dockerfile`:

```bash
uv run docker-build
```

You can customize the image name and tag via arguments:

```bash
uv run docker-build --image my-registry/gitlabform --tag dev
```

To see all Docker build options:

```bash
uv run docker-build --help
```

To ensure the newly built image is functional, run a smoke test that executes the application version check inside a container:

```bash
uv run docker-verify
```

To see options for Docker verification:

```bash
uv run docker-verify --help
```

## Documentation

We use **MkDocs** with the **Material** theme to generate our project documentation. The toolkit provides commands to preview changes locally and build the final static site.

To serve the documentation with live-reloading. This is ideal for seeing your changes in real-time as you edit the markdown files:

```bash
uv run docs-serve
```

The site will be available at http://localhost:8000.

To generate the static documentation site in the `site/` directory (used for deployment to GitHub Pages):

```bash
uv run docs-build
```
