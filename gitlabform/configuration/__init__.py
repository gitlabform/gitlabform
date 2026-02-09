from gitlabform.configuration.common import ConfigurationCommon
from gitlabform.configuration.groups import ConfigurationGroups
from gitlabform.configuration.projects import ConfigurationProjects

#
# This the only external interface for operating on the configuration from a given YAML file
# (or an input string in case of tests).
#


class Configuration(ConfigurationProjects):
    pass
