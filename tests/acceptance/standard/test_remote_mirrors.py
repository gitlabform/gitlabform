import os
import pytest
from typing import TYPE_CHECKING
from gitlab.v4.objects import ProjectRemoteMirror

from tests.acceptance import run_gitlabform, get_random_name, create_project
from tests.acceptance.conftest import GitLabFormLogs


@pytest.fixture(scope="class")
def mirror_target_projects(other_group):
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
def mirror_urls(gl, mirror_target_projects, root_username, root_access_token):
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
    # http_mirror_password_auth_url = gitlab_url
    # ssh_mirror_password_auth_url = gitlab_url.replace("http://", f"ssh://")

    first_project, second_project, third_project = mirror_target_projects
    
    # Construct mirror URLs with embedded credentials - each pointing to a different target project
    mirror_url_base_http_password_auth = gitlab_url.replace("http://", f"http://{root_username}:{root_access_token}@")
    first_project_mirror_url_http_password_auth = f"{mirror_url_base_http_password_auth}/{first_project.path_with_namespace}.git"

    mirror_url_base_ssh_password_auth = gitlab_url.replace("http://", f"ssh://{root_username}:{root_access_token}@")
    second_project_mirror_url_ssh_password_auth = f"{mirror_url_base_ssh_password_auth}/{second_project.path_with_namespace}.git"

    mirror_url_base_ssh_public_key_auth = gitlab_url.replace("http://", f"ssh://{root_username}@")
    third_project_mirror_url_ssh_public_key_auth = f"{mirror_url_base_ssh_public_key_auth}/{third_project.path_with_namespace}.git"

    return first_project_mirror_url_http_password_auth, second_project_mirror_url_ssh_password_auth, third_project_mirror_url_ssh_public_key_auth


    # if gitlab_url_http:
    #     base_url_http = gitlab_url_http.replace("http://", f"http://{root_username}:{root_access_token}@")
    #     first_project_url_http = f"{base_url_http}/{first_project.path_with_namespace}.git"

    # if gitlab_url_ssh:
    #     base_url_ssh = gitlab_url_ssh.replace("ssh://", f"ssh://@{root_username}:{root_access_token}@")
        
    #     second_project_url_ssh_password_based = f"{base_url_ssh}/{second_project.path_with_namespace}.git"
    #     third_project_url_ssh_public_key_based = f"{gitlab_url_ssh}/{third_project.path_with_namespace}.git"

    # # For SSH based URL, GitLab allows authenticating using SSH public key or username/password (i.e. token)
    # # https://docs.gitlab.com/user/project/repository/mirror/#ssh-authentication

    # return first_project_url_http, second_project_url_ssh_password_based, third_project_url_ssh_public_key_based


@pytest.fixture(scope="class")
def root_access_token():
    """Return the root user's Personal Access Token.
    
    This is the root user's Personal Access Token.
    Used for password-based authentication in remote mirror tests.
    """
    return os.getenv("GITLAB_TOKEN")


@pytest.fixture(scope="class")
def root_username():
    """Return the root username for GitLab authentication.
    
    Used for password-based authentication in remote mirror tests.
    """
    return "root"


class TestRemoteMirrorsProcessor:
    @staticmethod
    def _normalize_url_for_comparison(url: str) -> str:
        """Normalize URL for comparison by removing credentials.
        
        Given a mirror URL for password-based authentication,
        this method returns the corresponding URL without credentials.
        
        Example:
        http://username:password@host/path.git -> http://host/path.git
        
        This is used to compare mirror URLs without credentials to find matching mirrors.
        """
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        # Reconstruct URL without userinfo (credentials)
        normalized = urlunparse((
            parsed.scheme,
            parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return normalized
    
    @staticmethod
    def _get_mirror_from_url(project, url_with_credentials: str) -> ProjectRemoteMirror | None:
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
        
        mirror_url_from_config_without_credentials = TestRemoteMirrorsProcessor._normalize_url_for_comparison(url_with_credentials)
        all_mirrors = project.remote_mirrors.list(get_all=True)

        for mirror in all_mirrors:
            mirror_url_from_gitlab = mirror.url
            mirror_url_from_gitlab_without_credentials = TestRemoteMirrorsProcessor._normalize_url_for_comparison(mirror_url_from_gitlab)
            if mirror_url_from_gitlab_without_credentials == mirror_url_from_config_without_credentials:
                return mirror
        
        return None

    def test_remote_mirrors_create(self, gl, project, mirror_urls):
        """
        Test creating multiple remote mirrors with different URL/auth types.
        """

        first_mirror_url_http_password_auth, second_mirror_url_ssh_password_auth, third_mirror_url_ssh_public_key_auth = mirror_urls

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

        if TYPE_CHECKING:
            assert isinstance(first_mirror, ProjectRemoteMirror)
            assert isinstance(second_mirror, ProjectRemoteMirror)
            assert isinstance(third_mirror, ProjectRemoteMirror)
        
        mirrors = project.remote_mirrors.list(get_all=True)
        assert len(mirrors) == 3
        
        assert first_mirror is not None
        assert first_mirror.enabled is True
        assert first_mirror.auth_method == "password"
        assert TestRemoteMirrorsProcessor._normalize_url_for_comparison(first_mirror.url) == TestRemoteMirrorsProcessor._normalize_url_for_comparison(first_mirror_url_http_password_auth)
        
        assert second_mirror is not None
        assert second_mirror.enabled is True
        assert second_mirror.auth_method == "password"
        assert second_mirror.keep_divergent_refs is True
        assert TestRemoteMirrorsProcessor._normalize_url_for_comparison(second_mirror.url) == TestRemoteMirrorsProcessor._normalize_url_for_comparison(second_mirror_url_ssh_password_auth)
        
        assert third_mirror is not None
        assert third_mirror.enabled is False
        assert third_mirror.auth_method == "ssh_public_key"
        assert TestRemoteMirrorsProcessor._normalize_url_for_comparison(third_mirror.url) == TestRemoteMirrorsProcessor._normalize_url_for_comparison(third_mirror_url_ssh_public_key_auth)


    def test_remote_mirrors_update_configuration(self, project, mirror_urls, gitlabform_logs: GitLabFormLogs):
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
        first_norm = TestRemoteMirrorsProcessor._normalize_url_for_comparison(first_mirror.url)

        second_mirror = self._get_mirror_from_url(project, second_url)
        second_norm = TestRemoteMirrorsProcessor._normalize_url_for_comparison(second_mirror.url)

        # 4. Assertions
        assert first_mirror.enabled is True
        assert first_mirror.auth_method == "password"
        # Use substring matching (in) because cli_ui often adds prefixes like '* ' or ':: '
        expected_unchanged = f"Remote mirror '{first_norm}' remains unchanged"
        assert any(expected_unchanged in msg for msg in gitlabform_logs.debug), \
            f"Expected unchanged message not found. Captured: {gitlabform_logs.debug}"

        assert second_mirror.enabled is True
        assert second_mirror.auth_method == "password"
        assert second_mirror.keep_divergent_refs is False
        expected_updated = f"Updated remote mirror '{second_norm}'"
        assert any(expected_updated in msg for msg in gitlabform_logs.debug), \
            f"Expected update message not found. Captured: {gitlabform_logs.debug}"


    def test_remote_mirrors_update_credentials(self, project_for_function, root_username, root_access_token, gitlabform_logs: GitLabFormLogs):
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
            f"ssh://{root_username}@localhost/dummy/ssh_key_target.git"
        ]

        # 1. Setup initial mirrors directly via API
        # We manually create these so GitLabForm sees them as "already existing"
        for url in urls:
            project_for_function.remote_mirrors.create({
                "url": url,
                "enabled": True,
                # Simple logic to assign auth_method for setup
                "auth_method": "password" if "ssh://" not in url or ":" in url.split("@")[0] else "ssh_public_key"
            })

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
            assert any(expected_debug in msg for msg in gitlabform_logs.debug), \
                f"Expected update log not found for {norm}."
            
            # Check Info Log: Confirms the reminder was printed at the standard output level
            expected_info = f"!!! REMINDER: 'force_update' was used for mirror '{norm}'"
            assert any(expected_info in msg for msg in gitlabform_logs.info), \
                f"Expected info reminder not found for {norm}."

    def test_remote_mirror_http_password_auth_sync(self, project, mirror_urls, mirror_target_projects):
        """
        Test remote mirror functionality for http and password based authentication.
        This also tests configuration of `force_push` config key.

        This is validated by creating a new branch and a test file in the source project.
        Then run gitlabform with `force_push` enabled for the target mirror.
        Then check the target mirror repo if the new branch and the test file exists.
        """
        import time

        first_mirror_url_http_password_auth, _, _ = mirror_urls
        first_mirror_repo, _, _ = mirror_target_projects

        # In GitLab, default setting for branch protection is to deny force push.
        # For first mirror, we need to allow force push to the main branch, so that
        # we can validate the mirror functionality.
        first_mirror_repo_main_branch = first_mirror_repo.protectedbranches.get("main")
        first_mirror_repo_main_branch.allow_force_push = True
        first_mirror_repo_main_branch.save()

        # Create a test file in a new branch in the source project to validate mirror functionality
        # We use a unique branch name to ensure we are testing a fresh sync
        sync_branch_name = get_random_name("sync_test_branch")
        new_branch = project.branches.create({"branch": sync_branch_name, "ref": "main"})
        
        test_file_content = "This is a test file for remote mirror validation"
        test_file_path = f"mirror_test_{sync_branch_name}.txt"
        
        project.files.create(
            {
                "branch": new_branch.name,
                "file_path": test_file_path,
                "content": test_file_content,
                "commit_message": "Add test file for mirror validation",
            }
        )

        # Validate that the test file exists in the source project
        source_file = project.files.get(ref=new_branch.name, file_path=test_file_path)
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

    # def test_remote_mirrors_force_sync(self, gl, project, mirror_urls, mirror_target_projects):
    #     """Test creating multiple remote mirrors with different configurations and validate mirror functionality.
        
    #     This test verifies that gitlabform can create multiple remote mirrors
    #     with different types of URLs.
        
    #     The test validates that mirrors are not just created, but actually functional by:
    #     1. Creating a test file in the source project
    #     2. Using force_push to trigger a sync
    #     3. Verifying the file appears in the target/mirrored project
        
    #     Configuration follows GitLabForm's pattern where config keys match GitLab API parameters.
    #     URLs must have credentials embedded: https://username:password@host/path.git
    #     """
    #     import time
        
    #     target = project.path_with_namespace
    #     first_url_http, second_url_http, third_url_ssh = mirror_urls
    #     first_target_project, _, _ = mirror_target_projects

    #     # In GitLab, default setting for a branch protection is to deny force push.
    #     # For first mirror, we need to allow force push to the main branch, so that
    #     # we can validate the mirror functionality. That's why we need to allow force
    #     # push to the main branch.
    #     first_target_project_main_branch = first_target_project.protectedbranches.get("main")
    #     first_target_project_main_branch.allow_force_push = True
    #     first_target_project_main_branch.save()

    #     # Create a test file in the source project to validate mirror functionality
    #     # Create the test file in a new branch because the main branch is protected.
    #     # Default config for target project does not allow force push to the main branch.
    #     new_branch = project.branches.create({"branch": "test_branch", "ref": "main"})
    #     test_file_content = "This is a test file for remote mirror validation"
    #     test_file_path = "mirror_test.txt"
    #     project.files.create(
    #         {
    #             "branch": new_branch.name,
    #             "file_path": test_file_path,
    #             "content": test_file_content,
    #             "commit_message": "Add test file for mirror validation",
    #         }
    #     )

    #     # Validate that the test file exists in the source project
    #     source_file = project.files.get(ref=new_branch.name, file_path=test_file_path)
    #     assert source_file is not None
    #     assert source_file.decode().decode("utf-8") == test_file_content

    #     test_yaml = f"""
    #         projects_and_groups:
    #           {target}:
    #             remote_mirrors:
    #               {first_url_http}:
    #                 enabled: true
    #                 only_protected_branches: false
    #                 auth_method: password
    #                 force_push: true
    #               {second_url_http}:
    #                 enabled: true
    #                 only_protected_branches: true
    #                 auth_method: password
    #             #   {third_url_ssh}:
    #             #     enabled: false
    #             #     only_protected_branches: false
    #             #     auth_method: password
    #         """

    #     run_gitlabform(test_yaml, target)

    #     first_mirror = self._get_mirror_from_url(project, first_url_http)
    #     second_mirror = self._get_mirror_from_url(project, second_url_http)
    #     # third_mirror = self._get_mirror_from_url(project, third_url)

    #     if TYPE_CHECKING:
    #         assert isinstance(first_mirror, ProjectRemoteMirror)
    #         assert isinstance(second_mirror, ProjectRemoteMirror)
    #         # assert isinstance(third_mirror, ProjectRemoteMirror)
        
    #     mirrors = project.remote_mirrors.list(get_all=True)
    #     assert len(mirrors) == 2
        
    #     assert first_mirror is not None
    #     assert first_mirror.enabled is True
    #     assert first_mirror.only_protected_branches is False
        
    #     assert second_mirror is not None
    #     assert second_mirror.enabled is True
    #     assert second_mirror.only_protected_branches is True
        
    #     # assert third_mirror is not None
    #     # assert third_mirror.enabled is False
    #     # assert third_mirror.only_protected_branches is False
        
    #     # Validate mirror functionality: wait for sync and verify test file appears in target
    #     # The first mirror has force_push: true, so it should sync immediately
    #     # Wait a bit for the sync to complete
    #     time.sleep(30)
        
    #     # Refresh the target project to get latest state
    #     first_target_project = gl.projects.get(id = first_target_project.id)
    #     first_mirror = self._get_mirror_from_url(project, first_url_http)
    #     print("*****************************************************")
    #     print(f"First mirror: {first_mirror.asdict()}")
    #     print("*****************************************************")
    #     # Verify the test file exists in the target project (proving mirror works)
    #     try:
    #         target_file = first_target_project.files.get(ref=new_branch.name, file_path=test_file_path)
    #     except Exception as e:
    #         # If file doesn't exist, the mirror didn't work - fail the test
    #         raise AssertionError(
    #             f"Mirror validation failed: test file '{test_file_path}' not found in first mirror project. "
    #             f"This indicates the mirror is not functioning correctly. Error: {e}"
    #         )
    #     assert target_file.decode().decode("utf-8") == test_file_content

    # def test_remote_mirrors_update(self, caplog, gl, project, mirror_urls):
    #     """Test updating existing remote mirrors and verifying unchanged mirrors remain unchanged.
    #     
    #     This test verifies that:
    #     - Mirrors with changed configuration are updated
    #     - Mirrors with unchanged configuration remain unchanged (no unnecessary updates)
    #     - The update logic correctly detects configuration differences
    #     """
    #     first_url, second_url, third_url = mirror_urls
    #     target = project.path_with_namespace
    #     first_mirror = self._get_mirror_from_url(project, first_url)
    #     second_mirror = self._get_mirror_from_url(project, second_url)
    #     third_mirror = self._get_mirror_from_url(project, third_url)
    #
    #     update_yaml = f"""
    #         projects_and_groups:
    #           {target}:
    #             remote_mirrors:
    #               {first_url}:
    #                 enabled: false
    #                 only_protected_branches: true
    #               {second_url}:
    #                 enabled: true
    #                 only_protected_branches: true
    #               {third_url}:
    #                 enabled: true
    #                 only_protected_branches: false
    #         """
    #
    #     run_gitlabform(update_yaml, target)
    #     updated_first_mirror = self._get_mirror_from_url(project, first_url)
    #     updated_second_mirror = self._get_mirror_from_url(project, second_url)
    #     updated_third_mirror = self._get_mirror_from_url(project, third_url)
    #
    #     with caplog.at_level(logging.DEBUG):
    #         # The first mirror should be updated
    #         assert f"Updating remote mirror '{first_url}'" in caplog.text or \
    #                f"Remote mirror '{first_url}' remains unchanged" in caplog.text
    #         assert updated_first_mirror is not None
    #         assert updated_first_mirror.enabled is False
    #         assert updated_first_mirror.only_protected_branches is True
    #
    #         # The second mirror should remain unchanged (same config)
    #         assert f"Remote mirror '{second_url}' remains unchanged" in caplog.text
    #         assert updated_second_mirror is not None
    #         assert updated_second_mirror.enabled is True
    #         assert updated_second_mirror.only_protected_branches is True
    #
    #         # The third mirror should be updated
    #         assert f"Updating remote mirror '{third_url}'" in caplog.text or \
    #                f"Remote mirror '{third_url}' remains unchanged" in caplog.text
    #         assert updated_third_mirror is not None
    #         assert updated_third_mirror.enabled is True
    #         assert updated_third_mirror.only_protected_branches is False

    def test_remote_mirrors_delete(self, gl, project, mirror_urls, gitlabform_logs):
        """Test deleting remote mirrors using the delete flag.
        
        This test verifies that:
        - Mirrors can be deleted using the 'delete: true' configuration
        - Non-existent mirrors configured for deletion are handled gracefully
        - Other mirrors not marked for deletion remain intact
        """
        first_url, second_url, third_url = mirror_urls
        second_mirror_before_test = self._get_mirror_from_url(project, second_url)
        third_mirror_before_test = self._get_mirror_from_url(project, third_url)
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
        # with caplog.at_level(logging.DEBUG):
        #     assert f"Skip deleting remote mirror '{non_existent_mirror_url}', because it doesn't exist" in caplog.text
        expected = f"Skip deleting remote mirror '{TestRemoteMirrorsProcessor._normalize_url_for_comparison(non_existent_mirror_url)}', because it doesn't exist"
        assert any(expected in msg for msg in gitlabform_logs.debug), \
            f"Expected message not found. Captured: {gitlabform_logs.debug}"


    def test_remote_mirrors_enforce_false(self, gl, project, mirror_urls):
        """Test the additive behavior when enforce: false is set.
        
        This test verifies that:
        - When 'enforce: false' is set, mirrors not mentioned in the 
          configuration are NOT deleted (additive behavior).
        - Existing mirrors mentioned in the configuration are updated correctly.

        """
        target = project.path_with_namespace
        first_url, second_url, third_url = mirror_urls
        
        # 1. Normalize our target URLs from the fixture
        second_norm = self._normalize_url_for_comparison(second_url)
        third_norm = self._normalize_url_for_comparison(third_url)
    
        # 2. Verify starting state: 2nd and 3rd mirrors should exist 
        # (assuming they were left over from previous test setup)
        mirrors_before = [
            self._normalize_url_for_comparison(m.url) 
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
            self._normalize_url_for_comparison(m.url) 
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
            f"Mirror {third_norm} was deleted but it should have been kept "
            f"because enforce is set to false."
        )

    def test_remote_mirrors_enforce_true(self, gl, group, project, mirror_urls):
        """Test the destructive behavior when enforce: true is set.
        
        This test verifies that:
        - When 'enforce: true' is set, any mirror found in GitLab that is 
          NOT defined in the configuration is automatically deleted.
        """
        target = project.path_with_namespace
        first_url, second_url, third_url = mirror_urls
        
        # Normalize our target URLs
        second_norm = self._normalize_url_for_comparison(second_url)
        third_norm = self._normalize_url_for_comparison(third_url)
        
        # Ensure we are starting with both mirrors
        mirrors_before = [
            self._normalize_url_for_comparison(m.url) 
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
            self._normalize_url_for_comparison(m.url) 
            for m in project.remote_mirrors.list(get_all=True)
        ]

        # 3. Assertions
        # third_url should now be GONE because it wasn't in the YAML
        assert len(mirrors_after) == 1
        assert second_norm in mirrors_after
        assert third_norm not in mirrors_after, (
            f"Mirror {third_norm} should have been deleted by enforce: true logic."
        )

    def test_remote_mirrors_enforce_with_explicit_delete(self, project, mirror_urls):
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
            self._normalize_url_for_comparison(third_url)
        }
    
        # --- DIRECT SETUP PHASE (using python-gitlab) ---
        # Clear existing mirrors first to ensure a clean state
        for m in project.remote_mirrors.list(get_all=True):
            m.delete()

        # Create 3 mirrors directly using the raw URLs from the fixture
        for url in [first_url, second_url, third_url]:
             payload = {
                 'url': url,
                 'enabled': True,
             }
             
             # Detect auth method based on fixture URL format
             if "://" in url and ":" not in url.split("://")[1].split("@")[0]:
                 payload['auth_method'] = 'ssh_public_key'
             else:
                 payload['auth_method'] = 'password'
             
             project.remote_mirrors.create(payload)
        
        # --- VALIDATE SETUP ---
        # 2. Fetch ACTUAL mirrors from GitLab AFTER creation
        actual_mirrors_from_api = project.remote_mirrors.list(get_all=True)
        actual_norms = {
            self._normalize_url_for_comparison(m.url) 
            for m in actual_mirrors_from_api
        }

        # VALIDATION: Ensure every expected URL from our fixture exists in GitLab
        assert expected_norms == actual_norms, (
            f"Setup Mismatch! \nExpected: {expected_norms}\nActual: {actual_norms}"
        )
    
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
        final_norms = {
            self._normalize_url_for_comparison(m.url) 
            for m in final_mirrors
        }
        
        # Only the second mirror's normalized URL should remain.
        second_norm = self._normalize_url_for_comparison(second_url)
        assert final_norms == {second_norm}, f"Expected only {second_norm} to remain. Found: {final_norms}"