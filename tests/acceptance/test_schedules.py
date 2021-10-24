import pytest


from tests.acceptance import run_gitlabform


@pytest.fixture(scope="class")
def schedules(gitlab, group_and_project):

    another_branch = "scheduled/new-feature"
    gitlab.create_branch(group_and_project, another_branch, "main")

    # fmt: off
    schedules = [
        ("Existing schedule", "main", "0 * * * *", {"active": "true"}),
        ("Existing schedule with vars", "main", "30 * * * *", {}),
        ("Existing schedule to replace", "main", "30 1 * * *", {}),
        ("Existing schedule to replace", another_branch, "30 2 * * *", {}),
    ]
    # fmt: on

    for schedule in schedules:
        gitlab.create_pipeline_schedule(
            group_and_project,
            *schedule,
        )

    redundant_schedule = gitlab.create_pipeline_schedule(
        group_and_project,
        "Redundant schedule",
        "main",
        "0 * * * *",
    )
    gitlab.create_pipeline_schedule_variable(
        group_and_project, redundant_schedule["id"], "test_variable", "test_value"
    )

    schedules.append(("Redundant schedule", "main", "0 * * * *"))

    return schedules  # provide fixture value


class TestSchedules:
    def test__add_new_schedule(self, gitlab, group_and_project, schedules):

        add_schedule = f"""
        projects_and_groups:
          {group_and_project}:
            schedules:
              "New schedule":
                ref: main
                cron: "0 * * * *"
                cron_timezone: "London"
                active: true
        """

        run_gitlabform(add_schedule, group_and_project)

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, group_and_project, "New schedule"
        )
        assert schedule is not None
        assert schedule["description"] == "New schedule"
        assert schedule["ref"] == "main"
        assert schedule["cron"] == "0 * * * *"
        assert schedule["cron_timezone"] == "London"
        assert schedule["active"] is True

    def test__add_new_schedule_with_mandatory_fields_only(
        self, gitlab, group_and_project, schedules
    ):

        add_schedule_mandatory_fields_only = f"""
        projects_and_groups:
          {group_and_project}:
            schedules:
              "New schedule with mandatory fields":
                ref: main
                cron: "30 1 * * *"
        """

        run_gitlabform(add_schedule_mandatory_fields_only, group_and_project)

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, group_and_project, "New schedule with mandatory fields"
        )
        assert schedule is not None
        assert schedule["description"] == "New schedule with mandatory fields"
        assert schedule["ref"] == "main"
        assert schedule["cron"] == "30 1 * * *"
        assert schedule["cron_timezone"] == "UTC"
        assert schedule["active"] is True

    def test__set_schedule_variables(self, gitlab, group_and_project, schedules):

        add_schedule_with_variables = f"""
        projects_and_groups:
          {group_and_project}:
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

        run_gitlabform(add_schedule_with_variables, group_and_project)

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, group_and_project, "New schedule with variables"
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

    def test__update_existing_schedule(self, gitlab, group_and_project, schedules):

        edit_schedule = f"""
        projects_and_groups:
          {group_and_project}:
            schedules:
              "Existing schedule":
                ref: scheduled/new-feature
                cron: "0 */4 * * *"
                cron_timezone: "Stockholm"
                active: false
        """

        run_gitlabform(edit_schedule, group_and_project)

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, group_and_project, "Existing schedule"
        )
        assert schedule is not None
        assert schedule["description"] == "Existing schedule"
        assert schedule["ref"] == "scheduled/new-feature"
        assert schedule["cron"] == "0 */4 * * *"
        assert schedule["cron_timezone"] == "Stockholm"
        assert schedule["active"] is False

    def test__replace_existing_schedules(self, gitlab, group_and_project, schedules):

        replace_schedules = f"""
        projects_and_groups:
          {group_and_project}:
            schedules:
              "Existing schedule to replace":
                ref: scheduled/new-feature
                cron: "0 */3 * * *"
                cron_timezone: "London"
                active: true
        """

        run_gitlabform(replace_schedules, group_and_project)

        schedules = self.__find_pipeline_schedules_by_description(
            gitlab, group_and_project, "Existing schedule to replace"
        )
        assert schedules is not None
        assert len(schedules) == 1
        assert schedules[0]["description"] == "Existing schedule to replace"
        assert schedules[0]["ref"] == "scheduled/new-feature"
        assert schedules[0]["cron"] == "0 */3 * * *"
        assert schedules[0]["cron_timezone"] == "London"
        assert schedules[0]["active"] is True

    def test__delete_schedule(self, gitlab, group_and_project, schedules):

        delete_schedule = f"""
        projects_and_groups:
          {group_and_project}:
            schedules:
              "Redundant schedule":
                delete: True
        """

        run_gitlabform(delete_schedule, group_and_project)

        schedule = self.__find_pipeline_schedule_by_description_and_get_first(
            gitlab, group_and_project, "Redundant schedule"
        )
        assert schedule is None

    @staticmethod
    def __find_pipeline_schedule_by_description_and_get_first(
        gitlab, group_and_project, description
    ):
        for schedule in gitlab.get_all_pipeline_schedules(group_and_project):
            if schedule["description"] == description:
                return gitlab.get_pipeline_schedule(group_and_project, schedule["id"])
        return None

    @staticmethod
    def __find_pipeline_schedules_by_description(
        gitlab, group_and_project, description
    ):
        return list(
            map(
                lambda schedule: gitlab.get_pipeline_schedule(
                    group_and_project, schedule["id"]
                ),
                filter(
                    lambda schedule: schedule["description"] == description,
                    gitlab.get_all_pipeline_schedules(group_and_project),
                ),
            )
        )
