from gitlabform.gitlab.core import GitLabCore


class GitLabPipelines(GitLabCore):
    def get_pipelines(self, project_and_group_name, branch):
        pipelines = self._make_requests_to_api(
            "projects/%s/pipelines?ref=%s",
            (project_and_group_name, branch),
        )
        return pipelines

    def get_pipeline(self, project_and_group_name, pipeline_id):
        pipeline = self._make_requests_to_api("/projects/%s/pipelines/%s", (project_and_group_name, pipeline_id))
        return pipeline

    def retry_pipeline(self, project_and_group_name, pipeline_id):
        pipeline = self._make_requests_to_api(
            "projects/%s/pipelines/%s/retry",
            (project_and_group_name, pipeline_id),
            method="POST",
            expected_codes=[200, 201],
        )
        return pipeline
