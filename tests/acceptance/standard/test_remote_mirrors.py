import os
import pytest
import time
from typing import cast, Tuple, Generator
from gitlab.v4.objects import Project, ProjectRemoteMirror, ProjectBranch, Group

from tests.acceptance import run_gitlabform, get_random_name, create_project
from tests.acceptance.conftest import GitLabFormLogs


@pytest.fixture(scope="class")
def mirror_target_projects(other_group: Group) -> Generator[Tuple[Project, Project, Project], None, None]:
    """Create three target projects in another group to use as mirror destinations."""
    first_project = create_project(other_group, get_random_name("mirror_target_1"))
    second_project = create_project(other_group, get_random_name("mirror_target_2"))
    third_project = create_project(other_group, get_random_name("mirror_target_3"))

    yield first_project, second_project, third_project

    # Cleanup
    first_project.delete()
    second_project.delete()
    third_project.delete()


@pytest.fixture(scope="class")
def mirror_urls(
    mirror_target_projects: Tuple[Project, Project, Project], root_username: str, root_access_token: str
) -> Tuple[str, str, str]:
    """Generate mirror URLs pointing to projects in the same GitLab instance.

    HTTP based URL for password based credential as required by GitLab API:
    http://username:password@host/path.git

    SSH based URL for password based credential as required by GitLab API:
    ssh://username:password@host/path.git

    SSH based URL for public-key based credential as required by GitLab API:
    ssh://username@host/path.git
    """

    # For local testing, we use http://localhost as the host since we don't have SSL setup.
    gitlab_url = os.getenv("GITLAB_URL", "http://localhost").rstrip("/")

    first_project, second_project, third_project = mirror_target_projects

    # Construct mirror URLs with embedded credentials - each pointing to a different target project
    mirror_url_base_http_password_auth = gitlab_url.replace("http://", f"http://{root_username}:{root_access_token}@")
    first_project_mirror_url_http_password_auth = (
        f"{mirror_url_base_http_password_auth}/{first_project.path_with_namespace}.git"
    )

    mirror_url_base_ssh_password_auth = gitlab_url.replace("http://", f"ssh://{root_username}:{root_access_token}@")
    second_project_mirror_url_ssh_password_auth = (
        f"{mirror_url_base_ssh_password_auth}/{second_project.path_with_namespace}.git"
    )

    mirror_url_base_ssh_public_key_auth = gitlab_url.replace("http://", f"ssh://{root_username}@")
    third_project_mirror_url_ssh_public_key_auth = (
        f"{mirror_url_base_ssh_public_key_auth}/{third_project.path_with_namespace}.git"
    )

    return (
        first_project_mirror_url_http_password_auth,
        second_project_mirror_url_ssh_password_auth,
        third_project_mirror_url_ssh_public_key_auth,
    )


class TestRemoteMirrorsProcessor:
    def _normalize_url_for_comparison(self, url: str) -> str:
        """Normalize URL for comparison by removing credentials.

        Given a mirror URL for password-based authentication,
        this method returns the corresponding URL without credentials.

        Example:
        http://username:password@host/path.git -> http://host/path.git

        This is used to compare mirror URLs without credentials to find matching mirrors.
        """
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        # Mypy fixes: handle None types from urlparse
        hostname = parsed.hostname if parsed.hostname else ""
        port_suffix = f":{parsed.port}" if parsed.port else ""
        netloc = hostname + port_suffix

        # Reconstruct URL without userinfo (credentials)
        normalized = urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
        return str(normalized)

    def _get_mirror_from_url(self, project: Project, url_with_credentials: str) -> ProjectRemoteMirror | None:
        """Helper method to get a remote mirror by URL.

        Given a password-based mirror URL, this method returns
        the corresponding ProjectRemoteMirror object if found, otherwise None.

        GitLab API returns URLs with credentials scrubbed (*****).
        So, we need to use URLs without credentials to find matching mirrors.

        Args:
            project: The GitLab project object
            url_with_credentials: The mirror URL to search for (may have embedded credentials)

        Returns:
            ProjectRemoteMirror object if found, None otherwise
        """

        mirror_url_from_config_without_credentials = self._normalize_url_for_comparison(url_with_credentials)
        all_mirrors = project.remote_mirrors.list(get_all=True)

        for mirror in all_mirrors:
            mirror_url_from_gitlab = cast(ProjectRemoteMirror, mirror).url
            mirror_url_from_gitlab_without_credentials = self._normalize_url_for_comparison(mirror_url_from_gitlab)
            if mirror_url_from_gitlab_without_credentials == mirror_url_from_config_without_credentials:
                return cast(ProjectRemoteMirror, mirror)

        return None

    def test_remote_mirrors_create(self, project: Project, mirror_urls: Tuple[str, str, str]) -> None:
        """
        Test creating multiple remote mirrors with different URL/auth types.
        """

        (
            first_mirror_url_http_password_auth,
            second_mirror_url_ssh_password_auth,
            third_mirror_url_ssh_public_key_auth,
        ) = mirror_urls

        gitlabform_config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                remote_mirrors:
                  {first_mirror_url_http_password_auth}:
                    enabled: true
                    auth_method: password
                  {second_mirror_url_ssh_password_auth}:
                    enabled: true
                    auth_method: password
                    keep_divergent_refs: true
                  {third_mirror_url_ssh_public_key_auth}:
                    enabled: false
                    auth_method: ssh_public_key
            """

        run_gitlabform(gitlabform_config, project.path_with_namespace)

        first_mirror = self._get_mirror_from_url(project, first_mirror_url_http_password_auth)
        second_mirror = self._get_mirror_from_url(project, second_mirror_url_ssh_password_auth)
        third_mirror = self._get_mirror_from_url(project, third_mirror_url_ssh_public_key_auth)

        # Mypy fix: Verify mirrors are not None before accessing attributes
        assert first_mirror is not None
        assert second_mirror is not None
        assert third_mirror is not None

        mirrors = project.remote_mirrors.list(get_all=True)
        assert len(mirrors) == 3

        assert first_mirror.enabled is True
        assert first_mirror.auth_method == "password"
        assert self._normalize_url_for_comparison(first_mirror.url) == self._normalize_url_for_comparison(
            first_mirror_url_http_password_auth
        )

        assert second_mirror.enabled is True
        assert second_mirror.auth_method == "password"
        assert getattr(second_mirror, "keep_divergent_refs", None) is True
        assert self._normalize_url_for_comparison(second_mirror.url) == self._normalize_url_for_comparison(
            second_mirror_url_ssh_password_auth
        )

        assert third_mirror.enabled is False
        assert third_mirror.auth_method == "ssh_public_key"
        assert self._normalize_url_for_comparison(third_mirror.url) == self._normalize_url_for_comparison(
            third_mirror_url_ssh_public_key_auth
        )

    def test_remote_mirrors_update_configuration(
        self, project: Project, mirror_urls: Tuple[str, str, str], gitlabform_logs: GitLabFormLogs
    ) -> None:
        """
        This test validates configuration update of remote mirror by spying on
        gitlabform's verbose logs.
        """

        # 1. Setup the mirror URLs from the fixture
        first_url, second_url, _ = mirror_urls

        gitlabform_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            remote_mirrors:
              {first_url}:
                enabled: true
                auth_method: password
              {second_url}:
                enabled: true
                auth_method: password
                keep_divergent_refs: false
        """

        # 2. Run GitLabForm
        run_gitlabform(gitlabform_config, project.path_with_namespace)

        # 3. Get normalized URLs for the assertions
        first_mirror = self._get_mirror_from_url(project, first_url)
        assert first_mirror is not None
        first_norm = self._normalize_url_for_comparison(first_mirror.url)

        second_mirror = self._get_mirror_from_url(project, second_url)
        assert second_mirror is not None
        second_norm = self._normalize_url_for_comparison(second_mirror.url)

        # 4. Assertions
        assert first_mirror.enabled is True
        assert first_mirror.auth_method == "password"
        # Use substring matching (in) because cli_ui often adds prefixes like '* ' or ':: '
        expected_unchanged = f"Remote mirror '{first_norm}' remains unchanged"
        assert any(
            expected_unchanged in msg for msg in gitlabform_logs.debug
        ), f"Expected unchanged message not found. Captured: {gitlabform_logs.debug}"

        assert second_mirror.enabled is True
        assert second_mirror.auth_method == "password"
        assert getattr(second_mirror, "keep_divergent_refs", None) is False
        expected_updated = f"Updated remote mirror '{second_norm}'"
        assert any(
            expected_updated in msg for msg in gitlabform_logs.debug
        ), f"Expected update message not found. Captured: {gitlabform_logs.debug}"

    def test_remote_mirrors_update_credentials(
        self, project_for_function: Project, root_username: str, root_access_token: str, gitlabform_logs: GitLabFormLogs
    ) -> None:
        """
        Validates credential updates for 3 mirror types (HTTP, SSH+Pass, SSH+Key).
        Uses project_for_function to ensure an isolated state for this test.
        """
        target_path = project_for_function.path_with_namespace

        # Define 3 distinct dummy URL types
        # These URLs don't need to exist; we are testing GitLabForm's logic branch and API communication
        urls = [
            f"http://{root_username}:{root_access_token}@localhost/dummy/http_target.git",
            f"ssh://{root_username}:{root_access_token}@localhost/dummy/ssh_pass_target.git",
            f"ssh://{root_username}@localhost/dummy/ssh_key_target.git",
        ]

        # 1. Setup initial mirrors directly via API
        # We manually create these so GitLabForm sees them as "already existing"
        for url in urls:
            project_for_function.remote_mirrors.create(
                {
                    "url": url,
                    "enabled": True,
                    # Simple logic to assign auth_method for setup
                    "auth_method": "password" if "ssh://" not in url or ":" in url.split("@")[0] else "ssh_public_key",
                }
            )

        # 2. Run GitLabForm with force_update: true
        config = f"""
        projects_and_groups:
          {target_path}:
            remote_mirrors:
              {urls[0]}:
                enabled: true
                force_update: true
              {urls[1]}:
                enabled: true
                force_update: true
              {urls[2]}:
                enabled: true
                force_update: true
        """

        run_gitlabform(config, target_path)

        # 3. Assertions
        for url in urls:
            norm = self._normalize_url_for_comparison(url)

            # Check Debug Log: Confirms the Processor triggered the update despite masked credentials
            expected_debug = f"Updating remote mirror '{norm}' with latest config"
            assert any(
                expected_debug in msg for msg in gitlabform_logs.debug
            ), f"Expected update log not found for {norm}."

            # Check Info Log: Confirms the reminder was printed at the standard output level
            expected_info = f"!!! REMINDER: 'force_update' was used for mirror '{norm}'"
            assert any(
                expected_info in msg for msg in gitlabform_logs.info
            ), f"Expected info reminder not found for {norm}."

    def test_remote_mirror_http_password_auth_sync(
        self,
        project: Project,
        mirror_urls: Tuple[str, str, str],
        mirror_target_projects: Tuple[Project, Project, Project],
    ) -> None:
        """
        Test remote mirror functionality for http and password based authentication.
        This also tests configuration of `force_push` config key.

        This is validated by creating a new branch and a test file in the source project.
        Then run gitlabform with `force_push` enabled for the target mirror.
        Then check the target mirror repo if the new branch and the test file exists.
        """
        first_mirror_url_http_password_auth, _, _ = mirror_urls
        first_mirror_repo, _, _ = mirror_target_projects

        # In GitLab, default setting for branch protection is to deny force push.
        # For first mirror, we need to allow force push to the main branch, so that
        # we can validate the mirror functionality.
        first_mirror_repo_main_branch = cast(ProjectBranch, first_mirror_repo.protectedbranches.get("main"))
        first_mirror_repo_main_branch.allow_force_push = True
        first_mirror_repo_main_branch.save()

        # Create a test file in a new branch in the source project to validate mirror functionality
        # We use a unique branch name to ensure we are testing a fresh sync
        sync_branch_name = get_random_name("sync_test_branch")
        project.branches.create({"branch": sync_branch_name, "ref": "main"})

        test_file_content = "This is a test file for remote mirror validation"
        test_file_path = f"mirror_test_{sync_branch_name}.txt"

        project.files.create(
            {
                "branch": sync_branch_name,
                "file_path": test_file_path,
                "content": test_file_content,
                "commit_message": "Add test file for mirror validation",
            }
        )

        # Validate that the test file exists in the source project
        source_file = project.files.get(ref=sync_branch_name, file_path=test_file_path)
        assert source_file is not None
        assert source_file.decode().decode("utf-8") == test_file_content

        # Run GitLabForm with force_push enabled.
        # This should trigger the self._sync_remote_mirror(project, mirror_in_gitlab) logic.
        gitlabform_config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                remote_mirrors:
                  {first_mirror_url_http_password_auth}:
                    enabled: true
                    auth_method: password
                    force_push: true
            """

        run_gitlabform(gitlabform_config, project.path_with_namespace)

        # Validate mirror functionality: wait for sync and verify test file appears in target.
        # Even with force_push: true, GitLab's Sidekiq worker may take a few seconds to
        # complete the physical git push to the remote.
        found = False
        max_retries = 10
        retry_interval = 5

        for i in range(max_retries):
            try:
                # Attempt to retrieve the file from the target repository
                target_file = first_mirror_repo.files.get(ref=sync_branch_name, file_path=test_file_path)
                if target_file.decode().decode("utf-8") == test_file_content:
                    found = True
                    break
            except Exception:
                # If 404/Exception, wait and try again
                time.sleep(retry_interval)

        assert found, (
            f"Mirror sync failed: File '{test_file_path}' not found in target project "
            f"'{first_mirror_repo.path_with_namespace}' after {max_retries * retry_interval} seconds."
        )

    def test_remote_mirrors_ssh_public_key_retrieval(
        self, project_for_function: Project, gitlabform_logs: GitLabFormLogs
    ) -> None:
        """
        Validates that when print_public_key is true, the SSH public key is
        retrieved and printed to the console.
        """
        target_path = project_for_function.path_with_namespace
        ssh_url = "ssh://git@github.com/dummy/target_repo.git"

        # 1. Run GitLabForm with print_public_key: true
        # We use auth_method: ssh_public_key to trigger the logic
        config = f"""
        projects_and_groups:
          {target_path}:
            remote_mirrors:
              {ssh_url}:
                enabled: true
                auth_method: ssh_public_key
                print_public_key: true
        """

        run_gitlabform(config, target_path)

        # 2. Assertions
        # Normalize the URL as the processor does for logs
        norm_url = self._normalize_url_for_comparison(ssh_url)

        # Check that the mirror was created/updated
        assert any(
            f"Creating remote mirror '{norm_url}'" in msg or f"Updated remote mirror '{norm_url}'" in msg
            for msg in gitlabform_logs.debug
        )

        # 3. Check for the Public Key Output
        # We look for the generic instructions and the presence of an SSH key pattern
        instruction_text = "This public key must be added to the target repository"
        key_header = f"🔑 SSH Public Key for mirror '{norm_url}':"

        # Verify the instructional text is in the info stream
        assert any(
            instruction_text in msg for msg in gitlabform_logs.info
        ), f"Instructional text not found in info logs. Captured: {gitlabform_logs.info}"

        assert any(
            key_header in msg for msg in gitlabform_logs.info
        ), f"Key header not found in info logs. Captured: {gitlabform_logs.info}"

        # Check if any message in the info stream looks like a public key (starts with ssh-rsa, ecdsa, etc.)
        ssh_key_patterns = ["ssh-rsa", "ssh-ed25519", "ecdsa-sha2-nistp256"]
        found_key = any(any(pattern in msg for pattern in ssh_key_patterns) for msg in gitlabform_logs.info)

        assert found_key, f"No SSH public key pattern found in info logs. Captured: {gitlabform_logs.info}"

    def test_remote_mirrors_delete(
        self, project: Project, mirror_urls: Tuple[str, str, str], gitlabform_logs: GitLabFormLogs
    ) -> None:
        """Test deleting remote mirrors using the delete flag.

        This test verifies that:
        - Mirrors can be deleted using the 'delete: true' configuration
        - Non-existent mirrors configured for deletion are handled gracefully
        - Other mirrors not marked for deletion remain intact
        """
        first_url, second_url, third_url = mirror_urls
        non_existent_mirror_url = f"http://username:password@localhost/non/existent_project.git"

        delete_yaml = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            remote_mirrors:
              {first_url}:
                delete: true
              {non_existent_mirror_url}:
                delete: true
        """

        run_gitlabform(delete_yaml, project.path_with_namespace)
        mirrors_after_test = project.remote_mirrors.list(get_all=True)
        second_mirror_after_test = self._get_mirror_from_url(project, second_url)
        third_mirror_after_test = self._get_mirror_from_url(project, third_url)

        # In last test, there were 3 mirrors.
        # This test should delete the first mirror successfully
        # So, there should be 2 mirrors remaining.
        # non-existent mirror deletion should be handled gracefully without quiting.

        assert len(mirrors_after_test) == 2

        # The first mirror should not exist as indicated by 'delete: true' config
        assert first_url not in (m.url for m in mirrors_after_test)

        # The second & third mirror should exist
        assert second_mirror_after_test is not None
        assert second_mirror_after_test in mirrors_after_test
        assert third_mirror_after_test is not None
        assert third_mirror_after_test in mirrors_after_test

        # The last mirror configured for deletion but it was never setup in gitlab.
        # Ensure expected error message is reported.
        expected = f"Skip deleting remote mirror '{self._normalize_url_for_comparison(non_existent_mirror_url)}', because it doesn't exist"
        assert any(
            expected in msg for msg in gitlabform_logs.debug
        ), f"Expected message not found. Captured: {gitlabform_logs.debug}"

    def test_remote_mirrors_enforce_false(self, project: Project, mirror_urls: Tuple[str, str, str]) -> None:
        """Test the additive behavior when enforce: false is set.

        This test verifies that:
        - When 'enforce: false' is set, mirrors not mentioned in the
          configuration are NOT deleted (additive behavior).
        - Existing mirrors mentioned in the configuration are updated correctly.

        """
        target = project.path_with_namespace
        _, second_url, third_url = mirror_urls

        # 1. Normalize our target URLs from the fixture
        second_norm = self._normalize_url_for_comparison(second_url)
        third_norm = self._normalize_url_for_comparison(third_url)

        # 2. Verify starting state: 2nd and 3rd mirrors should exist
        # (assuming they were left over from previous test setup)
        mirrors_before = [
            self._normalize_url_for_comparison(cast(ProjectRemoteMirror, m).url)
            for m in project.remote_mirrors.list(get_all=True)
        ]

        assert second_norm in mirrors_before
        assert third_norm in mirrors_before

        # 3. Apply config that only contains the second mirror
        not_enforce_yaml = f"""
        projects_and_groups:
          {target}:
            remote_mirrors:
              enforce: false
              {second_url}:
                enabled: true
                auth_method: password
                only_protected_branches: true
        """

        run_gitlabform(not_enforce_yaml, target)

        # 4. Get the state after the run and normalize for comparison
        mirrors_after = [
            self._normalize_url_for_comparison(cast(ProjectRemoteMirror, m).url)
            for m in project.remote_mirrors.list(get_all=True)
        ]

        # 5. Assertions
        # Total number of mirrors should still be 2 because enforce: false
        # prevents the deletion of third_url
        assert len(mirrors_after) == 2

        # The mirror in the config (second) must still exist
        assert second_norm in mirrors_after

        # The mirror NOT in the config (third) must ALSO still exist (Additive check)
        assert third_norm in mirrors_after, (
            f"Mirror {third_norm} was deleted but it should have been kept " f"because enforce is set to false."
        )

    def test_remote_mirrors_enforce_true(self, project: Project, mirror_urls: Tuple[str, str, str]) -> None:
        """Test the destructive behavior when enforce: true is set.

        This test verifies that:
        - When 'enforce: true' is set, any mirror found in GitLab that is
          NOT defined in the configuration is automatically deleted.
        """
        target = project.path_with_namespace
        _, second_url, third_url = mirror_urls

        # Normalize our target URLs
        second_norm = self._normalize_url_for_comparison(second_url)
        third_norm = self._normalize_url_for_comparison(third_url)

        # Ensure we are starting with both mirrors
        mirrors_before = [
            self._normalize_url_for_comparison(cast(ProjectRemoteMirror, m).url)
            for m in project.remote_mirrors.list(get_all=True)
        ]
        assert second_norm in mirrors_before
        assert third_norm in mirrors_before

        # 1. Apply config with enforce: true, only containing the second mirror
        enforce_true_yaml = f"""
        projects_and_groups:
          {target}:
            remote_mirrors:
              enforce: true
              {second_url}:
                enabled: true
                auth_method: password
        """

        run_gitlabform(enforce_true_yaml, target)

        # 2. Get state after run
        mirrors_after = [
            self._normalize_url_for_comparison(cast(ProjectRemoteMirror, m).url)
            for m in project.remote_mirrors.list(get_all=True)
        ]

        # 3. Assertions
        # third_url should now be GONE because it wasn't in the YAML
        assert len(mirrors_after) == 1
        assert second_norm in mirrors_after
        assert third_norm not in mirrors_after, f"Mirror {third_norm} should have been deleted by enforce: true logic."

    def test_remote_mirrors_enforce_with_explicit_delete(
        self, project: Project, mirror_urls: Tuple[str, str, str]
    ) -> None:
        """Test the interaction between 'enforce: true' and explicit 'delete: true'.

        This test verifies that:
        - Mirrors marked with 'delete: true' are removed correctly.
        - Mirrors NOT in the config are removed by the 'enforce: true' logic.
        - Handles multiple auth types (password vs ssh_public_key) during setup.
        - The processor handles both types of removals in a single run.
        """
        target = project.path_with_namespace
        first_url, second_url, third_url = mirror_urls

        # 1. Define EXPECTED normalized URLs BEFORE setup
        expected_norms = {
            self._normalize_url_for_comparison(first_url),
            self._normalize_url_for_comparison(second_url),
            self._normalize_url_for_comparison(third_url),
        }

        # --- DIRECT SETUP PHASE (using python-gitlab) ---
        # Clear existing mirrors first to ensure a clean state
        for m in project.remote_mirrors.list(get_all=True):
            cast(ProjectRemoteMirror, m).delete()

        # Create 3 mirrors directly using the raw URLs from the fixture
        for url in [first_url, second_url, third_url]:
            payload = {
                "url": url,
                "enabled": True,
            }

            # Detect auth method based on fixture URL format
            if "://" in url and ":" not in url.split("://")[1].split("@")[0]:
                payload["auth_method"] = "ssh_public_key"
            else:
                payload["auth_method"] = "password"

            project.remote_mirrors.create(payload)

        # --- VALIDATE SETUP ---
        # 2. Fetch ACTUAL mirrors from GitLab AFTER creation
        actual_mirrors_from_api = project.remote_mirrors.list(get_all=True)
        actual_norms = {
            self._normalize_url_for_comparison(cast(ProjectRemoteMirror, m).url) for m in actual_mirrors_from_api
        }

        # VALIDATION: Ensure every expected URL from our fixture exists in GitLab
        assert expected_norms == actual_norms, f"Setup Mismatch! \nExpected: {expected_norms}\nActual: {actual_norms}"

        # --- TEST PHASE ---
        # We delete 'first', keep 'second', and omit 'third' (letting enforce delete it)
        test_yaml = f"""
        projects_and_groups:
          {target}:
            remote_mirrors:
              enforce: true
              {first_url}:
                delete: true
              {second_url}:
                enabled: true
                auth_method: password
                only_protected_branches: true
        """

        run_gitlabform(test_yaml, target)

        # --- VERIFICATION PHASE ---
        final_mirrors = project.remote_mirrors.list(get_all=True)
        final_norms = {self._normalize_url_for_comparison(cast(ProjectRemoteMirror, m).url) for m in final_mirrors}

        # Only the second mirror's normalized URL should remain.
        second_norm = self._normalize_url_for_comparison(second_url)
        assert final_norms == {second_norm}, f"Expected only {second_norm} to remain. Found: {final_norms}"

    def test_remote_mirrors_print_details(
        self,
        project: Project,
        mirror_urls: Tuple[str, str, str],
        gitlabform_logs: GitLabFormLogs,
        root_username,
        root_access_token,
    ) -> None:
        """
        Validates that when print_details is true, the full mirror object
        details are retrieved and printed to the info logs.
        """
        target_path = project.path_with_namespace
        first_url, second_url, _ = mirror_urls

        # Normalize URLs as they will appear in the masked logs
        # first_norm = self._normalize_url_for_comparison(first_url)
        # second_norm = self._normalize_url_for_comparison(second_url)

        # 1. Setup: Ensure at least one mirror exists manually that is NOT in the config
        # This tests that the report shows the "Final State" of GitLab, not just the config.
        project.remote_mirrors.create({"url": second_url, "enabled": True, "auth_method": "password"})

        # 2. Run GitLabForm with global print_details: true
        # Config only contains the first mirror
        config = f"""
        projects_and_groups:
          {target_path}:
            remote_mirrors:
              print_details: true
              enforce: false
              {first_url}:
                enabled: true
                auth_method: password
                only_protected_branches: true
        """

        run_gitlabform(config, target_path)

        # 3. Assertions: Check for the Report Header
        report_header = f"📋 Final Remote Mirror Report for '{target_path}':"
        assert any(
            report_header in msg for msg in gitlabform_logs.info
        ), f"Report header not found in info logs. Captured: {gitlabform_logs.info}"

        # 4. Assertions: Check for Mirror 1 (from config)
        # We expect GitLab to have masked the username and the token/password
        # resulting in "https://*****:*****@..."
        expected_api_url = first_url.replace(root_username, "*****").replace(root_access_token, "*****")
        assert any(f"- url: {expected_api_url}" in msg for msg in gitlabform_logs.info)
        assert any("- only_protected_branches: True" in msg for msg in gitlabform_logs.info)

        # 5. Assertions: Check for Mirror 2 (unconfigured but existing in GitLab)
        # We expect GitLab to have masked the username and the token/password
        # resulting in "https://*****:*****@..."
        # This confirms the report shows all mirrors if enforce is false
        expected_api_url = second_url.replace(root_username, "*****").replace(root_access_token, "*****")
        assert any(f"- url: {expected_api_url}" in msg for msg in gitlabform_logs.info)

        # 6. Check for status with icon (Default status for new/idle mirrors is 'none')
        # We check for 'none' or 'finished' depending on how fast GitLab processed the sync
        status_pattern = ["update_status: ⚪ none", "update_status: ✅ finished"]
        found_status = any(any(pattern in msg for pattern in status_pattern) for msg in gitlabform_logs.info)
        assert found_status, f"Mirror status icon not found in report. Logs: {gitlabform_logs.info}"

        # 7. Verify visual separators
        separator = "─" * 30
        assert any(separator in msg for msg in gitlabform_logs.info), "Visual separator line not found in report logs."

    def test_remote_mirrors_print_details_disabled_by_default(
        self, project_for_function: Project, mirror_urls: Tuple[str, str, str], gitlabform_logs: GitLabFormLogs
    ) -> None:
        """
        Ensures that no detailed report is printed when print_details is not set.
        """
        target_path = project_for_function.path_with_namespace
        url, _, _ = mirror_urls

        config = f"""
        projects_and_groups:
          {target_path}:
            remote_mirrors:
              {url}:
                enabled: true
        """

        run_gitlabform(config, target_path)

        report_header = "📋 Final Remote Mirror Report"
        assert not any(
            report_header in msg for msg in gitlabform_logs.info
        ), "Report header found in logs even though print_details was not enabled."
