import pytest

from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


class TestGroupSettings:
    def test__can_set_gitlab_duo_flags(self, gl, project, group, subgroup, other_subgroup):
        instance_settings = gl.settings.get()
        instance_settings.duo_features_enabled = True
        instance_settings.save()

        edit_group_settings = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              duo_availability: default_off
          {subgroup.full_path}/*:
            group_settings:
              duo_features_enabled: true
          {other_subgroup.full_path}/*:
            group_settings:
              lfs_enabled: true
        """

        run_gitlabform(edit_group_settings, group)

        refreshed_group = gl.groups.get(group.id)
        assert refreshed_group.duo_features_enabled is False
        # Despite: https://docs.gitlab.com/api/groups/#get-a-single-group stating duo_availability is returned by the API
        # it is not... https://gitlab.com/gitlab-org/gitlab/-/issues/572223
        # assert refreshed_group.duo_availability is "default_off"

        refreshed_subgroup = gl.groups.get(subgroup.id)
        assert refreshed_subgroup.duo_features_enabled is True

        refreshed_other_subgroup = gl.groups.get(other_subgroup.id)
        # parent group setting has duo_availability as "default_off" so shouldn't be enabled since not explicitly set
        assert refreshed_other_subgroup.duo_features_enabled is False

        instance_settings = gl.settings.get()
        instance_settings.duo_features_enabled = False
        instance_settings.save()
