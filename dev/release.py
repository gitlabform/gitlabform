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


def _conclude_validation(
    message: str,
    severity: str,
    release_type: str,
) -> NoReturn:
    """
    Finalizes the validation process and signals the GitHub runner.

    - Emits a release-type classification ('versioned' or 'unversioned').
    - Writes a Markdown summary to the GitHub Job Summary page.
    - Uses workflow commands (::error:: or ::notice::) to highlight status in the UI.
    - Exits with 1 on error to stop the workflow, or 0 to continue (even if skipping).
    """
    if severity == "error":
        status, icon, color, gh_severity = "FAILED", "❌", "red", "error"
    elif release_type == "versioned":
        status, icon, color, gh_severity = "VERSIONED", "✅", "green", "notice"
    elif release_type == "unversioned":
        status, icon, color, gh_severity = "UNVERSIONED", "✅", "green", "notice"
    else:
        status, icon, color, gh_severity = "UNKNOWN", "⚠️", "orange", "warning"

    # 1. Terminal Narrative
    logger.info("─" * 80)
    logger.info(f"{icon} [bold {color}]RELEASE {status}:[/bold {color}] {message}")
    logger.info("─" * 80)

    # 2. GitHub UI Highlights (Annotations)
    print(f"::{gh_severity} title=Release Check::{message}")

    # 3. GitHub Job Summary (Markdown)
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(f"## {icon} Release Eligibility: {status}\n\n")
            f.write(f"> {message}\n")

    _append_github_output("release_type", release_type)
    sys.exit(1 if severity == "error" else 0)


def _get_run_info(run_id: str, repo: str, headers: dict, base_url: str, upstream_name: str) -> dict:
    """
    Fetches workflow run metadata. Used to verify that a manual release
    is targeting a successful run of the 'Main branch' workflow.
    """
    run_url = f"{base_url}/actions/runs/{run_id}"
    logger.info(
        f"Retrieving upstream workflow '[bold cyan]{upstream_name}[/bold cyan]' run metadata for run ID: [bold cyan]{run_id}[/bold cyan]"
    )
    response = requests.get(run_url, headers=headers, timeout=15)
    if response.status_code == 404:
        raise ValueError(f"Run ID '{run_id}' not found in repo '{repo}'.")
    response.raise_for_status()

    run_data = response.json()
    conclusion = run_data.get("conclusion")
    actual_name = run_data.get("name")
    head_sha = run_data.get("head_sha", "unknown")
    logger.info(
        f"Run [bold cyan]{run_id}[/bold cyan] found: workflow='{actual_name}', status='{conclusion}', sha='{head_sha[:8]}'"
    )

    if conclusion != "success":
        raise ValueError(f"Run ID '{run_id}' status is '{conclusion}'. Must be 'success'.")
    if actual_name != upstream_name:
        raise ValueError(f"Run ID '{run_id}' belongs to workflow '{actual_name}' but must belong to '{upstream_name}'.")
    return run_data


def _get_tag_sha(tag_name: str, headers: dict, base_url: str) -> str:
    """
    Resolves a git tag name to its commit SHA. This allows us to verify
    if a tag actually points to the code that was built in a specific run.
    """
    logger.info(f"Resolving tag [bold cyan]{tag_name}[/bold cyan] to a commit SHA...")
    res = requests.get(f"{base_url}/commits/{tag_name}", headers=headers, timeout=15)
    if res.status_code in [404, 422]:
        raise ValueError(f"Tag '{tag_name}' not found.")
    res.raise_for_status()
    sha = res.json().get("sha")
    logger.info(f"Tag [bold cyan]{tag_name}[/bold cyan] resolves to SHA: [bold cyan]{sha[:8]}[/bold cyan]")
    return sha


def _find_tag_for_sha(commit_sha: str, headers: dict, base_url: str) -> str:
    """
    Performs a reverse lookup: finds a version tag (v*) associated with a SHA.
    Iterates through paginated GitHub API results until a match is found.
    """
    logger.info(f"Scanning repository tags for a version matching SHA [bold cyan]{commit_sha[:8]}[/bold cyan]...")
    page = 1
    while True:
        logger.info(f"Retrieving repository tags (page {page})...")
        tags_url = f"{base_url}/tags?per_page=100&page={page}"
        response = requests.get(tags_url, headers=headers, timeout=15)
        response.raise_for_status()
        tags = response.json()
        if not tags:
            logger.info("End of tag list reached.")
            break
        for tag in tags:
            if tag.get("commit", {}).get("sha") == commit_sha:
                name = tag.get("name", "")
                if name.startswith("v"):
                    logger.info(f"Match found: [bold green]{name}[/bold green]")
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
       GH_TOKEN="your_pat" EVENT="workflow_dispatch" REPO="owner/repo" MANUAL_RELEASE_TAG="v1.0.0" MANUAL_UPSTREAM_RUN_ID="12345" uv run glf-dev release gh-workflow-check

    2. Automated Trigger:
       GH_TOKEN="your_pat" EVENT="workflow_run" REPO="owner/repo" CONCLUSION="success" \
       SHA="$(git rev-parse HEAD)" AUTOMATED_UPSTREAM_RUN_ID="67890" uv run glf-dev release gh-workflow-check
    """
    event_name = os.environ.get("EVENT")
    repo = os.environ.get("REPO")
    token = os.environ.get("GH_TOKEN")
    manual_tag = os.environ.get("MANUAL_RELEASE_TAG", "").strip()
    manual_run_id = os.environ.get("MANUAL_UPSTREAM_RUN_ID", "").strip()
    upstream_conclusion = os.environ.get("CONCLUSION")
    commit_sha = os.environ.get("SHA")
    automated_run_id = os.environ.get("AUTOMATED_UPSTREAM_RUN_ID")
    upstream_workflow = os.environ.get("UPSTREAM_WORKFLOW_NAME", "Main branch")

    logger.info(f"Validating release eligibility for [bold cyan]{repo or 'Unknown Repo'}[/bold cyan]")
    logger.info(f"Trigger Event: [bold blue]{event_name or 'Unknown Event'}[/bold blue]")

    if not event_name or not repo:
        _conclude_validation("Missing EVENT or REPO env vars.", severity="error", release_type="unknown")

    if not token:
        logger.warning("GH_TOKEN environment variable is not set. API calls to GitHub will likely fail.")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    base_url = f"https://api.github.com/repos/{repo}"

    # Case 1: Manual Trigger (Untrusted Input)
    # We verify that the user-provided Tag and Run ID actually exist via GitHub API
    # and ensure the Tag points to the same SHA as the Workflow Run.
    if event_name == "workflow_dispatch":
        logger.info(
            f"Processing manual workflow dispatch for tag [bold green]{manual_tag or '[MISSING]'}[/bold green] (Upstream Run: {manual_run_id or '[MISSING]'})"
        )

        if not manual_run_id or not re.match(r"^[0-9]+$", manual_run_id):
            _conclude_validation(
                "Manual workflow dispatch requires a numeric MANUAL_UPSTREAM_RUN_ID.",
                severity="error",
                release_type="unknown",
            )

        try:
            # Verify the Workflow Run is successful and exists.
            run_data = _get_run_info(manual_run_id, repo, headers, base_url, upstream_workflow)
            run_sha = run_data.get("head_sha")

            # If a version tag is supplied, this is a release workflow and we must validate it.
            if manual_tag:
                tag_sha = _get_tag_sha(manual_tag, headers, base_url)
                if tag_sha != run_sha:
                    _conclude_validation(
                        f"Tag SHA mismatch for Run {manual_run_id}.",
                        severity="error",
                        release_type="unknown",
                    )

                head_sha = run_data.get("head_sha", "unknown")
                _append_github_output("version", manual_tag)
                _append_github_output("run_id", manual_run_id)
                _append_github_output("head_sha", head_sha)
                _conclude_validation(
                    f"Manually triggered versioned release for tag '{manual_tag}'.",
                    severity="notice",
                    release_type="versioned",
                )

            logger.info("No version tag supplied; treating this as a main-branch unversioned release.")
            _append_github_output("version", "")
            _append_github_output("run_id", manual_run_id)
            _append_github_output("head_sha", run_sha or "unknown")
            _conclude_validation(
                f"Manually triggered unversioned release for commit '{run_sha[:8]}'.",
                severity="notice",
                release_type="unversioned",
            )
        except ValueError as e:
            _conclude_validation(str(e), severity="error", release_type="unknown")
        except requests.exceptions.RequestException as e:
            error_msg = f"GitHub API communication error: {e}"
            if e.response is not None and e.response.status_code == 401:
                error_msg = "Unauthorized (401). Ensure GH_TOKEN is set and valid for the target repository."
            _conclude_validation(error_msg, severity="error", release_type="unknown")
        except Exception as e:
            _conclude_validation(
                f"Unexpected error during release check: {e}",
                severity="error",
                release_type="unknown",
            )

    # Case 2: Automated Trigger (Trusted Input)
    # GitHub provides the Run ID and SHA automatically. We verify that a SemVer
    # tag (v*) exists on that SHA to justify proceeding with a release.
    if event_name == "workflow_run":
        logger.info(
            f"Processing automated release trigger for SHA [bold green]{commit_sha[:8] if commit_sha else '[MISSING]'}[/bold green] (Run ID: {automated_run_id or '[MISSING]'})"
        )

        if not commit_sha or not automated_run_id:
            _conclude_validation(
                "Missing SHA or AUTO_ID env vars for automated release.",
                severity="error",
                release_type="unknown",
            )

        if upstream_conclusion != "success":
            # This trigger is only valid when the upstream main-branch workflow succeeded.
            # A failed upstream build is a legitimate non-release outcome, not an error.
            _conclude_validation(
                f"Upstream build status was '{upstream_conclusion}'.",
                severity="warning",
                release_type="unknown",
            )
        try:
            # A successful workflow_run is always a legitimate main-branch validation event.
            # The release classification is decided afterward based on whether a version tag
            # exists for that commit. Lack of a v* tag means it is a valid unversioned publish,
            # not a failed automated release check.
            tag_name = _find_tag_for_sha(commit_sha, headers, base_url)
            if not tag_name:
                _append_github_output("version", "")
                _append_github_output("run_id", automated_run_id)
                _append_github_output("head_sha", commit_sha)
                _conclude_validation(
                    f"No version tag (v*) found for SHA {commit_sha[:8]}; treating this as an unversioned release.",
                    severity="notice",
                    release_type="unversioned",
                )

            _append_github_output("version", tag_name)
            _append_github_output("run_id", automated_run_id)
            _append_github_output("head_sha", commit_sha)
            _conclude_validation(
                f"Auto triggered versioned release for tag '{tag_name}'",
                severity="notice",
                release_type="versioned",
            )
        except Exception as e:
            msg = f"Resolution error: {e}"
            if (
                isinstance(e, requests.exceptions.RequestException)
                and e.response is not None
                and e.response.status_code == 401
            ):
                msg = "Unauthorized (401). Ensure GH_TOKEN is valid."
            _conclude_validation(msg, severity="error", release_type="unknown")
        return

    _conclude_validation(f"Unsupported event: {event_name}", severity="error", release_type="unknown")


def publish_pypi(extra_args: list[str] | None = None):
    """Publishes the built Python artifacts to PyPI.

    Args:
        extra_args: Additional arguments for uv publish.
    """
    run_command(["uv", "publish"] + (extra_args or []), "Publishing package to PyPI")


def publish_docker(image_name: str | None = None):
    """Pushes a Docker image to a registry.

    The image reference is resolved by the caller (for example, from the Docker build
    command's tag) and passed through as a single value. This keeps the CLI consistent
    with Docker's own image-reference semantics and avoids reconstructing tags from
    separate image/name arguments.
    """
    image_name = image_name or "localhost/gitlabform:latest"
    docker_bin = get_executable("docker")

    run_command([docker_bin, "push", image_name], f"Pushing Docker image: [bold cyan]{image_name}[/bold cyan]")
