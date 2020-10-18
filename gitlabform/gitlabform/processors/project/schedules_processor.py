import logging
from typing import Dict, List

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor


class SchedulesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("schedules")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        existing_schedules = self.gitlab.get_all_pipeline_schedules(project_and_group)
        schedule_ids_by_description = self.__group_schedule_ids_by_description(
            existing_schedules
        )

        for schedule_description in sorted(configuration["schedules"]):
            schedule_ids = schedule_ids_by_description.get(schedule_description)
            if configuration.get("schedules|" + schedule_description + "|delete"):
                if schedule_ids:
                    logging.debug(
                        "Deleting pipeline schedules '%s'", schedule_description
                    )
                    for schedule_id in schedule_ids:
                        self.gitlab.delete_pipeline_schedule(
                            project_and_group, schedule_id
                        )
                else:
                    logging.debug(
                        "Not deleting pipeline schedules '%s', because none exist",
                        schedule_description,
                    )
            else:
                if schedule_ids and len(schedule_ids) == 1:
                    logging.debug(
                        "Changing existing pipeline schedule '%s'", schedule_description
                    )

                    updated_schedule = self.gitlab.update_pipeline_schedule(
                        project_and_group,
                        schedule_ids[0],
                        configuration.get("schedules|" + schedule_description),
                    )
                    self.gitlab.take_ownership(
                        project_and_group, updated_schedule["id"]
                    )
                    self.__set_schedule_variables(
                        project_and_group,
                        updated_schedule.get("id"),
                        configuration.get(
                            "schedules|" + schedule_description + "|variables"
                        ),
                    )
                elif schedule_ids:
                    logging.debug(
                        "Replacing existing pipeline schedules '%s'",
                        schedule_description,
                    )
                    for schedule_id in schedule_ids:
                        self.gitlab.delete_pipeline_schedule(
                            project_and_group, schedule_id
                        )
                    self.create_schedule_with_variables(
                        configuration, project_and_group, schedule_description
                    )
                else:
                    logging.debug(
                        "Creating pipeline schedule '%s'", schedule_description
                    )
                    self.create_schedule_with_variables(
                        configuration, project_and_group, schedule_description
                    )

    def create_schedule_with_variables(
        self, configuration, project_and_group, schedule_description
    ):
        data = configuration.get("schedules|" + schedule_description)
        created_schedule = self.gitlab.create_pipeline_schedule(
            project_and_group,
            schedule_description,
            data.get("ref"),
            data.get("cron"),
            optional_data=data,
        )
        self.__set_schedule_variables(
            project_and_group,
            created_schedule.get("id"),
            configuration.get("schedules|" + schedule_description + "|variables"),
        )

    def __set_schedule_variables(self, project_and_group, schedule_id, variables):
        schedule = self.gitlab.get_pipeline_schedule(project_and_group, schedule_id)

        existing_variables = schedule.get("variables")
        if existing_variables:
            logging.debug(
                "Deleting variables for pipeline schedule '%s'", schedule["description"]
            )

            for variable in existing_variables:
                self.gitlab.delete_pipeline_schedule_variable(
                    project_and_group, schedule_id, variable.get("key")
                )

        for variable_key, variable_data in variables.items():
            self.gitlab.create_pipeline_schedule_variable(
                project_and_group,
                schedule_id,
                variable_key,
                variable_data.get("value"),
                variable_data,
            )

    @staticmethod
    def __group_schedule_ids_by_description(schedules) -> Dict[str, List[str]]:
        schedule_ids_by_description: Dict[str, List[str]] = {}

        for schedule in schedules:
            description = schedule["description"]
            schedule_ids_by_description.setdefault(description, []).append(
                schedule["id"]
            )

        return schedule_ids_by_description
