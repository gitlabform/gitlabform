import pytest

from tests.acceptance import run_gitlabform, gl


class TestGroupSettings:
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__edit_new_setting_premium(self, gitlab, project, group):

        project_id = gitlab._get_project_id(f"{group}/{project}")

        settings = gitlab.get_group_settings(group)
        assert "file_template_project_id" not in settings

        edit_group_settings = f"""
        projects_and_groups:
          {group}/*:
            group_settings:
              file_template_project_id: {project_id}
        """

        run_gitlabform(edit_group_settings, group)

        settings = gitlab.get_group_settings(group)
        # the type returned by the API is int, but in the _get_project_id we return str,
        # so we need a cast here
        assert settings["file_template_project_id"] == int(project_id)
