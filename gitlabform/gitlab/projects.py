import json
import logging.config

from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabProjects(GitLabCore):

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

    def get_project_push_rules(self, project_and_group_name):
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
        pid = self._get_project_id(project_and_group_name)

        self._make_requests_to_api("projects/%s/push_rule", pid, 'PUT', push_rules)

    def get_hook_id(self, project_and_group_name, url):
        hooks = self._make_requests_to_api("projects/%s/hooks", project_and_group_name, 'GET')
        for hook in hooks:
            if hook['url'] == url:
                return hook['id']
        return None

    def delete_hook(self, project_and_group_name, hook_id):
        self._make_requests_to_api("projects/%s/hooks/%s", (project_and_group_name, hook_id), 'DELETE')

    def put_hook(self, project_and_group_name, hook_id, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/hooks/%s", (project_and_group_name, hook_id), 'PUT', data)

    def post_hook(self, project_and_group_name, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/hooks", project_and_group_name, 'POST', data, expected_codes=201)

    def post_approvals(self, project_and_group_name, data):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data_required = {'id': pid}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/approvals", pid, 'POST', data, expected_codes=201)

    def put_approvers(self, project_and_group_name, approvers, approver_groups):
        """
        :param project_and_group_name: "group/project" string
        :param approvers: list of approver user names
        :param approver_groups: list of approver group paths
        """

        # gitlab API expects ids, not names of users and groups, so we need to convert first
        approver_ids = []
        for approver_name in approvers:
            approver_ids.append(self._get_user_id(approver_name))
        approver_group_ids = []
        for group_path in approver_groups:
            approver_group_ids.append(self._get_group_id(group_path))

        # we need to pass data to this gitlab API endpoint as JSON, because when passing as data the JSON converter
        # used by requests lib changes empty arrays into nulls and omits it, which results in
        # {"error":"approver_group_ids is missing"} error from gitlab...
        # TODO: create JSON object directly, omit converting string to JSON
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data = "{"\
               + '"id":' + str(pid) + ','\
               + '"approver_ids": [' + ','.join(str(x) for x in approver_ids) + '],'\
               + '"approver_group_ids": [' + ','.join(str(x) for x in approver_group_ids) + ']'\
               + "}"
        json_data = json.loads(data)
        self._make_requests_to_api("projects/%s/approvers", pid, 'PUT', data=None, json=json_data)

    def get_project_group_shares(self, project_and_group_name):
        """
        :param project_and_group_name: "group/project" string
        :return dict of group shares with key of full_path, value of the group_share data
                docs: https://docs.gitlab.com/ee/api/projects.html#get-single-project
        """
        settings = self.get_project_settings(project_and_group_name)
        try:
            return {g["group_full_path"]: g for g in settings["shared_with_groups"]}
        except NotFoundException:
            return dict()


    def get_project_members(self, project_and_group_name):
        """
        :param project_and_group_name: "group/project" string
        :return dict of users with key of username and value of user_share data
                docs: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project
        """
        try:
            members = self._make_requests_to_api("projects/%s/members", project_and_group_name)
            return {m["username"]:m for m in members}
        except NotFoundException:
            return list()

    def get_group_members(self, group_name, skip_owner=True):
        """
        :param group_name name of group string
        :param skip_owner do not include the owner in user list
        :return list of usernames of the members of the group
        """
        try:
            id = self._get_group_id(group_name)
            members = self._make_requests_to_api("groups/%s/members", id)
            member_usernames = []
            for m in members:
                if skip_owner and m["access_level"] == 50:
                    continue
                member_usernames.append(m["username"])
            return member_usernames
        except NotFoundException:
            return list()


    def share_with_group(self, project_and_group_name, group_name, group_access, expires_at):
        data = {
            "group_id": self._get_group_id(group_name),
            "expires_at": expires_at
        }
        if group_access is not None:
            data['group_access'] = group_access
        logging.warning("\t++ ADD group access: %s [%s] to: %s", group_name, group_access, project_and_group_name)
        return self._make_requests_to_api("projects/%s/share", project_and_group_name, method='POST', data=data, expected_codes=201)

    def update_group_share_of_project(self, project_and_group_name, group_name, group_access, expires_at):
        data = {
            "group_id": self._get_group_id(group_name),
            "expires_at": expires_at
        }
        if group_access is not None:
            data['group_access'] = group_access
        group_id = self._get_group_id(group_name)
        logging.warning("\t~~ UPD group access: %s [%s] to: %s", group_name, group_access, project_and_group_name)
        return self._make_requests_to_api("projects/%s/share/%s", (project_and_group_name, group_id), method='PUT', data=data, expected_codes=200)

    def unshare_with_group(self, project_and_group_name, group_name):
        group_id = self._get_group_id(group_name)
        logging.warning("\t-- DEL group access: %s to: %s", group_name, project_and_group_name)
        return self._make_requests_to_api("projects/%s/share/%s", (project_and_group_name, group_id), method='DELETE',
                                          expected_codes=204)


    def archive(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/archive", project_and_group_name, method='POST',
                                          expected_codes=[200, 201])

    def unarchive(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/unarchive", project_and_group_name, method='POST',
                                          expected_codes=[200, 201])
