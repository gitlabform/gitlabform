from gitlabform.gitlab.projects import GitLabProjects


class GitLabProjectDeployKeys(GitLabProjects):
    def get_deploy_keys(self, project_and_group_name):
        return self._make_requests_to_api(
            "projects/%s/deploy_keys", project_and_group_name
        )

    def post_deploy_key(self, project_and_group_name, deploy_key_in_config):
        # deploy_key_in_config has to be like this:
        # {
        #     'title': title,
        #     'key': key,
        #     'can_push': can_push,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/deploy_keys.html#add-deploy-key
        self._make_requests_to_api(
            "projects/%s/deploy_keys",
            project_and_group_name,
            "POST",
            deploy_key_in_config,
            expected_codes=201,
        )

    def put_deploy_key(
        self, project_and_group_name, deploy_key_in_gitlab, deploy_key_in_config
    ):
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
        return self._make_requests_to_api(
            "projects/%s/deploy_keys/%s", (project_and_group_name, id), "GET"
        )
