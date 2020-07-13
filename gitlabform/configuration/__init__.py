from gitlabform import Singleton
from gitlabform.configuration.projects_and_groups import ConfigurationProjectsAndGroups


class Configuration(ConfigurationProjectsAndGroups, metaclass=Singleton):
    pass
