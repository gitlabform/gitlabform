import logging
import os
import pytest
from gitlabform.configuration import ConfigurationProjectsAndGroups


logger = logging.getLogger(__name__)


class TestConfigurationProjectsAndGroups:

    def test__get_effective_config_for_project__only_group_and_project__other_project(self):

        current_path = os.path.dirname(os.path.realpath(__file__))
        c = ConfigurationProjectsAndGroups(os.path.join(current_path, 'config_with_only_group_and_project.yaml'))

        x = c.get_effective_config_for_project('project_not_in_config/group_not_in_config')

        assert x == {}

    def test__get_effective_config_for_project__only_group_and_project__project_from_config__additive_project_settings(self):

        current_path = os.path.dirname(os.path.realpath(__file__))
        c = ConfigurationProjectsAndGroups(os.path.join(current_path, 'config_with_only_group_and_project.yaml'))

        x = c.get_effective_config_for_project('some_group/some_project')

        additive__project_settings = x['project_settings']

        # merged hashes from group and project levels
        assert additive__project_settings == {'foo': 'bar', 'bar': 'foo'}

    def test__get_effective_config_for_project__only_group_and_project__project_from_config__additive_hooks(self):

        current_path = os.path.dirname(os.path.realpath(__file__))
        c = ConfigurationProjectsAndGroups(os.path.join(current_path, 'config_with_only_group_and_project.yaml'))

        x = c.get_effective_config_for_project('some_group/some_project')

        additive__hooks = x['hooks']
        assert additive__hooks == {'a': {'foo': 'bar'}, 'b': {'bar': 'foo'}}  # added from both group and project level
