from deepdiff import DeepDiff
from unittest.mock import MagicMock, patch

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    GroupTransformer,
)
from gitlabform.gitlab import GitLab


def test__transform_for_merge_request_approvals() -> None:
    config_yaml = f"""
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            approvals_required: 1
            name: "Dev Code Review - UAT"
            groups: # this comment is needed...
              - a_group
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)
    
    # Mock the python-gitlab wrapper
    with patch('gitlabform.configuration.transform.GitlabWrapper') as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_group_id = MagicMock(side_effect=[123])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock
        
        transformer = GroupTransformer(gitlab_mock)
        transformer.transform(configuration, last=True)

        assert gl_mock.get_group_id.call_count == 1

    # effective_config_yaml_str = ez_yaml.to_string(obj=configuration.config, options={})
    # print("!!!")
    # print(effective_config_yaml_str)

    expected_transformed_config_yaml = f"""
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            approvals_required: 1
            name: "Dev Code Review - UAT"
            group_ids: # this comment is needed...
              - 123
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)
    transformer.convert_to_simple_types(expected_transformed_config)

    assert not DeepDiff(configuration.config, expected_transformed_config.config)
