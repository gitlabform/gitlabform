import pytest
from typing import TYPE_CHECKING

from tests.acceptance import run_gitlabform, get_random_name


@pytest.fixture(scope="class")
def urls():
    first_name = get_random_name("hook")
    second_name = get_random_name("hook")
    first_url = f"http://hooks/{first_name}.org"
    second_url = f"http://hooks/{second_name}.org"
    return first_url, second_url


class TestHooksProcessor:
    def get_hook_from_url(self, project, url):
        return next(h for h in project.hooks.list() if h.url == url)

    def test_hooks_create(self, gl, project, urls):
        target = project.path_with_namespace
        first_url, second_url = urls

        test_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {first_url}:
                    push_events: false
                    merge_requests_events: false
                  {second_url}:
                    job_events: false
                    note_events: false
            """

        run_gitlabform(test_yaml, target)

        first_created_hook = self.get_hook_from_url(project, first_url)
        second_created_hook = self.get_hook_from_url(project, second_url)
        if TYPE_CHECKING:
            assert isinstance(first_created_hook, ProjectHook)
            assert isinstance(second_created_hook, ProjectHook)
        assert len(project.hooks.list()) == 2
        assert (
            first_created_hook.push_events,
            first_created_hook.merge_requests_events,
        ) == (False, False)
        assert (second_created_hook.job_events, second_created_hook.note_events) == (
            False,
            False,
        )

    def test_hooks_update(self, gl, project, urls):
        first_url, second_url = urls
        target = project.path_with_namespace
        first_hook = self.get_hook_from_url(project, first_url)
        second_hook = self.get_hook_from_url(project, second_url)

        update_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {first_url}:
                    id: {first_hook.id}
                    push_events: true
                    merge_requests_events: true
            """

        run_gitlabform(update_yaml, target)
        modified_hook = self.get_hook_from_url(project, first_url)
        unchanged_hook = self.get_hook_from_url(project, second_url)

        assert modified_hook.asdict() != first_hook.asdict()
        assert unchanged_hook.asdict() == second_hook.asdict()
        assert modified_hook.push_events == True
        assert modified_hook.merge_requests_events == True

    def test_hooks_delete(self, gl, project, urls):
        target = project.path_with_namespace
        first_url, second_url = urls
        orig_second_hook = self.get_hook_from_url(project, second_url)

        delete_yaml = f"""
        projects_and_groups:
          {target}:
            hooks:
              {first_url}:
                delete: true
              {second_url}:
                job_events: false
                note_events: false
        """

        run_gitlabform(delete_yaml, target)
        hooks = project.hooks.list()
        second_hook = self.get_hook_from_url(project, second_url)

        assert len(hooks) == 1
        assert first_url not in (h.url for h in hooks)
        assert second_hook in hooks
        assert second_hook == orig_second_hook
