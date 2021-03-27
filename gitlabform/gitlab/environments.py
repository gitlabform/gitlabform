import json

from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabEnvironments(GitLabCore):
    def get_all_environments(self, project_and_group_name):
        # https://docs.gitlab.com/ee/api/environments.html#list-environments
        return self._make_requests_to_api(
            "projects/%s/environments", project_and_group_name
        )

    def get_environment(self, project_and_group_name, env_name):
        # https://docs.gitlab.com/ee/api/environments.html#get-a-specific-environment
        e = self._make_requests_to_api(
            "projects/%s/environments", project_and_group_name
        )
        for env in e:
            if env["name"] == env_name:
                eid = env["id"]
                return self._make_requests_to_api(
                    "projects/%s/environments/%s", (project_and_group_name, eid)
                )

    def post_environment(self, project_and_group_name, data):
        # https://docs.gitlab.com/ee/api/environments.html#create-a-new-environment
        self._make_requests_to_api(
            "projects/%s/environments",
            project_and_group_name,
            "POST",
            data,
            expected_codes=201,
        )

    def delete_environment(self, project_and_group_name, eid):
        # https://docs.gitlab.com/ee/api/environments.html#delete-an-environment
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api(
            "projects/%s/environments/%s",
            (project_and_group_name, eid),
            method="DELETE",
            expected_codes=[204, 404],
        )

    def stop_environment(self, project_and_group_name, eid):
        # https://docs.gitlab.com/ee/api/environments.html#stop-an-environment
        self._make_requests_to_api(
            "projects/%s/environments/%s/stop",
            (project_and_group_name, eid),
            method="POST",
            expected_codes=[200, 404],
        )


#    def put_environment():
# https://docs.gitlab.com/ee/api/environments.html#edit-an-existing-environment
