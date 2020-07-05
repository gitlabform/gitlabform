import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, get_gitlab, delete_variables_from_group, GROUP_NAME


@pytest.fixture(scope="function")
def gitlab(request):
    create_group(GROUP_NAME)

    gl = get_gitlab()

    def fin():
        delete_variables_from_group(GROUP_NAME, ['FOO', 'BAR'])

    request.addfinalizer(fin)
    return gl  # provide fixture value


config_single_secret_variable = """
gitlab:
  api_version: 4

group_settings:
  """ + GROUP_NAME + """:
    project_settings:
      builds_access_level: enabled
    group_secret_variables:
      foo:
        key: FOO
        value: 123
"""

config_single_secret_variable2 = """
gitlab:
  api_version: 4

group_settings:
  """ + GROUP_NAME + """:
    project_settings:
      builds_access_level: enabled
    group_secret_variables:
      foo:
        key: FOO
        value: 123456
"""

config_more_secret_variables = """
gitlab:
  api_version: 4

group_settings:
  """ + GROUP_NAME + """:
    project_settings:
      builds_access_level: enabled
    group_secret_variables:
      foo:
        key: FOO
        value: 123456
      bar:
        key: BAR
        value: bleble
"""


class TestGroupSecretVariables:

    def test__single_secret_variable(self, gitlab):
        gf = GitLabForm(config_string=config_single_secret_variable,
                        project_or_group=GROUP_NAME)
        gf.main()

        secret_variables = gitlab.get_group_secret_variables(GROUP_NAME)
        assert len(secret_variables) == 1

    def test__reset_single_secret_variable(self, gitlab):
        gf = GitLabForm(config_string=config_single_secret_variable,
                        project_or_group=GROUP_NAME)
        gf.main()

        secret_variables = gitlab.get_group_secret_variables(GROUP_NAME)
        assert len(secret_variables) == 1
        assert secret_variables[0]['value'] == '123'

        gf = GitLabForm(config_string=config_single_secret_variable2,
                        project_or_group=GROUP_NAME)
        gf.main()

        secret_variables = gitlab.get_group_secret_variables(GROUP_NAME)
        assert len(secret_variables) == 1
        assert secret_variables[0]['value'] == '123456'

    def test__more_secret_variables(self, gitlab):
        gf = GitLabForm(config_string=config_more_secret_variables,
                        project_or_group=GROUP_NAME)
        gf.main()

        secret_variables = gitlab.get_group_secret_variables(GROUP_NAME)
        secret_variables_keys = set([secret['key'] for secret in secret_variables])
        assert len(secret_variables) == 2
        assert secret_variables_keys == {'FOO', 'BAR'}
