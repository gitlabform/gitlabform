"""Tasks related to releasing artifacts (PyPI and Docker)."""

import argparse
import os
import re
import sys
from typing import NoReturn
import requests
from dev.common import logger, run_command, get_executable


def _append_github_output(key: str, value: str):
    """
    Communicates data back to the GitHub Actions runner.

    By writing to the file path defined in the GITHUB_OUTPUT environment variable,
    we make variables available to subsequent steps and jobs in the workflow via
    the 'steps.<id>.outputs' context.
    """
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
    else:
        logger.debug(f"[Local Simulation] GITHUB_OUTPUT: {key}={value}")


def _conclude_validation(is_valid: bool, message: str, severity: str = "notice") -> NoReturn:
    """
    Finalizes the validation process and signals the GitHub runner.

    - Sets 'is_valid' output for conditional job execution.
    - Writes a Markdown summary to the GitHub Job Summary page.
    - Uses workflow commands (::error:: or ::notice::) to highlight status in the UI.
    - Exits with 1 on error to stop the workflow, or 0 to continue (even if skipping).
    """
    icon = "✅" if is_valid else ("❌" if severity == "error" else "⏭️")

    if severity == "error":
        logger.error(f"{icon} {severity.upper()}: {message}")
    else:
        logger.info(f"{icon} {severity.upper()}: {message}")

    # GitHub Workflow Command for UI highlights
    print(f"::{severity}::{message}")

    # Write to Job Summary
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            status = "VALID" if is_valid else "SKIPPED"
            f.write(f"### Release Validation: {status}\n{message}\n")

    _append_github_output("is_valid", "true" if is_valid else "false")
    sys.exit(1 if severity == "error" else 0)


def _get_run_info(run_id: str, repo: str, headers: dict, base_url: str) -> dict:
    """
    Fetches workflow run metadata. Used to verify that a manual release
    is targeting a successful run of the 'Main Workflow'.
    """
    run_url = f"{base_url}/actions/runs/{run_id}"
    response = requests.get(run_url, headers=headers, timeout=15)
    if response.status_code == 404:
        raise ValueError(f"Run ID '{run_id}' not found in repo '{repo}'.")
    response.raise_for_status()

    run_data = response.json()
    if run_data.get("conclusion") != "success":
        raise ValueError(f"Run ID '{run_id}' status is '{run_data.get('conclusion')}'. Must be 'success'.")
    if run_data.get("name") != "Main Workflow":
        raise ValueError(f"Run ID '{run_id}' must belong to 'Main Workflow'.")

    return run_data


def _get_tag_sha(tag_name: str, headers: dict, base_url: str) -> str:
    """
    Resolves a git tag name to its commit SHA. This allows us to verify
    if a tag actually points to the code that was built in a specific run.
    """
    res = requests.get(f"{base_url}/commits/{tag_name}", headers=headers, timeout=15)
    if res.status_code in [404, 422]:
        raise ValueError(f"Tag '{tag_name}' not found.")
    res.raise_for_status()
    return res.json().get("sha")


def _find_tag_for_sha(commit_sha: str, headers: dict, base_url: str) -> str:
    """
    Performs a reverse lookup: finds a version tag (v*) associated with a SHA.
    Iterates through paginated GitHub API results until a match is found.
    """
    page = 1
    while True:
        tags_url = f"{base_url}/tags?per_page=100&page={page}"
        response = requests.get(tags_url, headers=headers, timeout=15)
        response.raise_for_status()
        tags = response.json()
        if not tags:
            break
        for tag in tags:
            if tag.get("commit", {}).get("sha") == commit_sha:
                name = tag.get("name", "")
                if name.startswith("v"):
                    return name
        if len(tags) < 100:
            break
        page += 1
    return ""


def gh_workflow_check(extra_args: list[str] | None = None):
    """
    Validates GitHub Workflow conditions and resolves release metadata.

    This command acts as a gatekeeper for the release pipeline. It verifies that the 
    environment variables provided by GitHub Actions match the expected state for a release.

    LOCAL TESTING:
    1. Manual Trigger:
       GH_TOKEN="your_pat" EVENT="workflow_dispatch" REPO="owner/repo" TAG="v1.0.0" MANUAL_ID="12345" uv run release gh-workflow-check

    2. Automated Trigger:
       GH_TOKEN="your_pat" EVENT="workflow_run" REPO="owner/repo" CONCLUSION="success" \
       SHA="$(git rev-parse HEAD)" AUTO_ID="67890" uv run release gh-workflow-check
    """
    event_name = os.environ.get("EVENT")
    repo = os.environ.get("REPO")
    token = os.environ.get("GH_TOKEN")
    manual_tag = os.environ.get("TAG", "").strip()
    manual_run_id = os.environ.get("MANUAL_ID", "").strip()
    upstream_conclusion = os.environ.get("CONCLUSION")
    commit_sha = os.environ.get("SHA")
    automated_run_id = os.environ.get("AUTO_ID")

    if not event_name or not repo:
        _conclude_validation(False, "Missing EVENT or REPO env vars.", severity="error")

    if not token:
        logger.warning("GH_TOKEN environment variable is not set. API calls to GitHub will likely fail.")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    base_url = f"https://api.github.com/repos/{repo}"

    # Case 1: Manual Trigger (Untrusted Input)
    # We verify that the user-provided Tag and Run ID actually exist via GitHub API
    # and ensure the Tag points to the same SHA as the Workflow Run.
    if event_name == "workflow_dispatch":
        if not manual_tag or not manual_run_id or not re.match(r"^[0-9]+$", manual_run_id):
            _conclude_validation(False, "Manual releases require a tag and numeric Run ID.", severity="error")
        try:
            # Verify the Workflow Run is successful and exists
            run_data = _get_run_info(manual_run_id, repo, headers, base_url)
            run_sha = run_data.get("head_sha")
            # Resolve the tag to a commit SHA
            tag_sha = _get_tag_sha(manual_tag, headers, base_url)

            if tag_sha != run_sha:
                _conclude_validation(False, f"Tag SHA mismatch for Run {manual_run_id}.", severity="error")
        except ValueError as e:
            _conclude_validation(False, str(e), severity="error")
        except requests.exceptions.RequestException as e:
            error_msg = f"GitHub API communication error: {e}"
            if e.response is not None and e.response.status_code == 401:
                error_msg = "Unauthorized (401). Ensure GH_TOKEN is set and valid for the target repository."
            _conclude_validation(False, error_msg, severity="error")
        except Exception as e:
            _conclude_validation(False, f"Unexpected error during release check: {e}", severity="error")

        _append_github_output("version", manual_tag)
        _append_github_output("run_id", manual_run_id)
        _conclude_validation(True, f"Manual validation passed for {manual_tag}.")

    # Case 2: Automated Trigger (Trusted Input)
    # GitHub provides the Run ID and SHA automatically. We verify that a SemVer
    # tag (v*) exists on that SHA to justify proceeding with a release.
    if event_name == "workflow_run":
        if not commit_sha or not automated_run_id:
            _conclude_validation(False, "Missing SHA or AUTO_ID env vars for automated release.", severity="error")

        if upstream_conclusion != "success":
            # We exit 0 here because the trigger might be valid but the upstream failed;
            # we just skip the release without failing the check job itself.
            _conclude_validation(False, f"Upstream was {upstream_conclusion}.", severity="notice")
        try:
            # Automated releases only happen if the commit has a 'v*' tag.
            # This prevents every successful main build from triggering a release.
            tag_name = _find_tag_for_sha(commit_sha, headers, base_url)
            if not tag_name:
                _conclude_validation(False, f"No v-tag for SHA {commit_sha[:8]}.", severity="notice")

            _append_github_output("version", tag_name)
            _append_github_output("run_id", automated_run_id)
            _conclude_validation(True, f"Automated validation passed: {tag_name}")
        except Exception as e:
            msg = f"Resolution error: {e}"
            if (
                isinstance(e, requests.exceptions.RequestException)
                and e.response is not None
                and e.response.status_code == 401
            ):
                msg = "Unauthorized (401). Ensure GH_TOKEN is valid."
            _conclude_validation(False, msg, severity="error")
        return

    _conclude_validation(False, f"Unsupported event: {event_name}", severity="error")


def publish_pypi(extra_args: list[str] | None = None):
    """Publishes the built Python artifacts to PyPI.

    Args:
        extra_args: Additional arguments for uv publish.
    """
    run_command(["uv", "publish"] + (extra_args or []), "Publishing package to PyPI")


def publish_docker(extra_args: list[str] | None = None):
    """Pushes the built Docker image to a registry.

    Args:
        extra_args: Arguments for the docker push command (e.g., --image, --tag).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"
    docker_bin = get_executable("docker")

    run_command([docker_bin, "push", image_name], f"Pushing Docker image: [bold cyan]{image_name}[/bold cyan]")
