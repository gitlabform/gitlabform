from unittest.mock import MagicMock


from gitlabform import Configuration, GitLab, GroupsProvider, ProjectsProvider


def test__create_groups_and_projects_list() -> None:
    config_yaml = f"""
    projects_and_groups:
      group_to_create/*:
        create_if_not_found: true
        group_settings:
          suggestion_commit_message: 'foobar'
      group_to_create/project_to_create:
        create_if_not_found: true
        project_settings:
          suggestion_commit_message: 'foobar'
      group_to_create/subgroup_to_create/*:
        create_if_not_found: true
        group_settings:
          suggestion_commit_message: 'foobar'
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)
    gitlab_mock.get_group_case_insensitive = MagicMock(return_value={})
    gitlab_mock.get_group_id_case_insensitive = MagicMock(return_value="123")
    gitlab_mock.create_group = MagicMock(return_value=True)

    groups_provider = GroupsProvider(gitlab_mock, configuration)
    groups = groups_provider.get_groups("ALL_DEFINED")

    assert len(groups.requested) == 2

    gitlab_mock.get_project_case_insensitive = MagicMock(
        return_value={"archived": False}
    )
    gitlab_mock.create_project = MagicMock(return_value=True)
    projects_provider = ProjectsProvider(
        gitlab_mock, configuration, include_archived_projects=False
    )
    projects = projects_provider.get_projects("ALL_DEFINED")

    assert len(projects.requested) == 1
