from logging import debug
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlab.v4.objects.projects import Project
from gitlab.exceptions import GitlabGetError, GitlabParsingError


class ProjectPushRulesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_push_rules", gitlab)

    def _process_configuration(self, project_path: str, configuration: dict):
        configured_project_push_rules = configuration.get("project_push_rules", {})
        project: Project = self.gl.get_project_by_path_cached(project_path)

        try:
            existing_push_rules = project.pushrules.get()
        except GitlabGetError as e:
            if e.response_code == 404:
                debug(
                    f"No existing push rules for '{project.name}', creating new push rules."
                )
                self.create_project_push_rules(project, configured_project_push_rules)
                return
        except GitlabParsingError as e:
            # Known issue from GitLab API when project push rule has never been configured.
            # In that scenario, the API returns `null` instead of an appropriate message
            # and error code.
            # See GitLab issue : https://gitlab.com/gitlab-org/gitlab/-/issues/513331
            # Until the issue is resolved, we will assume push rule is not configured.
            # When the above issue is resolved, this exception block can be removed.

            debug(
                f"Cannot determine if push rule is currently configured for '{project.name}', attempting to create new push rules."
            )
            self.create_project_push_rules(project, configured_project_push_rules)
            return

        if self._needs_update(
            existing_push_rules.asdict(), configured_project_push_rules
        ):
            self.update_push_rules(existing_push_rules, configured_project_push_rules)
        else:
            debug("No update needed for Project Push Rules")

    @staticmethod
    def update_push_rules(push_rules, configured_project_push_rules: dict):
        for key, value in configured_project_push_rules.items():
            debug(f"Updating setting {key} to value {value}")
            setattr(push_rules, key, value)
        push_rules.save()

    @staticmethod
    def create_project_push_rules(project, push_rules_config: dict):
        debug(f"Creating push rules with configuration: {push_rules_config}")
        project.pushrules.create(push_rules_config)
