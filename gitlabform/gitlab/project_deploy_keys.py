from gitlabform.gitlab.core import UnexpectedResponseException
from gitlabform.gitlab.projects import GitLabProjects


class GitLabProjectDeployKeys(GitLabProjects):
    def get_all_deploy_keys(self):
        return self._make_requests_to_api("deploy_keys")

    def get_deploy_keys(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/deploy_keys", project_and_group_name)

    def post_deploy_key(self, project_and_group_name, deploy_key_in_config):
        # deploy_key_in_config has to be like this:
        # {
        #     'title': title,
        #     'key': key,
        #     'can_push': can_push,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/deploy_keys.html#add-deploy-key

        try:
            self._make_requests_to_api(
                "projects/%s/deploy_keys",
                project_and_group_name,
                "POST",
                deploy_key_in_config,
                expected_codes=[201],
            )

        except UnexpectedResponseException as e:
            if e.response_status_code == 400 and ("has already been taken" in e.response_text):
                # Sometimes GitLab throws HTTP 400: {"deploy_key.fingerprint_sha256":["has already been taken"]}
                # when you try to add an existing SSH key to another project, although according to the API docs
                # it should work
                # (see https://docs.gitlab.com/ee/api/deploy_keys.html#add-deploy-keys-to-multiple-projects).

                # As a workaround, when that happens, we will try to get this key's id and enable this existing key
                # for the new project.

                all_existing_keys = self.get_all_deploy_keys()

                existing_key_id = None
                for existing_key in all_existing_keys:
                    if self._keys_are_effectively_equal(existing_key["key"], deploy_key_in_config["key"]):
                        existing_key_id = existing_key["id"]
                        break

                if existing_key_id:
                    # POST /projects/:id/deploy_keys/:key_id/enable
                    self._make_requests_to_api(
                        "projects/%s/deploy_keys/%s/enable",
                        (project_and_group_name, existing_key_id),
                        "POST",
                        expected_codes=201,
                    )
                else:
                    e.message = (
                        e.message
                        + "\n"
                        + "!!! However we haven't found this key in GitLab under the /deploy_keys API... !!!"
                    )
                    raise e

    def put_deploy_key(self, project_and_group_name, deploy_key_in_gitlab, deploy_key_in_config):
        # according to docs_new at https://docs.gitlab.com/ee/api/deploy_keys.html#update-deploy-key
        # you only can change key's title and can_push param

        changeable_data = {
            "title": deploy_key_in_config.get("title", None),
            "can_push": deploy_key_in_config.get("can_push", None),
        }

        return self._make_requests_to_api(
            "projects/%s/deploy_keys/%s",
            (project_and_group_name, deploy_key_in_gitlab["id"]),
            "PUT",
            changeable_data,
        )

    def delete_deploy_key(self, project_and_group_name, deploy_key_in_config):
        return self._make_requests_to_api(
            "projects/%s/deploy_keys/%s",
            (project_and_group_name, deploy_key_in_config["id"]),
            method="DELETE",
            expected_codes=[204, 404],
        )

    def get_deploy_key(self, project_and_group_name, id):
        return self._make_requests_to_api("projects/%s/deploy_keys/%s", (project_and_group_name, id), "GET")

    @staticmethod
    def _keys_are_effectively_equal(key1, key2):
        # We ignore the comment part of the SSH key as GitLab doesn't allow adding the same key just
        # with a different comment BUT it also has a bug that it returns keys with only parts of the
        # comments if the comment contains spaces, so it may show a difference where there is none...

        key1_type = key1.split(" ")[0]
        key1_value = key1.split(" ")[1]
        key2_type = key2.split(" ")[0]
        key2_value = key2.split(" ")[1]

        return (key1_type == key2_type) and (key1_value == key2_value)
