import logging.config

from gitlab import GitlabGetError

from gitlabform.gitlabform.core import if_in_config_and_not_skipped


class SecretVariables(object):

    @if_in_config_and_not_skipped
    def process_secret_variables(self, project_and_group, configuration):
        project = self.gl.projects.get(project_and_group)
        if project.builds_access_level == 'disabled':
            logging.warning("Builds disabled in this project so I can't set secret variables here.")
            return

        logging.debug("Secret variables BEFORE: %s", project.variables.list())
        for secret_variable_name in sorted(configuration['secret_variables']):
            secret_variable = configuration['secret_variables'][secret_variable_name]
            logging.info("Setting secret variable: %s", secret_variable)

            try:
                existing_variable = project.variables.get(secret_variable['key'])
                for key, value in secret_variable.items():
                    setattr(existing_variable, key, value)
                existing_variable.save()
            except GitlabGetError:  # doesn't exist yet
                project.variables.create(secret_variable)

        logging.debug("Secret variables AFTER: %s", project.variables.list())
