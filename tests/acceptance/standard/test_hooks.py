import logging
import pytest
from typing import TYPE_CHECKING
from gitlab.v4.objects import ProjectHook

from tests.acceptance import run_gitlabform, get_random_name


@pytest.fixture(scope="class")
def urls():
    first_name = get_random_name("hook")
    second_name = get_random_name("hook")
    third_name = get_random_name("hook")
    first_url = f"http://hooks/{first_name}.org"
    second_url = f"http://hooks/{second_name}.org"
    third_url = f"http://hooks/{third_name}.com"
    return first_url, second_url, third_url


class TestHooksProcessor:
    def get_hook_from_url(self, project, url):
        return next(h for h in project.hooks.list() if h.url == url)

    def test_hooks_create(self, gl, project, urls):
        target = project.path_with_namespace
        first_url, second_url, third_url = urls

        test_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {first_url}:
                    token: a1b2c3d4
                    push_events: false
                    merge_requests_events: true
                  {second_url}:
                    job_events: true
                    note_events: true
                  {third_url}:
                    token: abc123def
                    push_events: true
                    merge_requests_events: true
            """

        run_gitlabform(test_yaml, target)

        first_created_hook = self.get_hook_from_url(project, first_url)
        second_created_hook = self.get_hook_from_url(project, second_url)
        third_created_hook = self.get_hook_from_url(project, third_url)

        if TYPE_CHECKING:
            assert isinstance(first_created_hook, ProjectHook)
            assert isinstance(second_created_hook, ProjectHook)
            assert isinstance(third_created_hook, ProjectHook)
        assert len(project.hooks.list()) == 3
        assert (
            first_created_hook.push_events,
            first_created_hook.merge_requests_events,
        ) == (False, True)
        assert (second_created_hook.job_events, second_created_hook.note_events) == (
            True,
            True,
        )
        assert (
            third_created_hook.push_events,
            third_created_hook.merge_requests_events,
        ) == (True, True)

    def test_hooks_update(self, caplog, gl, project, urls):
        first_url, second_url, third_url = urls
        target = project.path_with_namespace
        first_hook = self.get_hook_from_url(project, first_url)
        second_hook = self.get_hook_from_url(project, second_url)
        third_hook = self.get_hook_from_url(project, third_url)

        update_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {first_url}:
                    token: a1b2c3d4
                    merge_requests_events: false
                    note_events: true
                  {second_url}:
                    job_events: true
                    note_events: true
                  {third_url}:
                    push_events: true
                    merge_requests_events: true
            """

        run_gitlabform(update_yaml, target)
        updated_first_hook = self.get_hook_from_url(project, first_url)
        updated_second_hook = self.get_hook_from_url(project, second_url)
        updated_third_hook = self.get_hook_from_url(project, third_url)

        assert updated_first_hook.asdict() != first_hook.asdict()
        # push_events stays False from previous test case config
        assert (
            updated_first_hook.push_events,
            updated_first_hook.merge_requests_events,
            updated_first_hook.note_events,
        ) == (False, False, True)

        # The second hook should remain unchanged.
        # The hook did not change from the previous test case. So, updating it is not necessary.
        assert updated_second_hook.asdict() == second_hook.asdict()
        assert (
            updated_second_hook.job_events,
            updated_second_hook.note_events,
        ) == (True, True)

        # The third hook should remain unchanged.
        # The hook initially had a token when it was created in previous test case.
        # In the current run/config the token is removed but all other configs remain same.
        # GitLabForm does not have memory or awareness of previous configs. So, comparing with
        # existing config in GitLab, the hook did not change and is not updated.
        assert updated_third_hook.asdict() == third_hook.asdict()
        assert (
            updated_third_hook.push_events,
            updated_third_hook.merge_requests_events,
        ) == (True, True)

    def test_hooks_delete(self, gl, project, urls, caplog):
        target = project.path_with_namespace
        first_url, second_url, third_url = urls
        second_hook_before_test = self.get_hook_from_url(project, second_url)
        third_hook_before_test = self.get_hook_from_url(project, third_url)
        non_existent_hook_url = f"https://unknown_{get_random_name('hook')}.com"

        delete_yaml = f"""
        projects_and_groups:
          {target}:
            hooks:
              {first_url}:
                delete: true
              {second_url}:
                job_events: false
                note_events: false
              {third_url}:
                token: abc123def
                push_events: true
                merge_requests_events: true
              {non_existent_hook_url}:
                delete: true
        """

        run_gitlabform(delete_yaml, target)
        hooks_after_test = project.hooks.list()
        second_hook_after_test = self.get_hook_from_url(project, second_url)
        third_hook_after_test = self.get_hook_from_url(project, third_url)

        assert len(hooks_after_test) == 2
        # The first hook should not exist as indicated by 'delete: true' config
        assert first_url not in (h.url for h in hooks_after_test)
        # The second hook should exist but updated as the config is different from
        # the setup in previous test case.
        assert second_hook_after_test in hooks_after_test
        assert second_hook_after_test.asdict() != second_hook_before_test.asdict()
        # The thrid hook should exist and same as it was setup in previous test case.
        assert third_hook_after_test in hooks_after_test
        assert third_hook_after_test.asdict() == third_hook_before_test.asdict()

    def test_hooks_enforce(self, gl, group, project, urls):
        target = project.path_with_namespace
        first_url, second_url, third_url = urls
        hooks_before_test = [h.url for h in project.hooks.list()]

        # Total number of hooks before the test should match the remaining
        # hooks at the end of previous test case.
        assert len(hooks_before_test) == 2

        enforce_yaml = f"""
                projects_and_groups:
                  {target}:
                    hooks:
                      enforce: true
                      {first_url}:
                        merge_requests_events: false
                        note_events: true
                """

        run_gitlabform(enforce_yaml, target)
        hooks_after_test = [h.url for h in project.hooks.list()]
        # Because of 'enforce: true' config, total number of hooks should be
        # what's in the applied config.
        assert len(hooks_after_test) == 1
        assert first_url in hooks_after_test
        assert second_url not in hooks_after_test
        assert third_url not in hooks_after_test

        not_enforce_yaml = f"""
                projects_and_groups:
                  {target}:
                    hooks:
                      enforce: false
                      http://www.newhook.org:
                        merge_requests_events: false
                        note_events: true
                """

        run_gitlabform(not_enforce_yaml, target)
        hooks_after_test = [h.url for h in project.hooks.list()]
        # Because of 'enforce: false', default config, total number of hooks should be
        # what's in the applied config and what was previously configured.
        assert len(hooks_after_test) == 2
        assert first_url in hooks_after_test and "http://www.newhook.org" in hooks_after_test

        parent_target = f"{group.path}/*"
        enforce_star_yaml = f"""
                projects_and_groups:
                  {parent_target}:
                    hooks:
                      enforce: true
                      {first_url}:
                        push_events: true
                  {target}:
                    hooks:
                      {second_url}:
                        job_events: true
                  """

        run_gitlabform(enforce_star_yaml, target)
        hooks_after_test = [h.url for h in project.hooks.list()]

        # Because 'enforce: true' config is in parent group, it will apply to all projects within the group.
        # So, the project being tested will contain only the hooks that are applied by the project and also
        # by the parent group config.
        assert len(hooks_after_test) == 2
        assert first_url in hooks_after_test and second_url in hooks_after_test
        assert "http://www.newhook.org" not in hooks_after_test

        enforce_delete_yaml = f"""
                projects_and_groups:
                  {target}:
                    hooks:
                      enforce: true
                      {first_url}:
                        delete: true
                """

        run_gitlabform(enforce_delete_yaml, target)
        hooks_after_test = [h.url for h in project.hooks.list()]

        # The 'enforce: true' config is set, which means only the hooks that are in the config
        # applied to the project, should exist. But, the only hook in the config is set to be
        # deleted. So, there should be no hooks remaining.
        assert len(hooks_after_test) == 0
