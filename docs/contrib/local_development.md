# Local Development

Welcome to the GitLabForm development guide. We use **`uv`** and a unified development toolkit to manage our lifecycle, ensuring a fast, deterministic, and reproducible environment for all contributors.

## Required tools

Following tools are used in this project. Please make sure you have them installed:

- **`uv`**: The primary tool for dependency management and running development tasks. It automatically manages the required Python version and virtual environment. [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/).
- **Docker**: Required for running local GitLab instances and for building container images. [Install Docker](https://docs.docker.com/get-docker/).
- **`jq`**: A command-line JSON processor used for orchestrating local GitLab instances. [Install `jq`](https://jqlang.github.io/jq/download/).

## Typical development workflow

The project provides a comprehensive CLI (**the development toolkit**) organized into task domains. You can discover the available domains by running the main entry point:

```bash
uv run dev --help
```

### Command Shortcuts

While `dev` is the central entry point, each domain is also registered as a direct shortcut in your environment. You can omit the `dev` prefix from any command for a more concise experience. For example, these two commands are identical:

* Full: `uv run dev workspace setup`
* Shortcut: `uv run workspace setup`

Each domain (like qa, docs, or workspace) provides its own help context. If you are ever unsure of the available sub-commands or arguments, simply run the domain name or add the `--help` flag:

```bash
uv run workspace            # Shows help for workspace setup and cleanup
uv run workspace --help     # Same as above
uv run docker build --help  # Shows help and available flags for Docker builds
```

A standard lifecycle for implementing a new feature or bug fix typically involves:

1. **New branch**: Create a new branch for your changes.
2. **Setup**: Initialize or update your local workspace using uv run workspace setup. This also installs the Git hooks. See Workspace Management section for more details. See [Workspace management](#workspace-management) section for more details.
3. **Develop**: Implement your logic or fix in the codebase.
4. **Quality**: Format and lint your code via the qa domain. See [Code quality](#code-quality) section for more details.
5. **Test**: Be sure to include/update tests for your changes. See [Testing](#testing) section for more details.
6. **Validate**: Perform a final check on the build artifacts. See [Building & Verification](#building-verification) section for more details.
7. **Commit**: Record your changes using the **Conventional Commits** standard. The Git hooks installed during setup will automatically validate your commit messages.

    !!! tip "Guided experience via Commitizen"

        You can use `uv run cz commit` that will present an interactive option in the terminal for selecting and commiting your changes.

8. **Documentation**: Add/update documentation if necessary for the change being introduced. See [Documentation](#documentation) section for more details.
9. **Open/Update PR**: Push your changes to GitHub and create/update a pull request.


## Workspace Management

Managing your development environment is handled by the workspace domain. We use `uv` to provide a consistent, isolated, and reproducible environment where everything is contained within an automatically managed `.venv`.

```bash
uv run workspace setup
```

This command performs several automated tasks:

1. **Python Management**: Automatically downloads and installs the specific Python version required by the project.
2. **Virtual Environment**: Creates a `.venv` directory in the project root. You do not need to manually create or activate this environment. `uv run` handles the activation context for you.
3. **Dependency Synchronization**: Installs all required runtime and development dependencies, ensuring your environment exactly matches the `uv.lock` file.
4. **Git Hook Installation**: Configures Git hooks to enforce linting, formatting, and Conventional Commit standards.

To reset your workspace and remove all build artifacts, caches, and the virtual environment:

```bash
uv run workspace clean
```

## Code Quality

Maintaining high code quality is essential for the stability and readability of the project. We use a suite of tools for automatic formatting and static analysis.

### Formatting

We use **black** to enforce a consistent code style across the entire repository. This ensures that the codebase remains readable and reduces friction during code reviews.

```bash
uv run qa format
```

### Linting

We use several tools (including `mypy` for type checking and `bandit` for security auditing) to catch potential issues before they are committed. By default, the `lint` command runs all configured checks in parallel.

```bash
uv run qa lint
```

You can also run a specific tool or pass additional arguments directly to the underlying linter. For example, to run only mypy with specific flags:

```bash
uv run qa lint mypy .
```

To see the list of available linting tools and help:

```bash
uv run qa lint --help
```

## Testing

We use **pytest** as the underlying engine for our entire test suite. The toolkit's `test` command acts as a passthrough, meaning any valid `pytest` argument or flag can be provided directly.

To discover all available testing options for the `qa` domain:

```bash
uv run qa test --help
```

**Common examples:**

- Run tests matching a keyword: `uv run qa test -k "archive"`
- Run tests with verbose output: `uv run qa test -v`
- Run with coverage reporting: `uv run qa test --cov=.`
- Run a specific test file/suite: `uv run qa test tests/<path-to-test-file>`
- Run a specific test within a test file/suite: `uv run qa test tests/<path-to-test-file>::<test-class>::<test-method>`

### Unit Tests

Unit tests are fast, isolated, and do not require a running GitLab instance. They are ideal for validating logic and configuration parsing:

```bash
uv run qa test tests/unit
```

### Acceptance Tests

Acceptance tests perform real operations against a running GitLab instance. Because they interact with an actual API, they are slower and require more setup than unit tests.

1. Start Local GitLab

    We recommend running tests against a disposable GitLab instance in Docker to ensure your environment matches our CI/CD pipelines:

    ```bash
    uv run gitlab-local up # Starts Enterprise Edition (EE) by default
    uv run gitlab-local down # Cleanup: Stops and removes the local GitLab container
    ```

    !!! note
    
        Use `uv run gitlab-local up --gitlab-flavor ce` to test against Community Edition.

    To see all available infrastructure management options:

    ```bash
    uv run gitlab-local up --help
    ```
    
    !!! tip "Testing against specific versions"
        You can test against specific GitLab releases using the version flag: `uv run gitlab-local up --gitlab-version 17.5.0-ee`.

    !!! note "Testing paid features"
    
        To test features requiring a GitLab instance with **Premium** or **Ultimate** tier, you'll need to have a license from GitLab that can be used for enabling those features in your local GitLab instance.
        
        Once you've obtained your license, you can set the `GITLAB_EE_LICENSE` environment variable or place your license in a file named `Gitlab.gitlab-license` in the project root. Our dev toolkit will automatically detect and apply this license during the setup. This file is also included in `.gitignore` so that it's not committed to the repository.


2. Run the tests

    Once the GitLab instance is healthy and accessible, execute the acceptance located in `tests/acceptance/` directory. See the examples above on how to run the tests.

    !!! tip

        Acceptance tests are usually slower than unit tests since they run against a real GitLab instance. This involves creating, updating, and deleting resources in GitLab. You may find it helpful to run only select tests instead of entire test suite. For example: run all tests related to the feature you're working on.


### Using a Remote GitLab Instance

It's not recommended, but if you prefer to run tests against non-local/disposable GitLab instance, provide the credentials via environment variables:

```bash
export GITLAB_URL="https://mygitlab.company.com"
export GITLAB_TOKEN="<admin_api_token>"
uv run qa test tests/acceptance
```

## Building & Verification

This section covers creating the distributable artifacts for the project, including the Python package and the Docker image.

### Python Distributions

We generate standard Python distribution artifacts (source distribution and wheels) that can be uploaded to PyPI. To generate the artifacts in the `dist/` directory:

```bash
uv run package build
```

To see available build options:

```bash
uv run package build --help
```

The `package verify` command performs an audit of the built files to ensure they are ready for release. This includes metadata validation via `twine`, content auditing via `check-wheel-contents`, and an automated smoke test that installs the wheel in a temporary isolated environment to check the entry point.

```bash
uv run package verify
```


### Docker Images

The Docker image is the recommended way to run GitLabForm in CI/CD environments. To build the image locally using our multi-stage `Dockerfile`:

```bash
uv run docker build
```

You can customize the image name and tag via arguments:

```bash
uv run docker build --image my-registry/gitlabform --tag dev
```

To see all Docker build options:

```bash
uv run docker build --help
```

To ensure the newly built image is functional, run a smoke test that executes the application version check inside a container:

```bash
uv run docker verify
```

To see options for Docker verification:

```bash
uv run docker verify --help
```

## Documentation

We use **MkDocs** with the **Material** theme to generate our project documentation. The toolkit provides commands via the `docs` domain to preview changes locally and build the final static site.

To serve the documentation with live-reloading (ideal for seeing your changes in real-time as you edit the markdown files):

```bash
uv run docs serve
```

The site will be available at `http://localhost:8000`.

To generate the static documentation site in the `site/` directory (used for deployment to GitHub Pages):

```bash
uv run docs build
```

To see all documentation management options:

```bash
uv run docs --help
```
