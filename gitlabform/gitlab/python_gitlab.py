import functools
from typing import Union

from cli_ui import debug

import gitlab.const
from gitlab import Gitlab, GitlabGetError
from gitlab.base import RESTObject
from gitlab.v4.objects import Group, Project


# Extends the python-gitlab class to add convenience wrappers for common functionality used within gitlabform
class PythonGitlab(Gitlab):
    def get_user_id(self, username) -> int:
        user = self.get_user_by_username_cached(username)
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
    def get_user_by_username_cached(self, username: str) -> RESTObject:
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
    def get_member_roles_cached(self, group_id: Union[int, None]):
        """Python-Gitlab does not natively support Member Roles yet
        use https://python-gitlab.readthedocs.io/en/stable/api-levels.html#lower-level-api-http-methods
        to directly invoke member_roles GET endpoint(s) in GitLab
        https://docs.gitlab.com/ee/api/member_roles.html
        """
        if self.is_gitlab_saas():
            if group_id is None:
                raise GitlabGetError(
                    "Group Id must be provided when getting member roles on GitLab SaaS",
                    404,
                )
            # SAAS
            path = f"/groups/{group_id}/member_roles"
        else:
            # Self-Managed & Dedicated
            path = f"/member_roles"

        debug(f"Retrieving member roles from: {path}")
        return self.http_get(path)

    @functools.lru_cache()
    def get_member_role_cached(
        self, name_or_id: Union[int, str], group_id: Union[int, None]
    ):
        member_roles = self.get_member_roles_cached(group_id)
        for member_role in member_roles:
            if member_role["id"] == name_or_id:
                return member_role
            elif (
                type(name_or_id) == str
                and member_role["name"].lower() == name_or_id.lower()
            ):
                return member_role

        # Failed to find member role so throw an exception explaining such to user
        raise GitlabGetError(
            f"Member Role with name or id {name_or_id} could not be found",
            404,
        )

    @functools.lru_cache()
    def get_member_role_id_cached(
        self, name_or_id: Union[int, str], group_id: Union[int, None]
    ) -> int:
        if type(name_or_id) is int:
            # Already supplied as an id so no need to go get it from API
            return name_or_id
        member_role = self.get_member_role_cached(name_or_id, group_id)
        return member_role["id"]

    @functools.lru_cache()
    def is_gitlab_saas(self) -> bool:
        return self.url == gitlab.const.DEFAULT_URL
