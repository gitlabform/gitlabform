import pytest

from gitlabform.configuration import Configuration


def test__config_with_different_case_group():
    group_name_with_varying_case = "GROUPnameWITHvaryingCASE"
    config_yaml = f"""
    projects_and_groups:
      {group_name_with_varying_case}/*: 
        project_settings:
          visibility: internal
    """
    configuration = Configuration(config_string=config_yaml)

    group_name_with_other_case = group_name_with_varying_case.lower()

    effective_configuration = configuration.get_effective_config_for_group(
        group_name_with_other_case
    )

    assert effective_configuration["project_settings"] == {"visibility": "internal"}


def test__config_with_different_case_project():
    group_and_project_name_with_varying_case = (
        "GroupNameWithVaryingCase/projectwithvaryingcase"
    )
    config_yaml = f"""
    projects_and_groups:
      {group_and_project_name_with_varying_case}: 
        project_settings:
          visibility: public
    """
    configuration = Configuration(config_string=config_yaml)

    group_and_project_name_with_other_case = (
        group_and_project_name_with_varying_case.upper()
    )

    effective_configuration = configuration.get_effective_config_for_project(
        group_and_project_name_with_other_case
    )

    assert effective_configuration["project_settings"] == {"visibility": "public"}


def test__config_with_different_case_duplicate_groups():
    config_yaml = """
    projects_and_groups:
      groupnamewithvaryingcase/*:
        project_settings:
          visibility: internal
      GROUPnameWITHvaryingCASE/*: # different case than defined above 
        project_settings:
          visibility: public
    """

    with pytest.raises(SystemExit):
        Configuration(config_string=config_yaml)


def test__config_with_different_case_duplicate_projects():
    config_yaml = """
    projects_and_groups:
      GroupNameWithVaryingCase/projectwithvaryingcase:
        project_settings:
          visibility: internal
      GroupNameWithVaryingCase/ProjectWithVaryingCase:
        project_settings:
          visibility: public
    """

    with pytest.raises(SystemExit):
        Configuration(config_string=config_yaml)


def test__config_with_different_case_duplicate_skip_groups():
    config_yaml = """
    skip_groups:
      - groupnamewithvaryingcase
      - GROUPnameWITHvaryingCASE
    """

    with pytest.raises(SystemExit):
        Configuration(config_string=config_yaml)


def test__config_with_different_case_duplicate_skip_projects():
    config_yaml = """
    skip_projects:
      - GroupNameWithVaryingCase/projectwithvaryingcase
      - GroupNameWithVaryingCase/ProjectWithVaryingCase
    """

    with pytest.raises(SystemExit):
        Configuration(config_string=config_yaml)
