from tests.acceptance import run_gitlabform


class TestGroupSettings:
    def test__edit_settings(self, gitlab, group):
        settings = gitlab.get_group_settings(group)
        assert settings["description"] != "foobar"

        edit_group_settings = f"""
        projects_and_groups:
          {group}/*:
            group_settings:
              description: foobar
        """

        run_gitlabform(edit_group_settings, group)

        settings = gitlab.get_group_settings(group)
        assert settings["visibility"] == "internal"

    def test__no_edit_needed(self, gitlab, group):
        settings = gitlab.get_group_settings(group)
        current_value = settings["path"]

        edit_group_settings = f"""
            projects_and_groups:
              {group}/*:
                group_settings:
                  path: {current_value}
            """

        run_gitlabform(edit_group_settings, group)

        settings = gitlab.get_group_settings(group)
        assert settings["path"] == current_value

    def test__edit_new_setting(self, gitlab, project, group):

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
        assert settings["file_template_project_id"] == project_id
