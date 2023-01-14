import ez_yaml
from deepdiff import DeepDiff
from pprint import pprint
from unittest.mock import MagicMock

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    UserTransformer,
    GroupTransformer,
)
from gitlabform.gitlab import GitLab


def test__transform_for_merge_request_approvals() -> None:
    config_yaml = f"""
    projects_and_groups:

      "*":
        merge_requests_approval_rules:
          standard:
            approvals_required: 1
            name: "All eligible users"

      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            groups:
              - some_group
            users:
              - a_user
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)
    gitlab_mock._get_group_id = MagicMock(side_effect=[1])
    gitlab_mock._get_user_id = MagicMock(side_effect=[2])
    # gitlab_mock._get_branch_id = MagicMock(side_effect=[3])

    ut = UserTransformer(gitlab_mock)
    ut.transform(configuration)

    gt = GroupTransformer(gitlab_mock)
    gt.transform(configuration, last=True)

    # ut = UserTransformer(gitlab_mock)
    # ut.transform(configuration)

    effective_config_yaml_str = ez_yaml.to_string(obj=configuration.config, options={})
    print("!!!BEFORE:")
    print(effective_config_yaml_str)

    expected_transformed_config_yaml = f"""
    projects_and_groups:

      "*":
        merge_requests_approval_rules:
          standard:
            approvals_required: 1
            name: "All eligible users"

      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            group_ids:
              - 1
            user_ids:
              - 2
    """

    expected_transformed_config = Configuration(
        config_string=expected_transformed_config_yaml
    )

    ut.convert_to_simple_types(expected_transformed_config)

    effective_config_yaml_str = ez_yaml.to_string(
        obj=expected_transformed_config.config, options={}
    )
    print("!!!After:")
    print(effective_config_yaml_str)

    difference = DeepDiff(configuration.config, expected_transformed_config.config)
    assert not difference
