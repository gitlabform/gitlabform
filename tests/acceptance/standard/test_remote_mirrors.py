import logging
import os
import pytest
from typing import TYPE_CHECKING
from gitlab.v4.objects import ProjectRemoteMirror

from tests.acceptance import run_gitlabform, get_random_name, create_project


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
        assert TestRemoteMirrorsProcessor._normalize_url_for_comparison(first_mirror.url) == TestRemoteMirrorsProcessor._normalize_url_for_comparison(first_mirror_url_http_password_auth)
        
        assert second_mirror is not None
        assert second_mirror.enabled is True
        assert TestRemoteMirrorsProcessor._normalize_url_for_comparison(second_mirror.url) == TestRemoteMirrorsProcessor._normalize_url_for_comparison(second_mirror_url_ssh_password_auth)
        
        assert third_mirror is not None
        assert third_mirror.enabled is False
        assert TestRemoteMirrorsProcessor._normalize_url_for_comparison(third_mirror.url) == TestRemoteMirrorsProcessor._normalize_url_for_comparison(third_mirror_url_ssh_public_key_auth)


    def test_remote_mirror_http_password_auth_sync(self, gl, project, mirror_urls, mirror_target_projects):
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
        first_mirror_repo_main_branch = first_mirror_repo.protectedbranches.get("main")
        first_mirror_repo_main_branch.allow_force_push = True
        first_mirror_repo_main_branch.save()

        # Create a test file in a new branch in the source project to validate mirror functionality
        new_branch = project.branches.create({"branch": "test_branch", "ref": "main"})
        test_file_content = "This is a test file for remote mirror validation"
        test_file_path = "mirror_test.txt"
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

        # Validate mirror functionality: wait for sync and verify test file appears in target
        # The first mirror has force_push: true, so it should sync immediately
        # Wait a bit for the sync to complete
        # time.sleep(30)
        
        # Refresh the target project to get latest state
        first_mirror_repo = gl.projects.get(id = first_mirror_repo.id)
        first_mirror = self._get_mirror_from_url(project, first_mirror_url_http_password_auth)
        print("*****************************************************")
        print(f"First mirror: {first_mirror.asdict()}")
        print("*****************************************************")
        # Verify the test file exists in the target project (proving mirror works)
        try:
            target_file = first_mirror_repo.files.get(ref=new_branch.name, file_path=test_file_path)
        except Exception as e:
            # If file doesn't exist, the mirror didn't work - fail the test
            print(f"Mirror sync failed. Error: {e}")
            raise AssertionError(
                f"Test file '{test_file_path}' not found in mirror project. "
                
            )
        assert target_file.decode().decode("utf-8") == test_file_content


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

    # def test_remote_mirrors_delete(self, gl, project, mirror_urls, caplog):
    #     """Test deleting remote mirrors using the delete flag.
    #     
    #     This test verifies that:
    #     - Mirrors can be deleted using the 'delete: true' configuration
    #     - Non-existent mirrors configured for deletion are handled gracefully
    #     - Other mirrors not marked for deletion remain intact
    #     """
    #     target = project.path_with_namespace
    #     first_url, second_url, third_url = mirror_urls
    #     second_mirror_before_test = self._get_mirror_from_url(project, second_url)
    #     third_mirror_before_test = self._get_mirror_from_url(project, third_url)
    #     non_existent_mirror_url = f"{os.getenv('GITLAB_URL', 'http://localhost').rstrip('/')}/non/existent_project.git"
    #
    #     delete_yaml = f"""
    #     projects_and_groups:
    #       {target}:
    #         remote_mirrors:
    #           {first_url}:
    #             delete: true
    #           {second_url}:
    #             enabled: true
    #             only_protected_branches: false
    #           {third_url}:
    #             enabled: true
    #             only_protected_branches: false
    #           {non_existent_mirror_url}:
    #             delete: true
    #     """
    #
    #     run_gitlabform(delete_yaml, target)
    #     mirrors_after_test = project.remote_mirrors.list(get_all=True)
    #     second_mirror_after_test = self._get_mirror_from_url(project, second_url)
    #     third_mirror_after_test = self._get_mirror_from_url(project, third_url)
    #
    #     assert len(mirrors_after_test) == 2
    #     # The first mirror should not exist as indicated by 'delete: true' config
    #     assert first_url not in (m.url for m in mirrors_after_test)
    #     # The second mirror should exist but updated as the config is different
    #     assert second_mirror_after_test is not None
    #     assert second_mirror_after_test in mirrors_after_test
    #     # The third mirror should exist and same as it was setup
    #     assert third_mirror_after_test is not None
    #     assert third_mirror_after_test in mirrors_after_test
    #     # The last mirror configured for deletion but it was never setup in gitlab.
    #     # Ensure expected error message is reported.
    #     with caplog.at_level(logging.DEBUG):
    #         assert f"Skip deleting remote mirror '{non_existent_mirror_url}', because it doesn't exist" in caplog.text

    # def test_remote_mirrors_enforce(self, gl, group, project, mirror_urls):
    #     """Test the enforce functionality for remote mirrors.
    #     
    #     This test verifies that:
    #     - When 'enforce: true' is set, only mirrors in the configuration exist
    #     - When 'enforce: false' is set, mirrors can accumulate (additive behavior)
    #     - Parent group enforce settings apply to child projects
    #     - Enforce works correctly with delete operations
    #     """
    #     target = project.path_with_namespace
    #     first_url, second_url, third_url = mirror_urls
    #     mirrors_before_test = [m.url for m in project.remote_mirrors.list(get_all=True)]
    #
    #     # Total number of mirrors before the test should match the remaining
    #     # mirrors at the end of previous test case.
    #     assert len(mirrors_before_test) == 2
    #
    #     enforce_yaml = f"""
    #             projects_and_groups:
    #               {target}:
    #                 remote_mirrors:
    #                   enforce: true
    #                   {first_url}:
    #                     enabled: true
    #                     only_protected_branches: false
    #             """
    #
    #     run_gitlabform(enforce_yaml, target)
    #     mirrors_after_test = [m.url for m in project.remote_mirrors.list(get_all=True)]
    #     # Because of 'enforce: true' config, total number of mirrors should be
    #     # what's in the applied config.
    #     assert len(mirrors_after_test) == 1
    #     assert first_url in mirrors_after_test
    #     assert second_url not in mirrors_after_test
    #     assert third_url not in mirrors_after_test
    #
    #     not_enforce_yaml = f"""
    #             projects_and_groups:
    #               {target}:
    #                 remote_mirrors:
    #                   enforce: false
    #                   {first_url}:
    #                     enabled: true
    #                     only_protected_branches: false
    #                   {second_url}:
    #                     enabled: true
    #                     only_protected_branches: true
    #             """
    #
    #     run_gitlabform(not_enforce_yaml, target)
    #     mirrors_after_test = [m.url for m in project.remote_mirrors.list(get_all=True)]
    #     # Because of 'enforce: false', default config, total number of mirrors should be
    #     # what's in the applied config and what was previously configured.
    #     assert len(mirrors_after_test) == 2
    #     assert first_url in mirrors_after_test and second_url in mirrors_after_test
    #
    #     parent_target = f"{group.path}/*"
    #     enforce_star_yaml = f"""
    #             projects_and_groups:
    #               {parent_target}:
    #                 remote_mirrors:
    #                   enforce: true
    #                   {first_url}:
    #                     enabled: true
    #                     only_protected_branches: false
    #               {target}:
    #                 remote_mirrors:
    #                   {second_url}:
    #                     enabled: true
    #                     only_protected_branches: true
    #               """
    #
    #     run_gitlabform(enforce_star_yaml, target)
    #     mirrors_after_test = [m.url for m in project.remote_mirrors.list(get_all=True)]
    #
    #     # Because 'enforce: true' config is in parent group, it will apply to all projects within the group.
    #     # So, the project being tested will contain only the mirrors that are applied by the project and also
    #     # by the parent group config.
    #     assert len(mirrors_after_test) == 2
    #     assert first_url in mirrors_after_test and second_url in mirrors_after_test
    #
    #     enforce_delete_yaml = f"""
    #             projects_and_groups:
    #               {target}:
    #                 remote_mirrors:
    #                   enforce: true
    #                   {first_url}:
    #                     delete: true
    #             """
    #
    #     run_gitlabform(enforce_delete_yaml, target)
    #     mirrors_after_test = [m.url for m in project.remote_mirrors.list(get_all=True)]
    #
    #     # The 'enforce: true' config is set, which means only the mirrors that are in the config
    #     # applied to the project, should exist. But, the only mirror in the config is set to be
    #     # deleted. So, there should be no mirrors remaining.
    #     assert len(mirrors_after_test) == 0
