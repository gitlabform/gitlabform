import logging
import os

from gitlabform.configuration import ConfigurationProjectsAndGroups

logger = logging.getLogger(__name__)


class TestConfigurationProjectsAndGroups:

    def test__get_effective_config_for_project__only_group_and_project__other_project(self):

        current_path = os.path.dirname(os.path.realpath(__file__))
        c = ConfigurationProjectsAndGroups(os.path.join(current_path, 'config_with_only_group_and_project.yaml'))

        x = c.get_effective_config_for_project('project_not_in_config/group_not_in_config')

        assert x == {}
