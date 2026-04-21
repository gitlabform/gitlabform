# Setup uv Local

This internal composite action centrally manages the installation of `uv` and configures the environment variables required for the project's toolchain.

## Purpose

Instead of repeating installation scripts and version pinning in every workflow file, this action provides a single source of truth for:
- The pinned `uv` version (currently `0.11.7`).
- Option to set the Python version used in CI job.
- Cross-platform installation logic (handling both Unix and Windows runners).

## Inputs

| Name | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `python-version` | The Python version to use (e.g., `3.12`, `3.14`). | `3.14` | No |

## Environment Variables Set

This action exports the following variables to the `$GITHUB_ENV`, making them available to all subsequent steps in the job:
- `UV_PYTHON`: The version of Python `uv` should use for toolchain management.
- `UV_VERSION`: The pinned version of `uv` installed.

## Usage

To use this action in a workflow, reference it by its local path:

```yaml
jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      
      - name: Configure uv environment
        uses: ./.github/actions/setup-uv-local
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: uv sync
```
