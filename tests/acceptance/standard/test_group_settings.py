import logging

from tests.acceptance import run_gitlabform


class TestGroupSettings:
    def test__edit_settings(self, gl, group):
        assert group.description != "foobar"

        edit_group_settings = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              description: foobar
        """

        run_gitlabform(edit_group_settings, group)

        group = gl.groups.get(group.id)
        assert group.visibility == "internal"

    def test__no_edit_needed(self, gl, group):
        current_value = group.path

        edit_group_settings = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_settings:
                  path: {current_value}
            """

        run_gitlabform(edit_group_settings, group)

        group = gl.groups.get(group.id)
        assert group.path == current_value

    def test__dry_run_shows_diff_and_does_not_edit(self, gl, group_for_function, caplog):
        group = group_for_function
        original_description = group.description
        assert original_description != "foobar"

        edit_group_settings = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              description: foobar
        """

        with caplog.at_level(logging.INFO):
            run_gitlabform(edit_group_settings, group, noop=True)

        assert "group_settings changes" in caplog.text
        assert "foobar" in caplog.text

        group = gl.groups.get(group.id)
        assert group.description == original_description
