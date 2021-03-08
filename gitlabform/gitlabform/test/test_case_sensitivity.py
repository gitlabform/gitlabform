import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    get_gitlab,
)

GROUP_NAME = "GroupNameWithVaryingCase"
PROJECT_NAME = "ProjectWithVaryingCase"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME


@pytest.fixture(scope="module")
def gitlab(request):
    gl = get_gitlab()

    gl.delete_group(GROUP_NAME)
    create_group(GROUP_NAME, "internal")
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    def fin():
        pass
        gl.delete_project(GROUP_AND_PROJECT_NAME)
        gl.delete_group(GROUP_NAME)

    request.addfinalizer(fin)
    return gl  # provide fixture value


config_with_different_case_group = """
    gitlab:
      api_version: 4
    
    group_settings:
      GROUPnameWITHvaryingCASE: # different case than defined above 
        project_settings:
          visibility: internal
"""

config_with_different_case_project = """
    gitlab:
      api_version: 4
    
    project_settings:
      GroupNameWithVaryingCase/projectwithvaryingcase: # different case than defined above 
        project_settings:
          visibility: internal
"""

config_with_different_case_duplicate_groups = """
    gitlab:
      api_version: 4
    
    group_settings:
      groupnamewithvaryingcase:
        project_settings:
          visibility: internal
      GROUPnameWITHvaryingCASE: # different case than defined above 
        project_settings:
          visibility: internal
"""

config_with_different_case_duplicate_projects = """
    gitlab:
      api_version: 4
    
    project_settings:
      GroupNameWithVaryingCase/projectwithvaryingcase:
        project_settings:
          visibility: internal
      GroupNameWithVaryingCase/ProjectWithVaryingCase:
        project_settings:
          visibility: internal
"""

config_with_different_case_duplicate_skip_groups = """
    gitlab:
      api_version: 4
    
    skip_groups:
      - groupnamewithvaryingcase
      - GROUPnameWITHvaryingCASE
"""

config_with_different_case_duplicate_skip_projects = """
    gitlab:
      api_version: 4
    
    skip_projects:
      - GroupNameWithVaryingCase/projectwithvaryingcase
      - GroupNameWithVaryingCase/ProjectWithVaryingCase
"""


class TestCaseSensitivitySettings:
    def test__config_with_different_case_group(self, gitlab):
        settings = gitlab.get_project_settings(GROUP_AND_PROJECT_NAME)
        assert settings["visibility"] == "private"

        gf = GitLabForm(
            config_string=config_with_different_case_group,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        settings = gitlab.get_project_settings(GROUP_AND_PROJECT_NAME)
        assert settings["visibility"] == "internal"

    def test__config_with_different_case_project(self, gitlab):
        settings = gitlab.get_project_settings(GROUP_AND_PROJECT_NAME)
        assert settings["visibility"] == "private"

        gf = GitLabForm(
            config_string=config_with_different_case_project,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        settings = gitlab.get_project_settings(GROUP_AND_PROJECT_NAME)
        assert settings["visibility"] == "internal"

    def test__config_with_different_case_duplicate_projects(self, gitlab):
        with pytest.raises(SystemExit):
            GitLabForm(
                config_string=config_with_different_case_duplicate_projects,
                project_or_group=GROUP_AND_PROJECT_NAME,
            )

    def test__config_with_different_case_duplicate_groups(self, gitlab):
        with pytest.raises(SystemExit):
            GitLabForm(
                config_string=config_with_different_case_duplicate_groups,
                project_or_group=GROUP_AND_PROJECT_NAME,
            )

    def test__config_with_different_case_duplicate_skip_groups(self, gitlab):
        with pytest.raises(SystemExit):
            GitLabForm(
                config_string=config_with_different_case_duplicate_skip_groups,
                project_or_group=GROUP_AND_PROJECT_NAME,
            )

    def test__config_with_different_case_duplicate_skip_projects(self, gitlab):
        with pytest.raises(SystemExit):
            GitLabForm(
                config_string=config_with_different_case_duplicate_skip_projects,
                project_or_group=GROUP_AND_PROJECT_NAME,
            )
