import logging
import json
import operator

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor


class EnvironmentsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("environments")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        logging.debug(
            "Environments BEFORE: %s",
            self.gitlab.get_all_environments(project_and_group),
        )
        e = self.gitlab.get_all_environments(project_and_group)
        for environment in sorted(configuration["environments"]):
            logging.info("Setting environment: %s", environment)
            data = configuration["environments"][environment]
            env = data["name"]

            if env in map(operator.itemgetter("name"), e):
                # env already defined - valid options are stop and delete
                if "stop" in data.keys() and data["stop"]:
                    # Stop environment
                    logging.info("Will stop %s.", env)
                    for x in e:
                        if x["name"] == env:
                            eid = x["id"]
                            self.gitlab.stop_environment(project_and_group, eid)
                            break

                if "delete" in data.keys() and data["delete"]:
                    # Request to delete env
                    logging.info("Will delete %s.", env)
                    for x in e:
                        if x["name"] == env:
                            eid = x["id"]
                            self.gitlab.stop_environment(project_and_group, eid)
                            self.gitlab.delete_environment(project_and_group, eid)
                            break
                else:
                    logging.info("Will not create %s as it is already defined.", env)
            else:
                # env does not exist so create it
                if (not "delete" in data.keys() or not data["delete"]) and (
                    not "stop" in data.keys() or not data["stop"]
                ):
                    # Create the environment env
                    logging.info("Will create the environment %s.", env)
                    self.gitlab.post_environment(project_and_group, data)
                else:
                    # env does not exist, and delete flag is true, or stop flag  is true so noop
                    logging.info(
                        "Will no create the environment %s because one or both of the delete and stop flags is true.",
                        env,
                    )
        logging.debug(
            "Environments AFTER: %s",
            self.gitlab.get_all_environments(project_and_group),
        )
