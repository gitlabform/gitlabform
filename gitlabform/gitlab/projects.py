import json

from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabProjects(GitLabCore):

    def create_project(self, name, path, namespace_id):
        data = {
            'name': name,
            'path': path,
            'namespace_id': namespace_id,
        }
        return self._make_requests_to_api("projects", data=data, method='POST', expected_codes=201)

    def delete_project(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s", project_and_group_name, method='DELETE',
                                          expected_codes=[202, 204])

    def get_all_projects(self):
        """
        :param group: group name
        :return: sorted list of ALL projects you have access to, strings "group/project_name"
        """
        try:
            result = self._make_requests_to_api("projects?order_by=name&sort=asc", paginated=True)
            return sorted(map(lambda x: x['path_with_namespace'], result))
        except NotFoundException:
            return []

    def post_deploy_key(self, project_and_group_name, deploy_key):
        # deploy_key has to be like this:
        # {
        #     'title': title,
        #     'key': key,
        #     'can_push': can_push,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/deploy_keys.html#add-deploy-key
        self._make_requests_to_api("projects/%s/deploy_keys", project_and_group_name, 'POST', deploy_key,
                                   expected_codes=201)

    def get_deploy_keys(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/deploy_keys", project_and_group_name)

    def get_deploy_key(self, project_and_group_name, id):
        return self._make_requests_to_api("projects/%s/deploy_keys/%s", (project_and_group_name, id), 'GET')

    def post_secret_variable(self, project_and_group_name, secret_variable):
        # secret_variable has to be like this:
        # {
        #     'key': key,
        #     'value': value,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/build_variables.html#create-variable
        self._make_requests_to_api("projects/%s/variables", project_and_group_name, 'POST', secret_variable,
                                   expected_codes=201)

    def put_secret_variable(self, project_and_group_name, secret_variable):
        # secret_variable has to be like this:
        # {
        #     'key': key,
        #     'value': value,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/build_variables.html#update-variable
        self._make_requests_to_api("projects/%s/variables/%s", (project_and_group_name, secret_variable['key']),
                                   'PUT', secret_variable)

    def get_secret_variable(self, project_and_group_name, secret_variable_key):
        return self._make_requests_to_api("projects/%s/variables/%s", (project_and_group_name, secret_variable_key))['value']

    def get_secret_variables(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/variables", project_and_group_name)

    def get_project_settings(self, project_and_group_name):
        try:
            return self._make_requests_to_api("projects/%s", project_and_group_name)
        except NotFoundException:
            return dict()

    def put_project_settings(self, project_and_group_name, project_settings):
        # project_settings has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/projects.html#edit-project
        self._make_requests_to_api("projects/%s", project_and_group_name, 'PUT', project_settings)

    def get_project_push_rules(self, project_and_group_name: str):
        try:
            return self._make_requests_to_api("projects/%s/push_rule", project_and_group_name)
        except NotFoundException:
            return dict()

    def put_project_push_rules(self, project_and_group_name, push_rules):
        # push_rules has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ee/api/projects.html#edit-project-push-rule

        # for this endpoint GitLab fails if project name contains ".", so lets use pid instead
        pid: str = self._get_project_id(project_and_group_name)

        self._make_requests_to_api("projects/%s/push_rule", pid, 'PUT', push_rules)

    def post_project_push_rules(self, project_and_group_name: str, push_rules):
        # push_rules has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ee/api/projects.html#edit-project-push-rule

        pid: str = self._get_project_id(project_and_group_name)

        self._make_requests_to_api("projects/%s/push_rule", pid, 'POST', push_rules)

    def get_hook_id(self, project_and_group_name, url):
        hooks = self._make_requests_to_api("projects/%s/hooks", project_and_group_name, 'GET')
        for hook in hooks:
            if hook['url'] == url:
                return hook['id']
        return None

    def delete_hook(self, project_and_group_name, hook_id):
        self._make_requests_to_api("projects/%s/hooks/%s", (project_and_group_name, hook_id), 'DELETE',
                                   expected_codes=[200, 204])

    def put_hook(self, project_and_group_name, hook_id, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/hooks/%s", (project_and_group_name, hook_id), 'PUT', data)

    def post_hook(self, project_and_group_name, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/hooks", project_and_group_name, 'POST', data, expected_codes=201)

    def post_approvals_settings(self, project_and_group_name, data):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data_required = {'id': pid}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/approvals", pid, 'POST', data, expected_codes=201)

    def get_approvals_settings(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/approvals", pid)

    def delete_legacy_approvers(self, project_and_group_name):
        # uses pre-12.3, deprecated API to clean up the setup of approvers made the old way of configuring approvers

        # we need to pass data to this gitlab API endpoint as JSON, because when passing as data the JSON converter
        # used by requests lib changes empty arrays into nulls and omits it, which results in
        # {"error":"approver_group_ids is missing"} error from gitlab...

        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data = "{" \
               + '"id":' + str(pid) + ',' \
               + '"approver_ids": [],' \
               + '"approver_group_ids": []' \
               + "}"
        json_data = json.loads(data)
        self._make_requests_to_api("projects/%s/approvers", pid, 'PUT', data=None, json=json_data)

    def get_approvals_rules(self, project_and_group_name):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/approval_rules", pid)

    def delete_approvals_rule(self, project_and_group_name, approval_rule_id):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/approval_rules/%s", (pid, approval_rule_id), method='DELETE',
                                   expected_codes=[200, 204])

    def create_approval_rule(self, project_and_group_name, name, approvals_required, approvers, approver_groups):
        pid = self._get_project_id(project_and_group_name)

        data = self._create_approval_rule_data(project_and_group_name, name, approvals_required, approvers,
                                               approver_groups)

        self._make_requests_to_api("projects/%s/approval_rules", pid, method='POST', data=data, expected_codes=201)

    def update_approval_rule(self, project_and_group_name, approval_rule_id, name, approvals_required,
                             approvers, approver_groups):
        pid = self._get_project_id(project_and_group_name)

        data = self._create_approval_rule_data(project_and_group_name, name, approvals_required, approvers,
                                               approver_groups)
        data['approval_rule_id'] = approval_rule_id

        self._make_requests_to_api("projects/%s/approval_rules/%s", (pid, approval_rule_id), method='PUT', data=data)

    def _create_approval_rule_data(self, project_and_group_name, name, approvals_required, approvers, approver_groups):
        pid = self._get_project_id(project_and_group_name)

        # gitlab API expects ids, not names of users and groups, so we need to convert first
        user_ids = []
        for approver_name in approvers:
            user_ids.append(self._get_user_id(approver_name))
        group_ids = []
        for group_path in approver_groups:
            group_ids.append(int(self._get_group_id(group_path)))

        data = {
            'id': int(pid),
            'name': name,
            'approvals_required': approvals_required,
            'user_ids': user_ids,
            'group_ids': group_ids,
        }

        return data

    def share_with_group(self, project_and_group_name, group_name, group_access, expires_at):
        data = {
            "group_id": self._get_group_id(group_name),
            "expires_at": expires_at
        }
        if group_access is not None:
            data['group_access'] = group_access
        return self._make_requests_to_api("projects/%s/share", project_and_group_name, method='POST', data=data,
                                          expected_codes=201)

    def unshare_with_group(self, project_and_group_name, group_name):
        # 404 means that the group already has not access, so let's accept it for idempotency
        group_id = self._get_group_id(group_name)
        return self._make_requests_to_api("projects/%s/share/%s", (project_and_group_name, group_id), method='DELETE',
                                          expected_codes=[204, 404])

    def archive(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/archive", project_and_group_name, method='POST',
                                          expected_codes=[200, 201])

    def unarchive(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/unarchive", project_and_group_name, method='POST',
                                          expected_codes=[200, 201])
