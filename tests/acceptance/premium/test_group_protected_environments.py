from typing import Any, List, cast

import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


def _list_group_protected_environments(gl, group) -> List[dict[str, Any]]:
    return cast(List[dict[str, Any]], gl.http_list(f"/groups/{group.id}/protected_environments", get_all=True))


class TestGroupProtectedEnvironments:
    def test__protect_a_group_environment(self, gl, group_for_function, subgroup_for_function):
        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_protected_environments:
              enforce: true
              production:
                deploy_access_levels:
                  - access_level: maintainer
                    group_inheritance_type: 0
                  - group: {subgroup_for_function.full_path}
          {subgroup_for_function.full_path}/*:
            group_protected_environments:
              skip: true
        """

        run_gitlabform(config, group_for_function)

        protected_envs = _list_group_protected_environments(gl, group_for_function)

        assert len(protected_envs) == 1
        assert protected_envs[0]["name"] == "production"
        assert len(protected_envs[0]["deploy_access_levels"]) == 2
        group_ids = [r["group_id"] for r in protected_envs[0]["deploy_access_levels"] if r.get("group_id")]
        assert group_ids == [subgroup_for_function.id]

    def test__update_group_protected_environment(self, gl, group_for_function):
        initial_config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_protected_environments:
              production:
                deploy_access_levels:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(initial_config, group_for_function)

        updated_config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_protected_environments:
              production:
                deploy_access_levels:
                  - access_level: {AccessLevel.DEVELOPER.value}
                approval_rules:
                  - access_level: {AccessLevel.MAINTAINER.value}
                    required_approvals: 1
        """

        run_gitlabform(updated_config, group_for_function)

        protected_envs = _list_group_protected_environments(gl, group_for_function)

        assert len(protected_envs) == 1
        assert protected_envs[0]["name"] == "production"
        assert protected_envs[0]["deploy_access_levels"][0]["access_level"] == AccessLevel.DEVELOPER.value
        assert len(protected_envs[0]["approval_rules"]) == 1
        assert protected_envs[0]["approval_rules"][0]["access_level"] == AccessLevel.MAINTAINER.value
        assert protected_envs[0]["approval_rules"][0]["required_approvals"] == 1

    def test__delete_and_enforce_group_protected_environments(self, gl, group_for_function):
        initial_config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_protected_environments:
              production:
                deploy_access_levels:
                  - access_level: maintainer
              staging:
                deploy_access_levels:
                  - access_level: developer
        """

        run_gitlabform(initial_config, group_for_function)
        assert len(_list_group_protected_environments(gl, group_for_function)) == 2

        enforce_config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_protected_environments:
              enforce: true
              production:
                deploy_access_levels:
                  - access_level: maintainer
        """

        run_gitlabform(enforce_config, group_for_function)

        protected_envs = _list_group_protected_environments(gl, group_for_function)
        assert [env["name"] for env in protected_envs] == ["production"]

        delete_config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_protected_environments:
              production:
                delete: true
        """

        run_gitlabform(delete_config, group_for_function)
        assert _list_group_protected_environments(gl, group_for_function) == []
