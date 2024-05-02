import functools
from typing import Union

from gitlab import Gitlab, GitlabGetError
from gitlab.base import RESTObject, RESTObjectList
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
