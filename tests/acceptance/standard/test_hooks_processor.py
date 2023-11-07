import logging
from typing import TYPE_CHECKING

from gitlab.v4.objects import ProjectHook

from tests.acceptance import run_gitlabform, get_random_name


class TestHooksProcessor:
    def project_hook(self, project):
        name = get_random_name("hook")
        hook = project.hooks.create({"url": f"http://hooks/{name}.org"})

        return hook

        # try:
        #     hook.delete()
        # except (GitlabDeleteError, GitlabHttpError) as e:
        #     if e.response_code == 404:
        #         pass

    def test_project_hooks_create_delete(self, gl, project):
        first_hook = self.project_hook(project)
        second_hook = self.project_hook(project)

        target = project.path_with_namespace
        test_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {first_hook.url}:
                    push_events: {first_hook.push_events}
                    merge_requests_events: {first_hook.merge_requests_events}
                  {second_hook.url}:
                    push_events: {second_hook.push_events}
                    merge_requests_events: {second_hook.merge_requests_events}
            """

        run_gitlabform(test_yaml, target)

        first_created_hook = project.hooks.get(first_hook.id)
        second_created_hook = project.hooks.get(second_hook.id)

        if TYPE_CHECKING:
            assert isinstance(first_created_hook, ProjectHook)
            assert isinstance(second_created_hook, ProjectHook)
        assert len(project.hooks.list()) == 2
        assert first_hook == first_created_hook
        assert second_hook == second_created_hook

        delete_yaml = f"""
        projects_and_groups:
            {target}:
              hooks:
                {first_hook.url}:
                  delete: true
        """

        run_gitlabform(delete_yaml, target)
        hooks = project.hooks.list()

        assert len(hooks) == 1
        assert first_hook not in hooks
        assert second_hook in hooks
        assert second_hook == second_created_hook

        second_hook.delete()

    def test_project_hooks_update(self, gl, project):
        project_hook = self.project_hook(project)
        target = project.path_with_namespace
        original_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {project_hook.url}:
                    push_events: {project_hook.push_events}
                    merge_requests_events: {project_hook.merge_requests_events}
            """

        run_gitlabform(original_yaml, target, include_archived_projects=False)
        original_hook = next(
            h for h in project.hooks.list() if h.url == project_hook.url
        )
        if TYPE_CHECKING:
            assert isinstance(original_hook, ProjectHook)

        update_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {project_hook.url}:
                    id: {original_hook.id}
                    push_events: {not project_hook.push_events}
                    merge_requests_events: {not project_hook.merge_requests_events}
            """

        run_gitlabform(update_yaml, target, include_archived_projects=False)
        modified_hook = next(
            h for h in project.hooks.list() if h.url == project_hook.url
        )

        if TYPE_CHECKING:
            assert isinstance(modified_hook, ProjectHook)
        assert modified_hook.asdict() != original_hook.asdict()
        assert modified_hook == project_hook

        modified_hook.delete()
