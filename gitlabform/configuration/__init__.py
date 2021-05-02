from gitlabform.configuration.case_insensitive_project_and_groups import (
    ConfigurationCaseInsensitiveProjectsAndGroups,
)


# note that we are NOT using mixins here, but only the most advanced subclass


class Configuration(ConfigurationCaseInsensitiveProjectsAndGroups):
    pass
