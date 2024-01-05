import logging
import pytest
from typing import TYPE_CHECKING

from tests.acceptance import run_gitlabform, get_random_name


LOGGER = logging.getLogger(__name__)


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
                    merge_requests_events: true
                  {second_url}:
                    job_events: true
                    note_events: true
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
        ) == (False, True)
        assert (second_created_hook.job_events, second_created_hook.note_events) == (
            True,
            True,
        )

    def test_hooks_update(self, caplog, gl, project, urls):
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
                    merge_requests_events: false
                    note_events: true
                  {second_url}:
                    job_events: true
                    note_events: true
            """

        run_gitlabform(update_yaml, target)
        updated_first_hook = self.get_hook_from_url(project, first_url)
        updated_second_hook = self.get_hook_from_url(project, second_url)

        with caplog.at_level(logging.DEBUG):
            assert f"Hook {second_url} remains unchanged" in caplog.text
            assert f"Changing existing hook '{first_url}'" in caplog.text
        assert updated_first_hook.asdict() != first_hook.asdict()
        assert updated_second_hook.asdict() == second_hook.asdict()
        # push events defaults to True, but it stays False
        assert updated_first_hook.push_events == False
        assert updated_first_hook.merge_requests_events == False
        assert updated_first_hook.note_events == True

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

    def test_hooks_enforce(self, gl, project, urls):
        target = project.path_with_namespace
        first_url, second_url = urls
        gl_hooks = project.hooks.list()
        assert len(gl_hooks) == 1
        assert second_url == gl_hooks[0].url

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
        gl_hook_urls = [h.url for h in project.hooks.list()]
        assert len(gl_hook_urls) == 1
        assert first_url in gl_hook_urls
        assert second_url not in gl_hook_urls
