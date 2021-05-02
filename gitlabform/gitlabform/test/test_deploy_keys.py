import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    get_gitlab,
    GROUP_NAME,
)

PROJECT_NAME = "deploy_keys_project"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME
GROUP_AND_PROJECT_NAME2 = GROUP_NAME + "/" + PROJECT_NAME + "2"


@pytest.fixture(scope="module")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    for project_name in [PROJECT_NAME, PROJECT_NAME + "2"]:
        create_project_in_group(GROUP_NAME, project_name)

    def fin():
        for group_and_project_name in [GROUP_AND_PROJECT_NAME, GROUP_AND_PROJECT_NAME2]:
            deploys_keys_ids = [
                deploy_key["id"]
                for deploy_key in gl.get_deploy_keys(group_and_project_name)
            ]
            for deploys_keys_id in deploys_keys_ids:
                gl.delete_deploy_key(group_and_project_name, deploys_keys_id)

    request.addfinalizer(fin)
    return gl  # provide fixture value


deploy_key_to_all_projects = """
common_settings:
  deploy_keys:
    foobar:
      key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC6OxCCViSjh8QUKNOoGqhUqs4LLDMyq/7DYuvMJu5lXwECWp0wFGoLXzYWCT6WOAP+vccncOrlVfsr9VJzXxR1QZq+p3joW25nWgjEw/HCPI6fnU1vROImzxnvwLS3EEJpy64Jq0FFwjt8vKSuQshPysEBSUTf5t3omb166MGlZ+Y6/tOf/8/3zqmvb8OqNmhUtfwxfE5oX8Z8bBaGrkxHlmYyJ9UBpfeEcFt1GqfiONPgchJJ4OqCJKqd7H4DZOosT64kTqPXhca44EOxiKQviCthv7bO+r7VSFo5TVo60ikq/sTR9ifXnd3B9x3LV1qzHHLlmnP//xkKHIZGxfyhgwtdGNWhEtKPiXUzZv4/48WUJMmtpjznhuEgjnpiJL3x0+vJCStA6WG0MiozBlS80Y4XHbt3X3bvlNSqSo/GpnxlPTUx+Lj/ASI75JDym14+C8RdSFN4iKl5Qjz5xFq4eXke00AahFvjAAV5BT8Qrlyg/cbt1pfWKND1T5Fqh6c=
      title: foobar_key
      can_push: false
"""


class TestDeployKeys:
    def test__deploy_key_to_all_projects(self, gitlab):
        gf = GitLabForm(
            config_string=deploy_key_to_all_projects,
            project_or_group=GROUP_NAME,
        )
        gf.main()

        deploy_keys1 = gitlab.get_deploy_keys(GROUP_AND_PROJECT_NAME)
        assert len(deploy_keys1) == 1

        deploy_keys2 = gitlab.get_deploy_keys(GROUP_AND_PROJECT_NAME2)
        assert len(deploy_keys2) == 1
