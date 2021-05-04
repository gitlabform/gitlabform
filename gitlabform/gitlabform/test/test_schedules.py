import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    get_gitlab,
    delete_pipeline_schedules_from_project,
    create_readme_in_project,
    GROUP_NAME,
)

PROJECT_NAME = "schedules_project"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME


@pytest.fixture(scope="module")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)
    create_readme_in_project(GROUP_AND_PROJECT_NAME)  # in main branch

    delete_pipeline_schedules_from_project(GROUP_AND_PROJECT_NAME)

    another_branch = "scheduled/new-feature"
    gl.create_branch(GROUP_AND_PROJECT_NAME, another_branch, "main")

    gl.create_pipeline_schedule(
        GROUP_AND_PROJECT_NAME,
        "Existing schedule",
        "main",
        "0 * * * *",
        {"active": "true"},
    )
    gl.create_pipeline_schedule(
        GROUP_AND_PROJECT_NAME, "Existing schedule with vars", "main", "30 * * * *"
    )

    gl.create_pipeline_schedule(
        GROUP_AND_PROJECT_NAME, "Existing schedule to replace", "main", "30 1 * * *"
    )
    gl.create_pipeline_schedule(
        GROUP_AND_PROJECT_NAME,
        "Existing schedule to replace",
        another_branch,
        "30 2 * * *",
    )

    redundant_schedule = gl.create_pipeline_schedule(
        GROUP_AND_PROJECT_NAME, "Redundant schedule", "main", "0 * * * *"
    )
    gl.create_pipeline_schedule_variable(
        GROUP_AND_PROJECT_NAME, redundant_schedule["id"], "test_variable", "test_value"
    )

    def fin():
        # delete all created resources
        delete_pipeline_schedules_from_project(GROUP_AND_PROJECT_NAME)
        gl.delete_branch(GROUP_AND_PROJECT_NAME, another_branch)
        gl.delete_project(GROUP_AND_PROJECT_NAME)

    request.addfinalizer(fin)
    return gl  # provide fixture value


add_schedule = """
project_settings:
  gitlabform_tests_group/schedules_project:
    schedules:
      "New schedule":
        ref: main
        cron: "0 * * * *"
        cron_timezone: "London"
        active: true
"""

add_schedule_mandatory_fields_only = """
project_settings:
  gitlabform_tests_group/schedules_project:
    schedules:
      "New schedule with mandatory fields":
        ref: main
        cron: "30 1 * * *"
"""

add_schedule_with_variables = """
project_settings:
  gitlabform_tests_group/schedules_project:
    schedules:
      "New schedule with variables":
        ref: main
        cron: "30 1 * * *"
        variables:
            var1: 
                value: value123
            var2:
                value: value987
                variable_type: file
"""

edit_schedule = """
project_settings:
  gitlabform_tests_group/schedules_project:
    schedules:
      "Existing schedule":
        ref: scheduled/new-feature
        cron: "0 */4 * * *"
        cron_timezone: "Stockholm"
        active: false
"""

replace_schedules = """
project_settings:
  gitlabform_tests_group/schedules_project:
    schedules:
      "Existing schedule to replace":
        ref: scheduled/new-feature
        cron: "0 */3 * * *"
        cron_timezone: "London"
        active: true
"""

delete_schedule = """
project_settings:
  gitlabform_tests_group/schedules_project:
    schedules:
      "Redundant schedule":
        delete: True
"""


class TestSchedules:
    def test__add_new_schedule(self, gitlab):
        gf = GitLabForm(
            config_string=add_schedule,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, "New schedule"
        )
        assert schedule is not None
        assert schedule["description"] == "New schedule"
        assert schedule["ref"] == "main"
        assert schedule["cron"] == "0 * * * *"
        assert schedule["cron_timezone"] == "London"
        assert schedule["active"] is True

    def test__add_new_schedule_with_mandatory_fields_only(self, gitlab):
        gf = GitLabForm(
            config_string=add_schedule_mandatory_fields_only,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, "New schedule with mandatory fields"
        )
        assert schedule is not None
        assert schedule["description"] == "New schedule with mandatory fields"
        assert schedule["ref"] == "main"
        assert schedule["cron"] == "30 1 * * *"
        assert schedule["cron_timezone"] == "UTC"
        assert schedule["active"] is True

    def test__set_schedule_variables(self, gitlab):
        gf = GitLabForm(
            config_string=add_schedule_with_variables,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, "New schedule with variables"
        )
        assert schedule is not None
        assert schedule["description"] == "New schedule with variables"
        assert schedule["ref"] == "main"
        assert schedule["cron"] == "30 1 * * *"
        assert schedule["cron_timezone"] == "UTC"
        assert schedule["active"] is True
        assert schedule["variables"] is not None
        assert len(schedule["variables"]) == 2

        assert schedule["variables"][0]["variable_type"] == "env_var"
        assert schedule["variables"][0]["key"] == "var1"
        assert schedule["variables"][0]["value"] == "value123"

        assert schedule["variables"][1]["variable_type"] == "file"
        assert schedule["variables"][1]["key"] == "var2"
        assert schedule["variables"][1]["value"] == "value987"

    def test__update_existing_schedule(self, gitlab):
        gf = GitLabForm(
            config_string=edit_schedule,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, "Existing schedule"
        )
        assert schedule is not None
        assert schedule["description"] == "Existing schedule"
        assert schedule["ref"] == "scheduled/new-feature"
        assert schedule["cron"] == "0 */4 * * *"
        assert schedule["cron_timezone"] == "Stockholm"
        assert schedule["active"] is False

    def test__replace_existing_schedules(self, gitlab):
        gf = GitLabForm(
            config_string=replace_schedules,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        schedules = self.__find_pipeline_schedules_by_description(
            gitlab, "Existing schedule to replace"
        )
        assert schedules is not None
        assert len(schedules) == 1
        assert schedules[0]["description"] == "Existing schedule to replace"
        assert schedules[0]["ref"] == "scheduled/new-feature"
        assert schedules[0]["cron"] == "0 */3 * * *"
        assert schedules[0]["cron_timezone"] == "London"
        assert schedules[0]["active"] is True

    def test__delete_schedule(self, gitlab):
        gf = GitLabForm(
            config_string=delete_schedule,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, "Redundant schedule"
        )
        assert schedule is None

    @staticmethod
    def __find_pipeline_schedule_by_description_and_get_first(gitlab, description):
        for schedule in gitlab.get_all_pipeline_schedules(GROUP_AND_PROJECT_NAME):
            if schedule["description"] == description:
                return gitlab.get_pipeline_schedule(
                    GROUP_AND_PROJECT_NAME, schedule["id"]
                )
        return None

    @staticmethod
    def __find_pipeline_schedules_by_description(gitlab, description):
        return list(
            map(
                lambda schedule: gitlab.get_pipeline_schedule(
                    GROUP_AND_PROJECT_NAME, schedule["id"]
                ),
                filter(
                    lambda schedule: schedule["description"] == description,
                    gitlab.get_all_pipeline_schedules(GROUP_AND_PROJECT_NAME),
                ),
            )
        )
