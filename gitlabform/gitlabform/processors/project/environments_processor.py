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
        project_environments = self.gitlab.get_all_environments(project_and_group)
        logging.debug(
            "Environments BEFORE: %s", project_environments,
        )
        for environment in sorted(configuration["environments"]):
            logging.info("Selected environment: %s", environment)
            data = configuration["environments"][environment]
            env = data["name"]

            if env in map(operator.itemgetter("name"), project_environments):
                # env already defined - valid options are stop, delete, or update
                if ("new_name" in data.keys()) or ("new_external_url" in data.keys()):
                    # Request to update an existing environment
                    if (
                          ("stop" in data.keys() and data["stop"]) or
                          ("delete" in data.keys() and data["delete"])
                        ):
                        # Stop or delete is true, so do not update
                        logging.info("Not updating %s because STOP or DELETE requested", env)
                    else:
                        # Update the environment
                        logging.info("Will update %s.", env)
                        for x in project_environments:
                            if x["name"] == env:
                                data["id"] = x["id"]
                                try:
                                    # new_name may or may not be defined
                                    data["name"] = data["new_name"]
                                except:
                                    pass
                                try:
                                    # new_external_url may or may not be defined
                                    data["external_url"] = data["new_external_url"]
                                except:
                                    pass
                                self.gitlab.put_environment(project_and_group, data)
                                break

                if "stop" in data.keys() and data["stop"]:
                    # Stop environment
                    logging.info("Will stop %s.", env)
                    for x in project_environments:
                        if x["name"] == env:
                            eid = x["id"]
                            self.gitlab.stop_environment(project_and_group, eid)
                            break

                if "delete" in data.keys() and data["delete"]:
                    # Request to delete env
                    logging.info("Will delete %s.", env)
                    for x in project_environments:
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
