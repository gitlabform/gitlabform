import functools
from typing import Union, Any, Optional, Dict, List

import gitlab.const
from gitlab import Gitlab, GitlabGetError, GitlabListError, GraphQL
from gitlab.base import RESTObject
from gitlab.v4.objects import Group, Project, User

from gitlabform.gitlab.core import NotFoundException

from logging import info


# Extends the python-gitlab class to add convenience wrappers for common functionality used within gitlabform
class PythonGitlab(Gitlab):
    def __init__(
        self,
        graphql: GraphQL,
        url: Optional[str] = None,
        private_token: Optional[str] = None,
        oauth_token: Optional[str] = None,
        job_token: Optional[str] = None,
        ssl_verify: Union[bool, str] = True,
        http_username: Optional[str] = None,
        http_password: Optional[str] = None,
        timeout: Optional[float] = None,
        api_version: str = "4",
        per_page: Optional[int] = None,
        pagination: Optional[str] = None,
        order_by: Optional[str] = None,
        user_agent: str = gitlab.const.USER_AGENT,
        retry_transient_errors: bool = False,
        keep_base_url: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            url,
            private_token,
            oauth_token,
            job_token,
            ssl_verify,
            http_username,
            http_password,
            timeout,
            api_version,
            per_page,
            pagination,
            order_by,
            user_agent,
            retry_transient_errors,
            keep_base_url,
            **kwargs,
        )
        # Python Gitlab GraphQL interface
        # https://python-gitlab.readthedocs.io/en/stable/api-usage-graphql.html
        self.graphql = graphql

    def get_user_id_cached(self, username) -> int | None:
        """
        Get user id from username
        API call layer "get_user_by_username" is cached, we do not cache at this level as it would add
        duplication of data into the cache
        """
        user = self.get_user_by_username_cached(username)

        if user is None:
            return None

        return user.id

    def get_group_id(self, groupname) -> int:
        group = self.get_group_by_path_cached(groupname)
        return group.id

    def get_project_id(self, name) -> int:
        project = self.get_project_by_path_cached(name)
        return project.id

    @functools.lru_cache()
    def get_project_by_path_cached(self, name: str, lazy: bool = False) -> Project:
        project: Project = self.projects.get(name, lazy)
        if project:
            return project

        raise GitlabGetError("No project found when getting '%s'" % name, 404)

    @functools.lru_cache()
    def get_group_by_path_cached(self, groupname: str) -> Group:
        group: Group = self.groups.get(groupname, with_projects=False)
        if group:
            return group

        raise GitlabGetError("No group found when getting '%s'" % groupname, 404)

    def get_group_case_insensitive(self, some_string: str) -> Dict:
        # maybe "foo/bar" is some group's path
        try:
            # try with exact case
            return self.groups.get(some_string, with_projects=False).asdict()
        except GitlabGetError as e:
            if e.response_code != 404:
                raise

        # try case insensitive; search by the last path component, because GitLab's
        # search only matches a group's own name/path, not its full path
        last_path_component = some_string.lower().rsplit("/", 1)[-1]
        for group in self.groups.list(search=last_path_component, get_all=True):
            if group.full_path.lower() == some_string.lower():
                return group.asdict()
        raise NotFoundException(f"Group/subgroup with path '{some_string}' not found.")

    def get_project_case_insensitive(self, some_string: str) -> Dict:
        # maybe "foo/bar" is some project's path
        try:
            # try with exact case
            return self.projects.get(some_string).asdict()
        except GitlabGetError as e:
            if e.response_code != 404:
                raise

        # try case insensitive; search by the last path component, because GitLab's
        # search only matches a project's own name/path, not its full path.
        # Note: no simple=True here, because the callers need fields like "archived"
        # that the simple representation lacks.
        last_path_component = some_string.lower().rsplit("/", 1)[-1]
        for project in self.projects.list(search=last_path_component, get_all=True):
            if project.path_with_namespace.lower() == some_string.lower():
                return project.asdict()
        raise NotFoundException(f"Project with path '{some_string}' not found.")

    def get_group_descendants(self, group_id_or_path) -> List[Dict]:
        group = self.groups.get(group_id_or_path, lazy=True)
        return [descendant.asdict() for descendant in group.descendant_groups.list(get_all=True)]

    def get_groups(self) -> List[str]:
        """
        :return: sorted list of group full paths
        """
        if self._is_admin():
            groups = self.groups.list(get_all=True, all_available=True)
        else:
            # as a non-admin it's pointless to get groups with a lower role than Reporter
            # - it's the minimal role that is needed to manage something (f.e. group labels)
            groups = self.groups.list(get_all=True, min_access_level=20)
        return sorted(group.full_path for group in groups)

    def get_projects(self, group: str, include_archived: bool = False, only_names: bool = True) -> List:
        """
        :param group: group name
        :param include_archived: set to True if archived projects should also be returned
        :param only_names: set to False to get the whole project dicts
        :return: sorted list of strings "group/project_name". Note that only projects from the "group" namespace are
                 returned, so if "group" (= members of this group) is also a member of some projects, they won't be
                 returned here.
        """
        list_args: Dict[str, Any] = {"include_subgroups": True}
        # there are 3 states of the "archived" flag: true, false, undefined - we use the last 2
        if not include_archived:
            list_args["archived"] = False
        if self._is_admin():
            list_args["all_available"] = True
        else:
            # it's pointless to get projects with a lower role than Reporter
            # - it's the minimal role that is needed to manage something (f.e. labels)
            list_args["min_access_level"] = 20

        try:
            projects = self.groups.get(group, lazy=True).projects.list(get_all=True, **list_args)
        except GitlabListError as e:
            if e.response_code != 404:
                raise
            projects = []

        # compare case-insensitively, because the group may be spelled with a different
        # case in the config than its canonical path in GitLab; the returned paths
        # are the canonical ones from GitLab
        group_prefix = group.lower() + "/"
        projects_in_group_namespace = [
            project.asdict() for project in projects if project.path_with_namespace.lower().startswith(group_prefix)
        ]

        if only_names:
            return sorted(project["path_with_namespace"] for project in projects_in_group_namespace)
        return sorted(projects_in_group_namespace, key=lambda project: project["path_with_namespace"])

    @functools.lru_cache()
    def _is_admin(self) -> bool:
        current_user = self.http_get("/user")
        return isinstance(current_user, dict) and bool(current_user.get("is_admin", False))

    #  Uses "LIST" to get a user by username, to get the full User object, call get using the user's id
    @functools.lru_cache()
    def get_user_by_username_cached(self, username: str) -> User | None:
        # Gitlab API will only ever return 0 or 1 entry when GETting using `username` attribute
        # https://docs.gitlab.com/ee/api/users.html#for-non-administrator-users
        # so will always be list[RESTObject] and never RESTObjectList from python-gitlab's api
        # username list is case-insensitive on the gitlab api
        users: list[RESTObject] = self.users.list(username=username)  # type: ignore

        if len(users) == 0:
            return None

        user = users[0]
        return self.users.get(user.id)

    @functools.lru_cache()
    def _get_member_roles_from_group_cached(self, group_full_path: str) -> List[Dict[str, str]]:
        """Query GraphQL using Python Gitlab
        https://python-gitlab.readthedocs.io/en/stable/api-usage-graphql.html

        GET Member_Role via REST Api needs "Owner" on Gitlab.com or "Admin" on Dedicated
        List of custom roles can be retrieved via GraphQL endpoint with "Guest+"
        https://gitlab.com/gitlab-org/gitlab/-/issues/511919#note_2287581884

        https://docs.gitlab.com/ee/api/graphql/reference/index.html#groupmemberroles
        """

        if group_full_path is None:
            raise GitlabGetError(
                "Group Path must be provided when getting member roles",
                404,
            )

        query = (
            """
        {
          group(fullPath: \""""
            + group_full_path
            + """\") {
            memberRoles {
              nodes {
                id
                name
              }
            }
          }
        }
        """
        )
        info(f"Executing graphQl query to get Member Roles for Group '{group_full_path}'")
        result = self.graphql.execute(query)

        # Validate Group / MemberRoles exist
        if (
            result["group"] is not None
            and result["group"]["memberRoles"] is not None
            and result["group"]["memberRoles"]["nodes"] is not None
        ):
            member_role_nodes = result["group"]["memberRoles"]["nodes"]
        else:
            raise GitlabGetError(f"Failed to get Member Roles from Group: {query}")

        return self._convert_result_to_member_roles(member_role_nodes)

    @functools.lru_cache()
    def _get_member_roles_from_instance_cached(self) -> List[Dict[str, str]]:
        """Query GraphQL using Python Gitlab
        https://python-gitlab.readthedocs.io/en/stable/api-usage-graphql.html

        GET Member_Role via REST Api needs "Admin" on Dedicated/Self-Hosted

        On Self-Hosted/Dedicated it is only possible to create Member Roles at an instance level, so we query at that
        level and cache the result in order to save API calls when processing multiple Groups

        List of custom roles can be retrieved via GraphQL endpoint with "Guest+"
        https://gitlab.com/gitlab-org/gitlab/-/issues/511919#note_2287581884

        https://docs.gitlab.com/ee/api/graphql/reference/index.html#groupmemberroles
        """

        query = """
            {
              memberRoles {
                edges {
                  node {
                    id
                    name
                  }
                }
              }
            }
            """
        result = self.graphql.execute(query)

        if result["memberRoles"] is not None and result["memberRoles"]["edges"] is not None:
            member_role_edges = result["memberRoles"]["edges"]
        else:
            raise GitlabGetError(f"Failed to get Member Roles from instance: {query}")

        member_role_nodes = []

        for edge in member_role_edges:
            member_role_nodes.append(edge["node"])

        return self._convert_result_to_member_roles(member_role_nodes)

    @staticmethod
    def _convert_result_to_member_roles(member_role_nodes: List[Dict[str, str]]) -> List[Dict[str, str]]:
        # Unwrap Ids from GraphQl Gids
        member_role_id_prefix = "gid://gitlab/MemberRole/"

        member_roles = []
        for node in member_role_nodes:
            member_role_id = node["id"]
            member_role_id = member_role_id.replace(member_role_id_prefix, "")
            member_roles.append({"id": member_role_id, "name": node["name"]})

        return member_roles

    @staticmethod
    def _get_member_role_from_member_roles(
        name_or_id: Union[int, str], member_roles: List[Dict[str, str]]
    ) -> Dict[str, str]:
        for member_role in member_roles:
            member_role_id: str = member_role["id"]
            member_role_name: str = member_role["name"]
            if int(member_role_id) == name_or_id:
                return member_role
            elif member_role_name.lower() == str(name_or_id).lower():
                return member_role

        # Failed to find member role so throw an exception explaining such to user
        raise GitlabGetError(
            f"Member Role with name or id {name_or_id} could not be found",
            404,
        )

    def get_member_role_id_cached(self, name_or_id: Union[int, str], group_full_path: str) -> int:
        """
        GETs a member role id set in the config by the Name of the Member Role (by calling out to API) or by Id

        Get member_roles calls themselves are Cached, the logic in this method otherwise performs no API calls,
        so we should not cache the result of this specific method, otherwise we may fill the cache with duplicate data
        """
        if type(name_or_id) is int:
            # Already supplied as an id so no need to go get it from API
            return name_or_id

        if self._is_gitlab_saas():
            member_roles = self._get_member_roles_from_group_cached(group_full_path)
        else:
            member_roles = self._get_member_roles_from_instance_cached()

        member_role = self._get_member_role_from_member_roles(name_or_id, member_roles)

        return int(member_role["id"])

    def _is_gitlab_saas(self) -> bool:
        return self.url == gitlab.const.DEFAULT_URL
