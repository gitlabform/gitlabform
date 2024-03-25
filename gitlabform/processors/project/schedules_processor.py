from logging import debug
from typing import Dict, List

from gitlab.base import RESTObjectList, RESTObject
from gitlab.v4.objects import Project, ProjectPipelineSchedule

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class SchedulesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("schedules", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        configured_schedules = configuration.get("schedules", {})

        enforce_schedules = configuration.get("schedules|enforce", False)

        # Remove 'enforce' key from the config so that it's not treated as a "schedule"
        if enforce_schedules:
            configured_schedules.pop("enforce")

        project: Project = self.gl.projects.get(project_and_group)
        existing_schedules: List[
            RESTObject
        ] | RESTObjectList = project.pipelineschedules.list()

        schedule_ids_by_description: dict = self._group_schedule_ids_by_description(
            existing_schedules
        )

        for schedule_description in sorted(configured_schedules):
            schedule_ids = schedule_ids_by_description.get(schedule_description)

            if configured_schedules[schedule_description].get("delete"):
                if schedule_ids:
                    debug("Deleting pipeline schedules '%s'", schedule_description)
                    for schedule_id in schedule_ids:
                        project.pipelineschedules.get(schedule_id).delete()
                else:
                    debug(
                        "Not deleting pipeline schedules '%s', because none exist",
                        schedule_description,
                    )
            else:
                if schedule_ids and len(schedule_ids) == 1:
                    debug(
                        "Changing existing pipeline schedule '%s'", schedule_description
                    )
                    schedule = project.pipelineschedules.get(schedule_ids[0])
                    self._update_existing_schedule(
                        configured_schedules, project, schedule, schedule_description
                    )
                elif schedule_ids:
                    debug(
                        "Replacing existing pipeline schedules '%s'",
                        schedule_description,
                    )
                    for schedule_id in schedule_ids:
                        project.pipelineschedules.get(schedule_id).delete()

                    self._create_schedule_with_variables(
                        configured_schedules, project, schedule_description
                    )
                else:
                    debug("Creating pipeline schedule '%s'", schedule_description)
                    self._create_schedule_with_variables(
                        configured_schedules, project, schedule_description
                    )

        if enforce_schedules:
            debug("Delete unconfigured schedules because enforce is enabled")

            self._delete_schedules_no_longer_in_config(
                configured_schedules, existing_schedules, project
            )

    def _update_existing_schedule(
        self,
        configured_schedules,
        project: Project,
        schedule: ProjectPipelineSchedule,
        schedule_description: str,
    ):
        entity_config = configured_schedules[schedule_description]
        if self._needs_update(entity_config, schedule.asdict()):
            # Delete and then re-create schedule so we can pass all info in the data to Gitlab in case their APIs change
            project.pipelineschedules.delete(schedule.id)

            self._create_schedule_with_variables(
                configured_schedules, project, schedule_description
            )

    def _create_schedule_with_variables(
        self, configured_schedules, project: Project, schedule_description: str
    ):
        data = configured_schedules[schedule_description]

        schedule_data = {"description": schedule_description, **data}
        debug("Creating pipeline schedule using data: '%s'", schedule_data)

        created_schedule_id = project.pipelineschedules.create(schedule_data).id
        created_schedule = project.pipelineschedules.get(created_schedule_id)

        self._set_schedule_variables(
            created_schedule,
            data.get("variables"),
        )

        created_schedule.save()

    @staticmethod
    def _set_schedule_variables(schedule: ProjectPipelineSchedule, variables):
        attributes = schedule.attributes
        existing_variables = attributes.get("variables")
        if existing_variables:
            debug("Deleting variables for pipeline schedule '%s'", schedule.description)

            for variable in existing_variables:
                schedule.variables.delete(variable.get("key"))

        if variables:
            for variable_key, variable_data in variables.items():
                variable_type = variable_data.get("variable_type")
                if variable_type:
                    schedule.variables.create(
                        {
                            "key": variable_key,
                            "value": variable_data.get("value"),
                            "variable_type": variable_data.get("variable_type"),
                        }
                    )
                else:
                    schedule.variables.create(
                        {
                            "key": variable_key,
                            "value": variable_data.get("value"),
                        }
                    )

    # schedules: List[ProjectPipelineSchedule] | RESTObjectList -> Incompatible with python 3.9
    @staticmethod
    def _group_schedule_ids_by_description(
        schedules,
    ) -> Dict[str, List[str]]:
        schedule_ids_by_description: Dict[str, List[str]] = {}

        for schedule in schedules:
            schedule_ids_by_description.setdefault(schedule.description, []).append(
                schedule.id
            )

        return schedule_ids_by_description

    @staticmethod
    def _delete_schedules_no_longer_in_config(
        configured_schedules: Dict, existing_schedules, project: Project
    ) -> None:
        schedule: ProjectPipelineSchedule
        for schedule in existing_schedules:
            schedule_description = schedule.description
            schedule_id = schedule.id

            debug(f"processing {schedule_id}: {schedule_description}")
            if schedule_description not in configured_schedules:
                debug(
                    "Deleting pipeline schedule named '%s', because it is not in gitlabform configuration",
                    schedule_description,
                )
                project.pipelineschedules.get(schedule_id).delete()
