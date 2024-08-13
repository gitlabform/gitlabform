import random
import re
from logging import debug
from typing import Dict, List

from gitlab.base import RESTObjectList, RESTObject
from gitlab.v4.objects import Project, ProjectPipelineSchedule

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class SchedulesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("schedules", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_schedules = configuration.get("schedules", {})

        enforce_schedules = configuration.get("schedules|enforce", False)

        # Remove 'enforce' key from the config so that it's not treated as a "schedule"
        if enforce_schedules:
            configured_schedules.pop("enforce")

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_schedules: List[RESTObject] | RESTObjectList = (
            project.pipelineschedules.list(get_all=True)
        )

        schedule_ids_by_description: Dict = self._group_schedule_ids_by_description(
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
                entity_config = configured_schedules[schedule_description]

                if schedule_ids and len(schedule_ids) == 1:
                    schedule = project.pipelineschedules.get(schedule_ids[0])
                    self._update_existing_schedule(
                        entity_config, project, schedule, schedule_description
                    )
                elif schedule_ids:
                    debug(
                        "Replacing existing pipeline schedules '%s'",
                        schedule_description,
                    )
                    for schedule_id in schedule_ids:
                        project.pipelineschedules.get(schedule_id).delete()

                    self._create_schedule_with_variables(
                        entity_config, project, schedule_description
                    )
                else:
                    debug("Creating pipeline schedule '%s'", schedule_description)
                    self._create_schedule_with_variables(
                        entity_config, project, schedule_description
                    )

        if enforce_schedules:
            debug("Delete unconfigured schedules because enforce is enabled")

            self._delete_schedules_no_longer_in_config(
                configured_schedules, existing_schedules, project
            )

    def _update_existing_schedule(
        self,
        entity_config: Dict,
        project: Project,
        schedule_in_gitlab: ProjectPipelineSchedule,
        schedule_description: str,
    ):
        entity_config["cron"] = _replace_extended_cron_pattern(
            project.id, entity_config["cron"]
        )
        if self._needs_update(schedule_in_gitlab.asdict(), entity_config):
            debug("Changing existing pipeline schedule '%s'", schedule_description)
            # In order to edit a Schedule created by someone else we need to take ownership:
            # https://docs.gitlab.com/ee/ci/pipelines/schedules.html#take-ownership
            shedule = project.pipelineschedules.get(schedule_in_gitlab.id)
            shedule.take_ownership()
            project.pipelineschedules.update(
                schedule_in_gitlab.id,
                {"description": schedule_description, **entity_config},
            )
            configured_variables = entity_config.get("variables")
            if configured_variables is not None:
                self._set_schedule_variables(
                    schedule_in_gitlab,
                    configured_variables,
                )
        else:
            debug("No update required for pipeline schedule '%s'", schedule_description)

    def _create_schedule_with_variables(
        self,
        entity_config: Dict,
        project: Project,
        schedule_description: str,
    ):
        entity_config["cron"] = _replace_extended_cron_pattern(
            project.id, entity_config["cron"]
        )
        schedule_data = {"description": schedule_description, **entity_config}
        debug("Creating pipeline schedule using data: '%s'", schedule_data)
        created_schedule_id = project.pipelineschedules.create(schedule_data).id
        created_schedule = project.pipelineschedules.get(created_schedule_id)

        configured_variables = entity_config.get("variables")
        if configured_variables is not None:
            self._set_schedule_variables(
                created_schedule,
                configured_variables,
            )

        created_schedule.save()

    @staticmethod
    def _set_schedule_variables(
        schedule: ProjectPipelineSchedule, variables: Dict
    ) -> None:
        attributes = schedule.attributes
        existing_variables = attributes.get("variables")
        if existing_variables:
            debug("Deleting variables for pipeline schedule '%s'", schedule.description)

            for variable in existing_variables:
                schedule.variables.delete(variable.get("key"))

        if variables:
            for variable_key, variable_data in variables.items():
                schedule.variables.create({"key": variable_key, **variable_data})

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


class ExtendedCronPattern:

    def __init__(self, project_id: int, cron_expression: str):
        self._h_pattern = re.compile(
            r"H(?:(\((?P<start>\d+)-(?P<end>\d+)\))|(?P<interval>/\d+))?"
        )
        # We do use random here to achieve a stable pseudo-random value, this is not security relevant
        # Seeding with project_id always returns the same numbers, that is what we want here.
        self._random = random.Random()  # nosec B311
        self._random.seed(project_id, 2)
        self._cron_parts = cron_expression.split()
        if len(self._cron_parts) != 5:
            raise ValueError(
                f"Expected 5 parts in the cron expression, got {self._cron_parts}"
            )

    def render(self) -> str:
        self._cron_parts[0] = self._detect_and_replace_h(self._cron_parts[0], 60)
        self._cron_parts[1] = self._detect_and_replace_h(self._cron_parts[1], 24)
        self._cron_parts[4] = self._detect_and_replace_h(self._cron_parts[4], 7)
        return " ".join(self._cron_parts)

    def _detect_and_replace_h(self, cron_part: str, default_max: int):
        parts = cron_part.split(",")
        for i, _ in enumerate(parts):
            match = self._h_pattern.match(parts[i])
            if match:
                self._replace_h(i, parts, match, default_max)
        return ",".join(parts)

    def _replace_h(self, i: int, parts: List[str], match: re.Match, default_max: int):
        interval = match.group("interval") or ""
        if interval:
            interval = int(interval[1:])
            times = int(default_max / interval)
            first = self._random.randint(0, interval)
            result = [str(first)]
            result.extend(str(first + i * interval) for i in range(1, times))
        else:
            start = int(match.group("start") or 0)
            end = int(match.group("end") or default_max - 1)
            result = [str(self._random.randint(start, end))]
        parts[i] = parts[i].replace(match.string, ",".join(result))


EXTENDED_CRON_PATTERN_ALIASES = {
    "@hourly": "H * * * *",
    "@daily": "H H * * *",
    "@weekly": "H H * * H",
    "@nightly": "H H(00-06) * * *",
}


def _replace_extended_cron_pattern(project_id: int, cron_expression: str) -> str:
    cron_expression = EXTENDED_CRON_PATTERN_ALIASES.get(
        cron_expression.lower(), cron_expression
    )
    return ExtendedCronPattern(project_id, cron_expression).render()
