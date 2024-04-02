import functools

from gitlab import Gitlab, GitlabGetError
from gitlab.base import RESTObject, RESTObjectList
from gitlab.v4.objects import Group


# Extends the python-gitlab class to add convenience wrappers for common functionality used within gitlabform
class PythonGitlab(Gitlab):
    def get_user_id(self, username) -> int:
        user = self.get_user_by_username(username)
        return user.id

    def get_group_id(self, groupname) -> int:
        groups = self.get_group_by_groupname(groupname)
        return groups.id

    def get_group_by_name(self, groupname: str) -> Group:
        group = self.get_group_by_groupname(groupname)
        return self.groups.get(group.id)

        #  Uses "LIST" to get a group by groupname, to get the full Group object, call get using the group's id

    @functools.lru_cache()
    def get_group_by_groupname(self, groupname: str) -> RESTObject:
        group: Group = self.groups.get(groupname)
        if group:
            return group

        raise GitlabGetError("No group found when getting '%s'" % groupname, 404)

    #  Uses "LIST" to get a user by username, to get the full User object, call get using the user's id
    @functools.lru_cache()
    def get_user_by_username(self, username: str) -> RESTObject:
        # Gitlab API will only ever return 0 or 1 entry when GETting using `username` attribute
        # https://docs.gitlab.com/ee/api/users.html#for-non-administrator-users
        # so will always be list[RESTObject] and never RESTObjectList from python-gitlab's api
        users: list[RESTObject] = self.users.list(username=username)  # type: ignore

        if len(users) == 0:
            raise GitlabGetError(
                "No users found when searching for username '%s'" % username, 404
            )

        return users[0]
