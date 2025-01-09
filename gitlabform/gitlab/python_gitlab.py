import functools
from typing import Union, Any, Optional, Dict, List

import gitlab.const
from gitlab import Gitlab, GitlabGetError, GraphQL
from gitlab.base import RESTObject
from gitlab.v4.objects import Group, Project

from cli_ui import debug as verbose


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

    @functools.lru_cache()
    def get_user_id_cached(self, username) -> int:
        user = self._get_user_by_username_cached(username)
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
        group: Group = self.groups.get(groupname)
        if group:
            return group

        raise GitlabGetError("No group found when getting '%s'" % groupname, 404)

    #  Uses "LIST" to get a user by username, to get the full User object, call get using the user's id
    @functools.lru_cache()
    def _get_user_by_username_cached(self, username: str) -> RESTObject:
        # Gitlab API will only ever return 0 or 1 entry when GETting using `username` attribute
        # https://docs.gitlab.com/ee/api/users.html#for-non-administrator-users
        # so will always be list[RESTObject] and never RESTObjectList from python-gitlab's api
        users: list[RESTObject] = self.users.list(username=username)  # type: ignore

        if len(users) == 0:
            raise GitlabGetError(
                "No users found when searching for username '%s'" % username, 404
            )

        return users[0]

    @functools.lru_cache()
    def _get_member_roles_from_group_cached(
        self, group_full_path: str
    ) -> List[Dict[str, str]]:
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
        verbose(
            f"Executing graphQl query to get Member Roles for Group '{group_full_path}'"
        )
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

        if (
            result["memberRoles"] is not None
            and result["memberRoles"]["edges"] is not None
        ):
            member_role_edges = result["memberRoles"]["edges"]
        else:
            raise GitlabGetError(f"Failed to get Member Roles from instance: {query}")

        member_role_nodes = []

        for edge in member_role_edges:
            member_role_nodes.append(edge["node"])

        return self._convert_result_to_member_roles(member_role_nodes)

    @staticmethod
    def _convert_result_to_member_roles(
        member_role_nodes: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
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

    def get_member_role_id_cached(
        self, name_or_id: Union[int, str], group_full_path: str
    ) -> int:
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
