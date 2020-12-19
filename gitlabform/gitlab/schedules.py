from gitlabform.gitlab.core import GitLabCore


class GitLabPipelineSchedules(GitLabCore):
    def get_all_pipeline_schedules(self, project_and_group_name):
        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules", project_and_group_name
        )

    def get_pipeline_schedule(self, project_and_group_name, pipeline_schedule_id):
        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s",
            (project_and_group_name, pipeline_schedule_id),
        )

    def create_pipeline_schedule(
        self, project_and_group_name, description, ref, cron, optional_data=None
    ):
        if optional_data is None:
            optional_data = {}
        data_required = {
            "description": description,
            "ref": ref,
            "cron": cron,
        }
        data = {**optional_data, **data_required}

        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules",
            project_and_group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def update_pipeline_schedule(
        self, project_and_group_name, pipeline_schedule_id, data
    ):
        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s",
            (project_and_group_name, pipeline_schedule_id),
            method="PUT",
            data=data,
            expected_codes=[200, 201],
        )

    def take_ownership(self, project_and_group_name, pipeline_schedule_id):
        self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s/take_ownership",
            (project_and_group_name, pipeline_schedule_id),
            method="POST",
            expected_codes=[200, 201],
        )

    def delete_pipeline_schedule(self, project_and_group_name, pipeline_schedule_id):
        self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s",
            (project_and_group_name, pipeline_schedule_id),
            method="DELETE",
            expected_codes=[200, 201, 204, 404],
        )

    def create_pipeline_schedule_variable(
        self,
        project_and_group_name,
        pipeline_schedule_id,
        variable_key,
        variable_value,
        optional_data=None,
    ):
        if optional_data is None:
            optional_data = {}
        data_required = {
            "key": variable_key,
            "value": variable_value,
        }
        data = {**optional_data, **data_required}

        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s/variables",
            (project_and_group_name, pipeline_schedule_id),
            method="POST",
            data=data,
            expected_codes=201,
        )

    def update_pipeline_schedule_variable(
        self,
        project_and_group_name,
        pipeline_schedule_id,
        variable_key,
        variable_value,
        optional_data=None,
    ):
        if optional_data is None:
            optional_data = {}
        data_required = {
            "value": variable_value,
        }
        data = {**optional_data, **data_required}

        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s/variables/%s",
            (project_and_group_name, pipeline_schedule_id, variable_key),
            method="PUT",
            data=data,
            expected_codes=[200, 201],
        )

    def delete_pipeline_schedule_variable(
        self, project_and_group_name, pipeline_schedule_id, variable_key
    ):
        return self._make_requests_to_api(
            "projects/%s/pipeline_schedules/%s/variables/%s",
            (project_and_group_name, pipeline_schedule_id, variable_key),
            method="DELETE",
            expected_codes=[200, 201, 202, 204, 404],
        )
