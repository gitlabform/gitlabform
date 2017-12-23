import urllib

from gitlabform.gitlab.core import GitLabCore


class GitLabProjects(GitLabCore):

    def get_all_projects(self):
        """
        :param group: group name
        :return: sorted list of ALL projects you have access to, strings "group/project_name"
        """
        result = self._make_requests_to_api("projects?order_by=name&sort=asc", paginated=True)
        return sorted(map(lambda x: x['path_with_namespace'], result))

    def post_deploy_key(self, project_and_group_name, deploy_key):
        pid = self._get_project_id(project_and_group_name)
        # deploy_key has to be like this:
        # {
        #     'title': title,
        #     'key': key,
        #     'can_push': can_push,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/deploy_keys.html#add-deploy-key
        self._make_requests_to_api("projects/%s/deploy_keys", pid, 'POST', deploy_key, expected_codes=201)

    def get_deploy_keys(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/deploy_keys", pid)

    def post_secret_variable(self, project_and_group_name, secret_variable):
        pid = self._get_project_id(project_and_group_name)
        # secret_variable has to be like this:
        # {
        #     'key': key,
        #     'value': value,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/build_variables.html#create-variable
        self._make_requests_to_api("projects/%s/variables", pid, 'POST', secret_variable, expected_codes=201)

    def put_secret_variable(self, project_and_group_name, secret_variable):
        pid = self._get_project_id(project_and_group_name)
        # secret_variable has to be like this:
        # {
        #     'key': key,
        #     'value': value,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/build_variables.html#update-variable
        self._make_requests_to_api("projects/%s/variables/%s", (pid, secret_variable['key']), 'PUT', secret_variable)

    def get_secret_variable(self, project_and_group_name, secret_variable_key):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/variables/%s", (pid, secret_variable_key))['value']

    def get_secret_variables(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/variables", pid)

    def get_project_settings(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s", pid)

    def put_project_settings(self, project_and_group_name, project_settings):
        pid = self._get_project_id(project_and_group_name)
        # project_settings has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/projects.html#edit-project
        self._make_requests_to_api("projects/%s", pid, 'PUT', project_settings)

    def get_hook_id(self, project_and_group_name, url):
        pid = self._get_project_id(project_and_group_name)
        hooks = self._make_requests_to_api("projects/%s/hooks", pid, 'GET')
        for hook in hooks:
            if hook['url'] == url:
                return hook['id']
        return None

    def delete_hook(self, project_and_group_name, hook_id):
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/hooks/%s", (pid, hook_id), 'DELETE')

    def put_hook(self, project_and_group_name, hook_id, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/hooks/%s", (pid, hook_id), 'PUT', data)

    def post_hook(self, project_and_group_name, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/hooks", pid, 'POST', data, expected_codes=201)
