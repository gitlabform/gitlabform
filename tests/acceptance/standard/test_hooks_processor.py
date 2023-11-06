import logging

from tests.acceptance import run_gitlabform, create_group, create_project


class TestHooksProcessor:
    def test_project_hooks_create_delete(self, gl, project, project_hook):
        target = project.path_with_namespace
        test_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {project_hook.url}:
                    push_events: {project_hook.push_events}
                    merge_requests_events: {project_hook.merge_requests_events}
            """

        run_gitlabform(test_yaml, target)

        created_hook = project.hooks.get(project_hook.id)
        assert project_hook == created_hook

        delete_yaml = f"""
        projects_and_groups:
            {target}:
              hooks:
                {created_hook.url}:
                  delete: true
        """

        run_gitlabform(delete_yaml, target)
        hooks = project.hooks.list()

        assert len(hooks) == 0

    def test_project_hooks_update(gl, project, project_hook):
        target = project.path_with_namespace
        test_yaml = f"""
            projects_and_groups:
              {target}:
                hooks:
                  {project_hook.url}:
                    push_events: {project_hook.push_events}
                    merge_requests_events: {project_hook.merge_requests_events}
            """

        original_hook = project.hooks.create(
            {
                "url": project_hook.url,
                "push_events": not project_hook.push_events,
                "merge_requests_events": not project_hook.merge_requests_events,
            }
        )
        project_hook.id = original_hook.id

        run_gitlabform(test_yaml, target, include_archived_projects=False)

        modified_hook = project.hooks.get(original_hook.id)

        assert modified_hook.asdict() != original_hook.asdict()
        assert modified_hook == project_hook

        modified_hook.delete()
