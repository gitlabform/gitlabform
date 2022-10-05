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
