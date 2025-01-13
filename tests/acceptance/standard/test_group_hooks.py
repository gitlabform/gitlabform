import logging
import pytest
from typing import TYPE_CHECKING
from gitlab.v4.objects import GroupHook

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


class TestGroupHooksProcessor:
    def get_hook_from_url(self, group, url):
        return next(h for h in group.hooks.list() if h.url == url)

    def test_hooks_create(self, gl, group, urls):
        first_url, second_url, third_url = urls

        test_yaml = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_hooks:
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

        run_gitlabform(test_yaml, group)

        first_created_hook = self.get_hook_from_url(group, first_url)
        second_created_hook = self.get_hook_from_url(group, second_url)
        third_created_hook = self.get_hook_from_url(group, third_url)

        if TYPE_CHECKING:
            assert isinstance(first_created_hook, GroupHook)
            assert isinstance(second_created_hook, GroupHook)
            assert isinstance(third_created_hook, GroupHook)
        assert len(group.hooks.list()) == 3
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

    def test_hooks_update(self, caplog, gl, group, urls):
        first_url, second_url, third_url = urls
        first_hook = self.get_hook_from_url(group, first_url)
        second_hook = self.get_hook_from_url(group, second_url)
        third_hook = self.get_hook_from_url(group, third_url)

        update_yaml = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_hooks:
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

        run_gitlabform(update_yaml, group)
        updated_first_hook = self.get_hook_from_url(group, first_url)
        updated_second_hook = self.get_hook_from_url(group, second_url)
        updated_third_hook = self.get_hook_from_url(group, third_url)

        with caplog.at_level(logging.DEBUG):
            # The first should be updated and be different than initial config done in previous test case.
            # The hook contains a token, which is a secret. So, cannot confirm whether it's different from
            # existing config in. This is why the hook is always updated. The hook's current config is also
            # different from when it was created in previous test case.
            assert f"Updating group hook '{first_url}'" in caplog.text
            assert updated_first_hook.asdict() != first_hook.asdict()
            # push_events stays False from previous test case config
            assert (
                updated_first_hook.push_events,
                updated_first_hook.merge_requests_events,
                updated_first_hook.note_events,
            ) == (False, False, True)

            # The second hook should remain unchanged.
            # The hook did not change from the previous test case. So, updating it is not necessary.
            assert f"Group hook '{second_url}' remains unchanged" in caplog.text
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
            assert f"Group hook '{third_url}' remains unchanged" in caplog.text
            assert updated_third_hook.asdict() == third_hook.asdict()
            assert (
                updated_third_hook.push_events,
                updated_third_hook.merge_requests_events,
            ) == (True, True)

    def test_hooks_delete(self, gl, group, urls, caplog):
        first_url, second_url, third_url = urls
        second_hook_before_test = self.get_hook_from_url(group, second_url)
        third_hook_before_test = self.get_hook_from_url(group, third_url)
        non_existent_hook_url = f"https://unknown_{get_random_name('hook')}.com"

        delete_yaml = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_hooks:
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

        run_gitlabform(delete_yaml, group)
        hooks_after_test = group.hooks.list()
        second_hook_after_test = self.get_hook_from_url(group, second_url)
        third_hook_after_test = self.get_hook_from_url(group, third_url)

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
        # The last hook configured for deletion but it was never setup in gitlab.
        # Ensure expected error message is reported.
        with caplog.at_level(logging.DEBUG):
            assert (
                f"Not deleting group hook '{non_existent_hook_url}', because it doesn't exist"
                in caplog.text
            )

    def test_hooks_enforce(self, gl, group, urls):
        first_url, second_url, third_url = urls
        hooks_before_test = [h.url for h in group.hooks.list()]

        # Total number of hooks before the test should match the remaining
        # hooks at the end of previous test case.
        assert len(hooks_before_test) == 2

        enforce_yaml = f"""
                projects_and_groups:
                  {group.full_path}/*:
                    group_hooks:
                      enforce: true
                      {first_url}:
                        merge_requests_events: false
                        note_events: true
                """

        run_gitlabform(enforce_yaml, group)
        hooks_after_test = [h.url for h in group.hooks.list()]
        # Because of 'enforce: true' config, total number of hooks should be
        # what's in the applied config.
        assert len(hooks_after_test) == 1
        assert first_url in hooks_after_test
        assert second_url not in hooks_after_test
        assert third_url not in hooks_after_test

        not_enforce_yaml = f"""
                projects_and_groups:
                  {group.full_path}/*:
                    group_hooks:
                      enforce: false
                      http://www.newhook.org:
                        merge_requests_events: false
                        note_events: true
                """

        run_gitlabform(not_enforce_yaml, group)
        hooks_after_test = [h.url for h in group.hooks.list()]
        # Because of 'enforce: false', default config, total number of hooks should be
        # what's in the applied config and what was previously configured.
        assert len(hooks_after_test) == 2
        assert (
            first_url in hooks_after_test
            and "http://www.newhook.org" in hooks_after_test
        )

        enforce_delete_yaml = f"""
                projects_and_groups:
                  {group.full_path}/*:
                    group_hooks:
                      enforce: true
                      {first_url}:
                        delete: true
                """

        run_gitlabform(enforce_delete_yaml, group)
        hooks_after_test = [h.url for h in group.hooks.list()]

        # The 'enforce: true' config is set, which means only the hooks that are in the config
        # applied to the project, should exist. But, the only hook in the config is set to be
        # deleted. So, there should be no hooks remaining.
        assert len(hooks_after_test) == 0
